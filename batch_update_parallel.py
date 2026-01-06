from app import app
from database import db, Scheme
from llm_summarizer import generate_structured_summary
import json
import time
import concurrent.futures
import threading

# Lock to ensure thread-safe database commits
db_lock = threading.Lock()
success_count = 0
processed_count = 0

def process_scheme(scheme_data):
    """
    Worker function to process a single scheme.
    scheme_data is a tuple/dict to avoid detaching SA objects across threads.
    """
    global success_count, processed_count
    
    sr_no, name, details, eligibility = scheme_data
    
    try:
        new_summary = generate_structured_summary(name, details, eligibility)
        if new_summary:
            return (sr_no, json.dumps(new_summary))
    except Exception as e:
        print(f"Error processing {sr_no}: {e}")
    
    return None

def update_summaries_parallel(limit=None, max_workers=2):
    global success_count, processed_count
    print(f"Starting PARALLEL database update for {'ALL' if limit is None else limit} schemes...")
    print(f"Using {max_workers} worker threads.")

    with app.app_context():
        # 1. Fetch data. We filter out schemes that appear to be already processed to save time.
        # "Old" summaries are plain text. "New" summaries are JSON starting with "{".
        query = db.session.query(Scheme.sr_no, Scheme.scheme_name, Scheme.details, Scheme.eligibility, Scheme.summary)
        
        if limit:
            query = query.limit(limit)
        
        all_schemes = query.all()
        # Filter for schemes that DO NOT have a conversational summary yet.
        # "New" summaries have "objective" containing "you" or "your" (case-insensitive).
        schemes_to_process = []
        skipped_count = 0
        
        for s in all_schemes:
            is_processed = False
            if s.summary and s.summary.strip().startswith('{'):
                try:
                    data = json.loads(s.summary)
                    obj = data.get('objective', '').lower()
                    if 'you' in obj or 'your' in obj:
                        is_processed = True
                except:
                    pass # Invalid JSON, treat as unprocessed
            
            if is_processed:
                skipped_count += 1
            else:
                schemes_to_process.append((s.sr_no, s.scheme_name, s.details, s.eligibility))
        
        total = len(schemes_to_process)
        
        print(f"Found {len(all_schemes)} total schemes.")
        print(f"Skipping {skipped_count} already processed (conversational) schemes.")
        print(f"Starting processing for remaining {total} schemes...")
        
        # 2. Process in Parallel
        updates_buffer = []
        batch_size = 10
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_audit = {executor.submit(process_scheme, s): s for s in schemes_to_process}
            
            for future in concurrent.futures.as_completed(future_to_audit):
                processed_count += 1
                result = future.result()
                
                if result:
                    sr_no, summary_json = result
                    updates_buffer.append((sr_no, summary_json))
                    print(f"[{processed_count}/{total}] Success: Scheme {sr_no}")
                else:
                    # Access scheme name from the data tuple we submitted
                    s_data = future_to_audit[future]
                    print(f"[{processed_count}/{total}] Failed: {s_data[1]}") # s_data[1] is scheme_name

                # 3. Write Batch to DB (Thread-safe)
                if len(updates_buffer) >= batch_size:
                    with db_lock:
                        print(f"Committing batch of {len(updates_buffer)}...")
                        try:
                            for u_sr_no, u_summary in updates_buffer:
                                # extensive updates: fetch object by ID and update
                                s = Scheme.query.get(u_sr_no)
                                if s:
                                    s.summary = u_summary
                            db.session.commit()
                            success_count += len(updates_buffer)
                            updates_buffer = [] # Clear buffer
                        except Exception as e:
                            print(f"Database Commit Error: {e}")
                            db.session.rollback()

        # 4. Final Commit for remaining items
        if updates_buffer:
            with db_lock:
                print(f"Committing final {len(updates_buffer)} items...")
                for u_sr_no, u_summary in updates_buffer:
                    s = Scheme.query.get(u_sr_no)
                    if s:
                        s.summary = u_summary
                db.session.commit()
                success_count += len(updates_buffer)

    print(f"DONE. Updated {success_count} new schemes. Total processed in this run: {total}.")

if __name__ == "__main__":
    # Adjust max_workers relative to your VRAM.
    # 2-3 is usually safe for RTX 4060 (8GB). Higher might cause OutOfMemory.
    update_summaries_parallel(limit=None, max_workers=2)
