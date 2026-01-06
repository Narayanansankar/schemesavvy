# search_engine.py
import os
import faiss
import numpy as np
import pandas as pd
import json
from sentence_transformers import SentenceTransformer
from serpapi import GoogleSearch
from database import db, Scheme
from nlp_utils import preprocess_text
from bda_logger import log_search_event

class SearchEngine:
    def __init__(self, app):
        print("Initializing Search Engine...")
        self.app = app
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.schemes_in_memory = []
        self._load_index()

    def _load_index(self):
        """Loads the Faiss index from disk or builds it if it doesn't exist."""
        with self.app.app_context():
            if os.path.exists("schemes.index"):
                print("Loading existing Faiss index...")
                self.index = faiss.read_index("schemes.index")
                schemes_df = pd.read_csv('schemes_mapping.csv')
                self.schemes_in_memory = [db.session.get(Scheme, sr_no) for sr_no in schemes_df['sr_no']]
                print(f"Index loaded. Index size: {self.index.ntotal}, Mapping size: {len(self.schemes_in_memory)}")
                log_search_event("SYSTEM_STARTUP", {"index_size": self.index.ntotal}, 0, False)
            else:
                print("No Faiss index found. Building a new one...")
                self.build_index()

    def build_index(self):
        """Builds and saves the Faiss index from scratch."""
        with self.app.app_context():
            schemes = Scheme.query.all()
            scheme_texts = [f"{s.scheme_name}. {s.details}. {s.benefits}" for s in schemes]
            print("Generating embeddings... This may take a moment.")
            vectors = self.sentence_model.encode(scheme_texts, show_progress_bar=True)
            vectors = np.array(vectors).astype('float32')

            dimension = vectors.shape[1]
            quantizer = faiss.IndexFlatL2(dimension)
            nlist = max(1, min(100, len(schemes) // 4))
            index = faiss.IndexIVFPQ(quantizer, dimension, nlist, 8, 8)

            print("Training Faiss index...")
            index.train(vectors)
            index.add(vectors)
            faiss.write_index(index, "schemes.index")
            
            scheme_data = [{"sr_no": s.sr_no} for s in schemes]
            pd.DataFrame(scheme_data).to_csv('schemes_mapping.csv', index=False)
            
            self.index = index
            self.schemes_in_memory = schemes
            print("Faiss index built and saved.")

    def _validate_summary(self, summary_json, sr_no):
        """Checks if a summary has the correct structure. Returns a valid dict or None."""
        if not summary_json:
            return None
        try:
            summary = json.loads(summary_json)
            # Check for required keys and correct types
            if (isinstance(summary, dict) and
                'objective' in summary and isinstance(summary['objective'], str) and
                'benefits' in summary and isinstance(summary['benefits'], list) and
                'eligibility' in summary and isinstance(summary['eligibility'], list)):
                return summary
            else:
                print(f"Warning: Malformed summary structure for sr_no {sr_no}. Will be regenerated on next batch run.")
                return None
        except (json.JSONDecodeError, TypeError):
            print(f"Warning: Invalid JSON in summary for sr_no {sr_no}. Will be regenerated on next batch run.")
            return None

    def search(self, query: str, context: dict) -> dict:
        """Performs the complete search pipeline with fixes for duplicates and filtering."""
        try:
            state_filter = context.get('state')
            category_filter = context.get('category')
    
            query_vector = self.sentence_model.encode([query])
            self.index.nprobe = 10
            
            distances, indices = self.index.search(np.array(query_vector).astype('float32'), 200) 
            
            query_keywords = set(preprocess_text(query).split())
            local_schemes = []
            
            seen_sr_nos = set()
    
            for i, idx in enumerate(indices[0]):
                if idx == -1 or idx >= len(self.schemes_in_memory):
                    continue
                
                scheme = self.schemes_in_memory[idx]
                if scheme is None or scheme.sr_no in seen_sr_nos:
                    continue
                
                # --- SMART CONTEXT FILTERING ---
                # 1. State Filter
                # If user asks for "Tamil Nadu", we show "Tamil Nadu" schemes AND "Central/All India" schemes.
                is_state_match = False
                if state_filter:
                    scheme_state = (scheme.state or "").lower()
                    filter_state = state_filter.lower()
                    
                    # Direct Match
                    if filter_state in scheme_state:
                        is_state_match = True
                    # Central/National Scheme Match (Allow these even if state is specified)
                    elif any(kw in scheme_state for kw in ["central", "all india", "national", "pan india", "india"]):
                        pass # Allowed, but not a specific state match
                    # Otherwise, skip
                    elif scheme_state.strip() != "": 
                        continue 

                # 2. Category Filter
                is_category_match = False
                if category_filter:
                    scheme_cat = (scheme.category or "").lower()
                    if category_filter.lower() in scheme_cat:
                        is_category_match = True
                    # We don't strictly exclude by category as categories are often messy/missing
                    # Instead, we rely on semantic search + boosts
    
                seen_sr_nos.add(scheme.sr_no)
                scheme_text = preprocess_text(f"{scheme.scheme_name} {scheme.details}")
                
                # --- SCORING ---
                # Base Scores
                keyword_score = len(query_keywords.intersection(scheme_text.split()))
                semantic_score = 1 / (1 + distances[0][i])
                
                # Context Boosts (Give bonus for matching state/category explicitly)
                boost = 0.0
                if is_state_match: boost += 0.2
                if is_category_match: boost += 0.1
                
                # Weighted Final Score
                relevance_score = float((0.6 * semantic_score) + (0.2 * keyword_score) + boost)
    
                # Validate summary safely
                try:
                    structured_summary = self._validate_summary(scheme.summary, scheme.sr_no)
                except Exception:
                    structured_summary = None

                local_schemes.append({
                    "id": scheme.sr_no,
                    "source": "Our Database", "scheme_name": scheme.scheme_name,
                    "state": scheme.state, "scheme_link": scheme.scheme_link,
                    "relevance_score": relevance_score, "summary": structured_summary,
                    "full_details": {
                        "details": scheme.details.lstrip("Details").strip() if scheme.details else "",
                        "eligibility": scheme.eligibility.lstrip("Eligibility").strip() if scheme.eligibility else ""
                    }
                })
            
            local_schemes.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            web_schemes = []
            web_fallback_triggered = len(local_schemes) < 3
            log_search_event(query, context, len(local_schemes), web_fallback_triggered)
            
            if web_fallback_triggered:
                print("Few local results found. Falling back to web search...")
                search_query = f"{query} {state_filter or ''} {category_filter or ''} scheme site:gov.in OR site:nic.in"
                try:
                    params = {"api_key": os.getenv("SERPAPI_KEY"), "engine": "google", "q": search_query, "gl": "in"}
                    search_results = GoogleSearch(params).get_dict()
                    for result in search_results.get("organic_results", [])[:3]:
                        web_schemes.append({
                            "source": "From the Web", "scheme_name": result.get("title"),
                            "details": result.get("snippet"), "scheme_link": result.get("link"),
                            "state": state_filter or "Varies", "eligibility": "Visit link for details",
                            "summary": None, "full_details": None
                        })
                except Exception as e:
                    print(f"Error during web search: {e}")
            return {
                "schemes": (local_schemes + web_schemes)[:10],
                "keywords": list(query_keywords)
            }
        except Exception as e:
            import traceback
            print("CRITICAL SEARCH ENGINE ERROR:")
            traceback.print_exc()
            return {"schemes": [], "keywords": [], "error": str(e)}
    