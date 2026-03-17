from backend.rag.ingestion import ingest_documents
from backend.rag.embeddings import get_embedding_model
from backend.rag.vector_store import VectorStore


def build_index():

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