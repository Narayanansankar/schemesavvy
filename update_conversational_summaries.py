from app import app
from database import db, Scheme
from llm_summarizer import generate_structured_summary
import json
import time

def update_summaries(limit=None):
    print(f"Starting database update for {'ALL' if limit is None else limit} schemes...")
    with app.app_context():
        # Get all schemes
        query = Scheme.query
        if limit:
            query = query.limit(limit)
            
        schemes = query.all()
        total = len(schemes)
        print(f"Found {total} schemes to process.")
        
        success_count = 0
        batch_size = 10  # Commit every 10 updates
        
        for i, scheme in enumerate(schemes):
            print(f"[{i+1}/{total}] Processing Scheme ID {scheme.sr_no}: {scheme.scheme_name}")
            
            try:
                # Generate Summary
                new_summary = generate_structured_summary(
                    scheme.scheme_name, 
                    scheme.details, 
                    scheme.eligibility
                )
                
                if new_summary:
                    scheme.summary = json.dumps(new_summary)
                    success_count += 1
                    print("  -> Updated successfully.")
                else:
                    print("  -> Failed to generate summary.")
                
                # Commit periodically to save progress
                if success_count % batch_size == 0:
                    db.session.commit()
                    print(f"  -> Committed batch of {batch_size}.")
                
            except Exception as e:
                print(f"  -> Error: {e}")
                
        # Final commit
        db.session.commit()
        print(f"Done. Processed {total} schemes. Successfully updated {success_count}.")

if __name__ == "__main__":
    # limit=None means ALL schemes. 
    # Providing a small number for testing, but set to None for full run.
    update_summaries(limit=None)
