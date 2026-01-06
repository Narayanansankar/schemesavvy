# app.py
import os
import pandas as pd
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
from sqlalchemy import inspect
from database import db, Scheme, init_db
from nlp_utils import extract_entities
from search_engine import SearchEngine

# Load environment variables from the .env file at the very top
load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

# Initialize the database with the app context
init_db(app)

# Initialize the Search Engine after the database is set up
search_engine = SearchEngine(app)

@app.route("/")
def home():
    """Renders the main search page."""
    return render_template("index.html")

@app.route("/query", methods=["POST"])
def query_schemes():
    """Handles user search queries."""
    user_input = request.json.get("query", "").strip()
    if not user_input:
        return jsonify({"status": "error", "message": "No query provided."}), 400

    # Manage conversational context in the user's session
    if 'context' not in session:
        session['context'] = {'state': None, 'category': None}

    new_state, new_category = extract_entities(user_input)
    if new_state:
        session['context']['state'] = new_state
    if new_category:
        session['context']['category'] = new_category
    
    # Delegate search logic to the SearchEngine. It returns a dictionary.
    search_result = search_engine.search(user_input, session['context'])
    
    # --- RAG: Generate AI Answer ---
    from llm_summarizer import generate_rag_answer
    top_schemes = search_result.get("schemes", [])
    language = request.json.get("language", "English")
    
    # Only generate if we have results
    ai_answer = None
    if top_schemes:
        # Run safely in a thread or simple blocking call (keeping it simple as per assessment "vibe coding")
        # For production, this should be async, but for <5s latency it's acceptable for a demo.
        ai_answer = generate_rag_answer(user_input, top_schemes, language)

    # Unpack the dictionary from search_result and build the final JSON response.
    return jsonify({
        "status": "success",
        "schemes": top_schemes,
        "keywords": search_result.get("keywords", []),
        "context": session['context'],
        "ai_answer": ai_answer
    }), 200

@app.route('/scheme/<int:scheme_id>')
def scheme_detail(scheme_id):
    """Renders the detailed view for a specific scheme."""
    try:
        # Use SQLAlchemy to find the scheme by primary key (sr_no)
        scheme = db.session.get(Scheme, scheme_id)
        
        if not scheme:
            return "Scheme not found", 404
            
        return render_template('detail.html', scheme=scheme)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/chat_scheme', methods=['POST'])
def chat_scheme():
    """Chat with the AI about a specific scheme."""
    data = request.json
    scheme_text = data.get('scheme_text', '')
    user_query = data.get('query', '')
    
    if not scheme_text or not user_query:
        return jsonify({"error": "Missing data"}), 400

    from llm_summarizer import chat_with_scheme_context
    response = chat_with_scheme_context(user_query, scheme_text)
    
    return jsonify({"response": response})

def initialize_database():
    """Checks if the database table exists. 
    deprecated: populating from CSV is now handled by manual Postgres restore.
    """
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.has_table('schemes'):
            print("Table 'schemes' not found. Creating table schema...")
            db.create_all()
            print("Note: Data should be loaded via pg_restore. CSV import is disabled.")
        else:
            print("Database table 'schemes' exists.")

if __name__ == "__main__":
    initialize_database()
    app.run(debug=True, use_reloader=False)