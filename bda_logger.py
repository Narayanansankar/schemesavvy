# bda_logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    """Sets up a rotating file logger for search analytics."""
    logger = logging.getLogger('bda_analytics')
    logger.setLevel(logging.INFO)
    try:
        handler = RotatingFileHandler('search_analytics.log', maxBytes=10000, backupCount=5)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except PermissionError:
        # If file is locked (common on Windows with multiple processes), use a console handler or null handler
        print("Warning: Could not access log file (locked). Logging to console only.")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

bda_log = setup_logger()

def log_search_event(query, context, local_results_count, web_fallback_triggered):
    """Logs a search event to the analytics file."""
    log_message = (
        f"QUERY: \"{query}\" | "
        f"CONTEXT: {context} | "
        f"LOCAL_RESULTS: {local_results_count} | "
        f"WEB_FALLBACK: {web_fallback_triggered}"
    )
    bda_log.info(log_message)