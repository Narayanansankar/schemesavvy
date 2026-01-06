# llm_summarizer.py
import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

import ollama

# --- Configuration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "BEDROCK").upper()
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# --- AWS Bedrock Client Setup ---
bedrock_client = None
if LLM_PROVIDER == "BEDROCK":
    try:
        bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv("AWS_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
    except Exception as e:
        print(f"Failed to initialize AWS Bedrock Client: {e}")

def generate_structured_summary(scheme_name: str, details_text: str, eligibility_text: str) -> dict | None:
    """
    Generates a structured scheme summary using the configured LLM provider (Bedrock or Ollama).
    """
    details_text = details_text.lstrip("Details").strip() if details_text else ""
    eligibility_text = eligibility_text.lstrip("Eligibility").strip() if eligibility_text else ""

    # 1. The Prompt (Universal)
    prompt = f"""
    You are a helpful AI Assistant named 'Scheme Savvy'. 
    Your goal is to explain government schemes to a citizen in simple, friendly English.
    
    Task: Analyze the following scheme and explain it to the user.
    
    Scheme Name: "{scheme_name}"
    Details: "{details_text}"
    Eligibility: "{eligibility_text}"

    Output Format: Provide ONLY a valid JSON object with these keys:
    1. "objective": A friendly sentence explaining how this scheme helps the user. (Use words like "You", "Your", "This helps you").
    2. "benefits": An array of strings listing the key benefits.
    3. "eligibility": An array of strings listing who can apply.

    Do not include any text outside the JSON object. Do not wrap in markdown code blocks.
    """

    print(f"Calling {LLM_PROVIDER} ({BEDROCK_MODEL_ID if LLM_PROVIDER == 'BEDROCK' else OLLAMA_MODEL}) for scheme: {scheme_name}")

    try:
        if LLM_PROVIDER == "BEDROCK":
            if not bedrock_client:
                print("Bedrock client not initialized.")
                return None
                
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = bedrock_client.invoke_model(
                body=body,
                modelId=BEDROCK_MODEL_ID,
                accept='application/json',
                contentType='application/json'
            )
            response_body = json.loads(response.get('body').read())
            response_text = response_body.get('content')[0].get('text')
            
        elif LLM_PROVIDER == "OLLAMA":
            response = ollama.chat(model=OLLAMA_MODEL, messages=[
                {'role': 'user', 'content': prompt},
            ], format='json') # Enforce JSON mode if supported or just parse text
            
            response_text = response['message']['content']
        else:
            print(f"Unknown LLM Provider: {LLM_PROVIDER}")
            return None

        # Post-Processing: Clean up potential Markdown wrappers
        cleaned_json_str = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_json_str)

    except Exception as e:
        print(f"LLM Generation Error ({LLM_PROVIDER}): {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_rag_answer(user_query: str, schemes: list, language: str = "English") -> str:
    """
    Synthesizes a conversational answer based on the user's query and the top retrieved schemes.
    Values RAG (Retrieval Augmented Generation).
    """
    if not schemes:
        return "I couldn't find any specific schemes matching your request in our database."

    # Prepare context from top 3 schemes
    context_text = ""
    for i, s in enumerate(schemes[:3]):
        context_text += f"{i+1}. {s['scheme_name']}: {s.get('summary', {}).get('objective', 'No summary available.')}\n"

    # Language instruction
    lang_instruction = ""
    if language.lower() == "hindi":
        lang_instruction = "Answer in clear, natural Hindi (Devanagari script)."
    elif language.lower() == "tamil":
        lang_instruction = "Answer in clear, natural Tamil."
    else:
        lang_instruction = "Answer in simple, friendly English."

    prompt = f"""
    You are 'Scheme Savvy', a helpful AI assistant for Indian Government Schemes.
    
    User Query: "{user_query}"
    
    Based ONLY on the following schemes found in our database, write a short, friendly paragraph (2-3 sentences) answering the user.
    Don't list them again as bullet points. Just synthesize the best options.
    
    Schemes Found:
    {context_text}
    
    Task: {lang_instruction}
    """
    
    print(f"Generating RAG Answer in {language} with {LLM_PROVIDER}...")
    
    try:
        if LLM_PROVIDER == "BEDROCK":
             if not bedrock_client: return "AI Service Unavailable."
             body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
             })
             response = bedrock_client.invoke_model(body=body, modelId=BEDROCK_MODEL_ID)
             response_body = json.loads(response.get('body').read())
             return response_body.get('content')[0].get('text').strip()
             
        elif LLM_PROVIDER == "OLLAMA":
             response = ollama.chat(model=OLLAMA_MODEL, messages=[{'role': 'user', 'content': prompt}])
             return response['message']['content'].strip()
             
    except Exception as e:
        print(f"RAG Generation Error: {e}")
        return "I found some relevant schemes for you below, but couldn't generate a summary at the moment."

def chat_with_scheme_context(user_query: str, scheme_text: str) -> str:
    """
    Answers a user's question specific to a single scheme's text.
    """
    prompt = f"""
    You are an expert assistant for this specific government scheme.
    
    SCHEME DETAILS:
    {scheme_text[:5000]} 
    (Context truncated for brevity if too long)
    
    USER QUESTION: "{user_query}"
    
    TASK: Answer the user's question accurately based ONLY on the scheme details provided above.
    If the answer is not in the text, imply say "I don't see that information in the official scheme details."
    Keep it concise and helpful.
    """
    
    try:
        if LLM_PROVIDER == "BEDROCK":
             if not bedrock_client: return "AI Service Unavailable."
             body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
             })
             response_body = json.loads(bedrock_client.invoke_model(body=body, modelId=BEDROCK_MODEL_ID).get('body').read())
             return response_body.get('content')[0].get('text').strip()
             
        elif LLM_PROVIDER == "OLLAMA":
             response = ollama.chat(model=OLLAMA_MODEL, messages=[{'role': 'user', 'content': prompt}])
             return response['message']['content'].strip()
             
    except Exception as e:
        return f"Sorry, I couldn't process that: {e}"
