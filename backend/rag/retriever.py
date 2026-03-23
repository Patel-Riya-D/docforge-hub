"""
Semantic Retriever using FAISS

This module handles vector-based retrieval of document chunks.

Responsibilities:
- Load FAISS index and metadata
- Convert user query into embedding vector
- Perform nearest neighbor search
- Apply metadata filters (doc_type, industry)
- Return top-k relevant chunks with similarity scores

Key Features:
- Fast vector search using FAISS
- Metadata-based filtering for targeted retrieval
- Score-based ranking (lower distance = better match)

Used by:
- RAG pipeline (query_search_engine)
"""

import faiss
import pickle
import numpy as np
from backend.rag.embeddings import get_embedding_model
from backend.utils.logger import get_logger
from backend.rag.background_indexer import index_lock
logger = get_logger("RETRIEVER")


class Retriever:

    def __init__(self):

        self.index = faiss.read_index("backend/rag/index/index.faiss")

        with open("backend/rag/index/meta.pkl", "rb") as f:
            self.metadata = pickle.load(f)

        self.embedding_model = get_embedding_model()

    def search(self, query, k=5, filters=None):
        """
        Perform semantic search over indexed document chunks.

        Workflow:
        1. Convert query into embedding vector using embedding model.
        2. Search FAISS index to retrieve top-k nearest neighbors.
        3. Attach similarity score (distance) to each result.
        4. Apply optional metadata filters:
            - doc_type
            - industry
        5. Return filtered and ranked results.

        Args:
            query (str): User query
            k (int): Number of top results to return
            filters (dict, optional): Metadata filters

        Returns:
            list[dict]:
                [
                    {
                        "doc_title": str,
                        "section": str,
                        "text": str,
                        "doc_type": str,
                        "industry": str,
                        "page_id": str,
                        "score": float
                    }
                ]

        Notes:
        - Lower score indicates higher similarity
        - Filtering is applied post-retrieval
        """

        logger.info(f"Search query: {query}")
        logger.info(f"Top K: {k}, Filters: {filters}")

        query_embedding = self.embedding_model.embed_query(query)

        query_vector = np.array([query_embedding]).astype("float32")

        with index_lock:
            distances, indices = self.index.search(query_vector, k)
            
        logger.info("FAISS search completed")

        results = []

        for i, idx in enumerate(indices[0]):

            chunk = self.metadata[idx]

            score = float(distances[0][i])

            print("---- DEBUG VERSION ----")
            print("Chunk:", chunk.get("version"))
            print("Filter:", filters.get("version"))

            # Apply metadata filters
            if filters:

                if filters.get("doc_type") and chunk["doc_type"] != filters["doc_type"]:
                    continue

                if filters.get("industry") and chunk["industry"] != filters["industry"]:
                    continue

                # ✅ VERSION FILTER FIX
                if filters.get("version"):

                    filter_version = str(filters["version"]).lower()
                    chunk_version = chunk.get("version")

                    # 🔥 CASE 1: latest → DO NOT filter (let FAISS return best)
                    if filter_version == "latest":
                        pass

                    # 🔥 CASE 2: specific version
                    else:
                        if str(chunk_version) != str(filters["version"]):
                            continue
                
            print("FINAL RESULTS AFTER FILTER:", len(results))
            
            #attach score to chunk
            chunk_with_score = {
                **chunk,
                "score": score
            }

            results.append(chunk_with_score)

            if len(results) >= k:
                break
        
        logger.info(f"Results returned: {len(results)}")


        results = sorted(
            results,
            key=lambda x: x["score"]  # lower = better
        )

        return results