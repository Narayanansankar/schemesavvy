# SchemeSavvy - Intelligent Government Schemes Assistant

SchemeSavvy is an AI-powered conversational platform designed to bridge the gap between Indian citizens and government welfare schemes. It uses advanced NLP, Hybrid RAG (Retrieval-Augmented Generation), and multilingual voice interaction to provide accurate, personalized, and accessible information.

## 🚀 Key Features
- **Context-Aware Search**: Semantic search using `sentence-transformers` and `FAISS` to find relevant schemes even with vague queries.
- **Hybrid RAG Chatbot**: Combines database retrieval with LLMs (AWS Bedrock / Ollama) to generate human-like answers.
- **Voice & Multilingual**: Supports Voice Input and answers in **English, Hindi, and Tamil**.
- **Split-View Details**: A dedicated "Chat with Scheme" page where users can ask questions specific to a single scheme's document.
- **Premium UI**: "Perplexity-style" modern interface with glassmorphism, sticky search, and masonry grid.
- **Real-time Context**: Filters results intelligently based on State and Category (e.g., boosting "Center" schemes when searching for a State).

## 📊 Data Sources & Integration
The core intelligence of SchemeSavvy is built upon real-world, high-veracity data:

- **Primary Source**: **[myschemes.gov.in](https://www.myschemes.gov.in/)** (National Portal for Government Schemes).
- **Data Acquisition**: A custom scraping pipeline was developed to aggregate over **6,000+ schemes** across Central and State levels.
- **Structured Attributes**: The dataset includes rich metadata for every scheme:
  - *Scheme Details & Benefits*
  - *Eligibility Criteria*
  - *Application Process*
  - *Required Documents*
- **Data Flow**: Scraped data -> Cleaned & Structured (CSV) -> Ingested into **PostgreSQL** -> Embeddings generated for **FAISS**.

## 🛠️ Technology Stack
- **Backend**: Python (Flask), SQLAlchemy, PostgreSQL
- **AI/ML**: 
  - **Models**: `all-MiniLM-L6-v2` (Embeddings), `Claude 3 Haiku` (via AWS Bedrock) / `Llama 3` (Local).
  - **Vector DB**: FAISS (Facebook AI Similarity Search).
  - **NLP**: NLTK for entity extraction, TF-IDF scoring.
- **Frontend**: HTML5, Modern CSS (Glassmorphism), Vanilla JS, Web Speech API.
- **External APIs**: SerpAPI (Google Search for latest updates).

## ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/schemesavvy.git
    cd schemesavvy
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```ini
    DATABASE_URI=postgresql://user:password@localhost/schemesavvy
    FLASK_SECRET_KEY=your_secret_key
    SERPAPI_KEY=your_serpapi_key
    
    # AI Configuration
    LLM_PROVIDER=BEDROCK  # or OLLAMA
    BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
    AWS_REGION=us-east-1
    AWS_ACCESS_KEY_ID=your_aws_key
    AWS_SECRET_ACCESS_KEY=your_aws_secret
    ```

4.  **Run the Application**
    ```bash
    python app.py
    ```
    Access the app at `http://127.0.0.1:5000`.

## 📁 Project Structure
- `app.py`: Main Flask application and API routes.
- `search_engine.py`: Core logic for semantic search, ranking, and context boosting.
- `llm_summarizer.py`: Integration with LLMs (Bedrock/Ollama) for RAG and Chat.
- `nlp_utils.py`: Text preprocessing and Entity Extraction (State/Category detection).
- `static/modern.css`: The premium design system.
- `templates/`: HTML templates for Search (`index.html`) and Details (`detail.html`).

## 🏆 Assessment Highlights
- **Real-World Data**: Successfully integrated external data scraped from `myschemes.gov.in` and stored in PostgreSQL (Bonus Requirement).
- **RAG Architecture**: Implements a complete Retrieval-Augmented Generation flow using Vector Search (Retrieval) and AWS Bedrock (Generation).
- **Chatbot Interface**: A fully functional contextual assistant that simplifies complex policy language.
- **Accessibility**: Solves the language barrier with Hindi/Tamil support.
