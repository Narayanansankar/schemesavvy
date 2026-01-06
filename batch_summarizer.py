# batch_summarizer.py
import os
import json
import time
import pandas as pd
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
DATABASE_URI = os.getenv("DATABASE_URI")
OLLAMA_API_URL = "http://localhost:11434/api/generate" # Default Ollama API endpoint
MODEL_NAME = "mistral" # The model we downloaded
BATCH_SIZE = 10 # How many schemes to fetch from DB at once
DELAY_BETWEEN_REQUESTS = 2 # Seconds to wait to be gentle on your machine

# --- Database Connection ---
try:
    engine = create_engine(DATABASE_URI)
    print("Successfully connected to the database.")
except Exception as e:
    print(f"Failed to connect to the database: {e}")
    exit()

def get_schemes_without_summary(limit=BATCH_SIZE):
    """Fetches a batch of schemes from the DB that have a NULL summary."""
    with engine.connect() as connection:
        query = text("SELECT sr_no, scheme_name, details, eligibility FROM schemes WHERE summary IS NULL LIMIT :limit")
        result = connection.execute(query, {"limit": limit})
        schemes = result.fetchall()
        return schemes

def update_scheme_summary(sr_no, summary_json):
    """Updates a scheme in the DB with its new structured summary."""
    with engine.connect() as connection:
        # Use a transaction to ensure data integrity
        with connection.begin() as transaction:
            try:
                query = text("UPDATE schemes SET summary = :summary WHERE sr_no = :sr_no")
                connection.execute(query, {"summary": json.dumps(summary_json), "sr_no": sr_no})
                transaction.commit()
                print(f"Successfully updated sr_no: {sr_no}")
            except Exception as e:
                print(f"Failed to update sr_no: {sr_no}. Error: {e}")
                transaction.rollback()

def generate_summary_with_ollama(scheme_name, details, eligibility):
    """Calls the local Ollama API to generate a structured summary."""
    prompt = f"""
    [INST] You are an expert policy analyst. Your task is to extract and summarize key information about a government scheme into a structured JSON object. You must only respond with the JSON object and nothing else.

    Analyze the following information for the scheme named "{scheme_name}":
    
    Details: "{details}"
    Eligibility: "{eligibility}"

    Provide a JSON object with these exact keys: "objective", "benefits", "eligibility".
    - "objective": A concise sentence on the main goal.
    - "benefits": An array of 3-5 strings listing key benefits.
    - "eligibility": An array of 3-5 strings listing key eligibility criteria.
    [/INST]
    """
    
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "format": "json", # This forces JSON output
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120) # 120-second timeout
        response.raise_for_status() # Raise an exception for bad status codes
        
        response_json = response.json()
        summary_content = json.loads(response_json['response'])
        return summary_content

    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

# --- Main Processing Loop ---
if __name__ == "__main__":
    print("Starting batch summarization process...")
    processed_count = 0
    while True:
        schemes_to_process = get_schemes_without_summary()
        if not schemes_to_process:
            print("All schemes have been summarized. Exiting.")
            break
        
        print(f"Found {len(schemes_to_process)} schemes to process in this batch.")
        
        for scheme in schemes_to_process:
            sr_no, name, dets, elig = scheme
            print(f"\n--- Processing Scheme SR_NO: {sr_no}, Name: {name[:50]}... ---")
            
            summary = generate_summary_with_ollama(name, dets, elig)
            
            if summary:
                update_scheme_summary(sr_no, summary)
                processed_count += 1
            else:
                print(f"Skipping update for sr_no: {sr_no} due to generation failure.")

            print(f"Waiting for {DELAY_BETWEEN_REQUESTS} seconds...")
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
    print(f"\nBatch processing complete. Total schemes processed in this run: {processed_count}")