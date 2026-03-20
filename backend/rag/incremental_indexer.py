import json
import os
from backend.rag.ingestion import ingest_documents
from backend.rag.embeddings import get_embedding_model
from backend.rag.vector_store import VectorStore
import faiss
import pickle

STATE_FILE = "backend/rag/index_state.json"


def load_last_index_time():
    """
    Load the timestamp of the last successful indexing run.

    This function reads the stored timestamp from a JSON state file
    (`index_state.json`) which is used to determine which documents
    have been updated since the last indexing process.

    Returns:
        str or None:
            - ISO timestamp string of last indexed document (e.g., "2026-03-18T10:00:00")
            - None if no previous indexing state exists

    Notes:
        - If the state file does not exist, this indicates a first-time indexing run.
        - Used for incremental update filtering.
    """
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE) as f:
        return json.load(f).get("last_indexed_time")


def save_last_index_time(timestamp):
    """
    Persist the latest indexing timestamp to disk.

    This function updates the `index_state.json` file with the most recent
    document update timestamp after a successful indexing operation.

    Args:
        timestamp (str): ISO formatted timestamp representing the latest
                         document update time processed during indexing.

    Returns:
        None

    Notes:
        - Ensures reproducibility and supports incremental indexing.
        - This value is used in future runs to detect newly added or updated documents.
    """
    with open(STATE_FILE, "w") as f:
        json.dump({"last_indexed_time": timestamp}, f)


def incremental_update():
    """
    Perform incremental indexing of Notion documents into the FAISS vector store.

    This function:
    1. Loads the last indexed timestamp from state.
    2. Fetches all documents from Notion via ingestion pipeline.
    3. Filters only newly added or updated documents based on `last_updated` field.
    4. Generates embeddings only for new/updated chunks.
    5. Loads existing FAISS index and metadata.
    6. Appends new vectors and metadata without rebuilding entire index.
    7. Saves updated index and metadata back to disk.
    8. Updates the indexing state with the latest timestamp.

    Returns:
        None

    Behavior:
        - If no new documents are detected, the function exits early.
        - If no previous index exists, a new index is created.

    Advantages:
        - Avoids full index rebuilds (efficient)
        - Reduces embedding cost
        - Enables near real-time updates

    Notes:
        - Requires `last_updated` field in each chunk (from Notion's last_edited_time)
        - Assumes FAISS index and metadata are stored locally
    """
    print("🔄 Running incremental indexing...")

    last_time = load_last_index_time()

    chunks = ingest_documents()

    # ✅ Filter only new/updated chunks
    if last_time:
        new_chunks = []

        for c in chunks:
            chunk_time = c.get("last_updated")

            if not chunk_time:
                continue  # skip bad data

            if not last_time or chunk_time > last_time:
                new_chunks.append(c)
    else:
        new_chunks = chunks

    if not new_chunks:
        print("✅ No new documents found")
        return

    model = get_embedding_model()

    texts = [c["text"] for c in new_chunks]
    embeddings = model.embed_documents(texts)

    store = VectorStore()

    # 🔥 Load existing index
    try:
        store.index = faiss.read_index("backend/rag/index/index.faiss")

        with open("backend/rag/index/meta.pkl", "rb") as f:
            store.metadata = pickle.load(f)

    except:
        print("⚠️ No existing index found, creating new one")

    store.add(embeddings, new_chunks)

    store.save("backend/rag/index")

    # ✅ Save latest timestamp
    valid_times = [c["last_updated"] for c in new_chunks if c.get("last_updated")]

    if valid_times:
        latest_time = max(valid_times)
        save_last_index_time(latest_time)

    print(f"✅ Added {len(new_chunks)} new chunks")