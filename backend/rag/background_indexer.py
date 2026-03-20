"""
Background Indexer Module

This module runs a continuous background process to keep the FAISS vector
index synchronized with Notion documents.

It uses incremental indexing to:
- Detect new or updated documents
- Avoid full index rebuilds
- Improve performance and efficiency

Key Features:
- Runs in a daemon thread
- Uses thread lock to prevent concurrent index writes
- Logs indexing activity for debugging and monitoring
- Executes at a fixed interval (configurable)

Usage:
    - Imported and started in FastAPI `main.py` during startup
"""

import time
from threading import Lock
from backend.rag.incremental_indexer import incremental_update
from backend.utils.logger import get_logger

# Initialize logger
logger = get_logger("INDEXER")

# Global lock to ensure safe FAISS updates
index_lock = Lock()

# Interval (in seconds) between indexing runs
INDEX_INTERVAL = 600  # 10 minutes


def start_auto_indexing():
    """
    Start the background indexing loop.

    This function runs indefinitely and periodically triggers incremental
    indexing to update the FAISS vector store with new or modified documents.

    Workflow:
        1. Acquire thread lock to prevent concurrent index updates
        2. Run incremental_update() to process new/updated documents
        3. Release lock
        4. Sleep for defined interval
        5. Repeat

    Returns:
        None

    Notes:
        - Designed to run as a daemon thread
        - Safe for concurrent API usage
        - Ensures near real-time synchronization with Notion
    """

    logger.info("🚀 Background indexer started")

    while True:
        try:
            logger.info("🔄 Checking for document updates...")

            with index_lock:
                incremental_update()

            logger.info(f"⏳ Sleeping for {INDEX_INTERVAL} seconds")

        except Exception as e:
            logger.error(f"❌ Indexing error: {str(e)}")

        time.sleep(INDEX_INTERVAL)