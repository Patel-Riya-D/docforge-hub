import faiss
import pickle
import numpy as np
from backend.rag.embeddings import get_embedding_model


class Retriever:

    def __init__(self):

        self.index = faiss.read_index("backend/rag/index/index.faiss")

        with open("backend/rag/index/meta.pkl", "rb") as f:
            self.metadata = pickle.load(f)

        self.embedding_model = get_embedding_model()

    def search(self, query, k=5, filters=None):

        query_embedding = self.embedding_model.embed_query(query)

        query_vector = np.array([query_embedding]).astype("float32")

        distances, indices = self.index.search(query_vector, k)

        results = []

        for idx in indices[0]:

            chunk = self.metadata[idx]

            # Apply metadata filters
            if filters:

                if filters.get("doc_type") and chunk["doc_type"] != filters["doc_type"]:
                    continue

                if filters.get("industry") and chunk["industry"] != filters["industry"]:
                    continue

            results.append(chunk)

            if len(results) >= k:
                break

        return results