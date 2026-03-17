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
        """
        Perform vector-based semantic search on indexed document chunks.

        This function:
        1. Converts the user query into an embedding vector.
        2. Searches the FAISS index to find top-k similar chunks.
        3. Applies optional metadata filters (doc_type, industry).
        4. Attaches similarity score (distance) to each result.

        Args:
            query (str): User query or search text.
            k (int, optional): Number of top results to return. Default is 5.
            filters (dict, optional): Metadata filters such as:
                {
                    "doc_type": str or None,
                    "industry": str or None
                }

        Returns:
            list[dict]: List of retrieved chunks with metadata and score:
                [
                    {
                        "doc_title": str,
                        "section": str,
                        "text": str,
                        "doc_type": str,
                        "industry": str,
                        "page_id": str,
                        "score": float   # FAISS distance (lower is better)
                    }
                ]
        """

        query_embedding = self.embedding_model.embed_query(query)

        query_vector = np.array([query_embedding]).astype("float32")

        distances, indices = self.index.search(query_vector, k)

        results = []

        for i, idx in enumerate(indices[0]):

            chunk = self.metadata[idx]

            score = float(distances[0][i])

            # Apply metadata filters
            if filters:

                if filters.get("doc_type") and chunk["doc_type"] != filters["doc_type"]:
                    continue

                if filters.get("industry") and chunk["industry"] != filters["industry"]:
                    continue
            
            #attach score to chunk
            chunk_with_score = {
                **chunk,
                "score": score
            }

            results.append(chunk_with_score)

            if len(results) >= k:
                break

        return results