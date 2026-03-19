"""
Vector Index Builder for RAG System

This script builds the FAISS vector index from ingested Notion documents.

Workflow:
1. Fetch documents using ingestion pipeline
2. Split documents into chunks with metadata
3. Generate embeddings using embedding model
4. Store embeddings and metadata in vector store
5. Persist index to disk for retrieval

Key Features:
- Batch embedding generation for efficiency
- Supports large datasets via chunked processing
- Stores both embeddings and metadata for retrieval

Output:
- FAISS index file
- Metadata file (used during retrieval)

Usage:
    python build_index.py

Used by:
- Retriever module for semantic search
"""
from backend.rag.ingestion import ingest_documents
from backend.rag.embeddings import get_embedding_model
from backend.rag.vector_store import VectorStore


def build_index():
    """
    Build and persist FAISS vector index from document chunks.

    Steps:
    1. Load and preprocess documents via ingestion pipeline
    2. Extract text content from chunks
    3. Generate embeddings in batches to avoid memory issues
    4. Store embeddings along with metadata in vector store
    5. Save index to disk for later retrieval

    Returns:
        None

    Notes:
    - Batch processing improves performance and prevents API overload
    - Embeddings are generated using configured embedding model
    - Output is saved to 'backend/rag/index'
    """

    chunks = ingest_documents()

    model = get_embedding_model()

    texts = [c["text"] for c in chunks]

    embeddings = []
    batch_size = 50

    for i in range(0, len(texts), batch_size):
        
        batch = texts[i:i+batch_size]
        print(f"Embedding batch {i} → {i+len(batch)}")

        emb = model.embed_documents(batch)
        embeddings.extend(emb)

    store = VectorStore()

    store.add(embeddings, chunks)

    store.save("backend/rag/index")

    print("Vector index built with", len(chunks), "chunks")


if __name__ == "__main__":
    build_index()