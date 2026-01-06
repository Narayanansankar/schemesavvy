# process_logs.py
import re
import pandas as pd
import sqlite3
from ast import literal_eval

def parse_log_line(line):
    """Uses regex to extract structured data from a single log line."""
    pattern = re.compile(
        r"^(?P<timestamp>.*?)\s-\s"
        r"QUERY:\s\"(?P<query>.*?)\"\s\|\s"
        r"CONTEXT:\s(?P<context>.*?)\s\|\s"
        r"LOCAL_RESULTS:\s(?P<local_results>\d+)\s\|\s"
        r"WEB_FALLBACK:\s(?P<web_fallback>True|False)$"
    )
    match = pattern.match(line)
    if not match:
        return None
    
    data = match.groupdict()
    
    # Safely evaluate the context string into a Python dictionary
    try:
        context_dict = literal_eval(data['context'])
        data['state_context'] = context_dict.get('state')
        data['category_context'] = context_dict.get('category')
    except (ValueError, SyntaxError):
        data['state_context'] = None
        data['category_context'] = None
        
    # Clean up and type cast
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data['local_results'] = int(data['local_results'])
    data['web_fallback'] = data['web_fallback'] == 'True'
    del data['context'] # Remove the raw context string
    
    return data

def process_logs():
    """Main ETL function to read, process, and save log data."""
    try:
        with open('search_analytics.log', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("search_analytics.log not found. Please run the web app to generate logs.")
        return

    print(f"Found {len(lines)} log entries to process.")
    
    parsed_data = [parse_log_line(line) for line in lines]
    valid_data = [d for d in parsed_data if d is not None]
    
    if not valid_data:
        print("No valid log entries found to process.")
        return

    df = pd.DataFrame(valid_data)
    
    # Save to a clean CSV file
    clean_csv_path = 'analytics_data.csv'
    df.to_csv(clean_csv_path, index=False)
    print(f"Clean data saved to {clean_csv_path}")
    
    # Save to a SQLite database for the dashboard
    db_path = 'analytics.db'
    conn = sqlite3.connect(db_path)
    df.to_sql('searches', conn, if_exists='replace', index=False)
    conn.close()
    print(f"Data loaded into SQLite database: {db_path}")

if __name__ == "__main__":
    process_logs()