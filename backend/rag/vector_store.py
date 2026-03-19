"""
Vector Store Module (FAISS)

This module manages storage and retrieval of embeddings using FAISS.

Responsibilities:
- Store embeddings and associated metadata
- Perform similarity search
- Persist index and metadata to disk

Key Features:
- Fast nearest neighbor search using FAISS
- Supports large-scale vector storage
- Maintains metadata for each vector (for citations)

Used by:
- build_index.py (index creation)
- retriever.py (search queries)
"""
import faiss
import numpy as np
import pickle


class VectorStore:
    """
    FAISS-based vector storage for embeddings and metadata.

    Attributes:
        index: FAISS index instance
        metadata (list): List of chunk metadata corresponding to vectors
    """

    def __init__(self):

        self.index = None
        self.metadata = []

    def add(self, embeddings, chunks):
        """
        Add embeddings and corresponding metadata to the vector store.

        Args:
            embeddings (list[list[float]]): List of embedding vectors
            chunks (list[dict]): Corresponding metadata for each embedding

        Notes:
        - Initializes FAISS index if not already created
        - Uses L2 distance for similarity search
        - Metadata is stored alongside embeddings for retrieval
        """

        vectors = np.array(embeddings).astype("float32")

        if self.index is None:
            dim = vectors.shape[1]
            self.index = faiss.IndexFlatL2(dim)

        self.index.add(vectors)

        self.metadata.extend(chunks)

    def search(self, query_embedding, k=5):
        """
        Perform similarity search using FAISS index.

        Args:
            query_embedding (list[float]): Embedding vector of query
            k (int): Number of nearest neighbors to retrieve

        Returns:
            list[dict]: Top-k matching chunks with metadata

        Notes:
        - Uses L2 distance (lower = more similar)
        - Returns metadata corresponding to nearest vectors
        """

        D, I = self.index.search(
            np.array([query_embedding]).astype("float32"),
            k
        )

        return [self.metadata[i] for i in I[0]]

    def save(self, path):
        """
        Save FAISS index and metadata to disk.

        Args:
            path (str): Directory path to store index files

        Outputs:
            - index.faiss → FAISS index file
            - meta.pkl → Metadata file

        Notes:
        - Required for loading index during retrieval
        - Metadata is serialized using pickle
        """

        faiss.write_index(self.index, f"{path}/index.faiss")

        with open(f"{path}/meta.pkl", "wb") as f:
            pickle.dump(self.metadata, f)