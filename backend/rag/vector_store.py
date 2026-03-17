import faiss
import numpy as np
import pickle


class VectorStore:

    def __init__(self):

        self.index = None
        self.metadata = []

    def add(self, embeddings, chunks):

        vectors = np.array(embeddings).astype("float32")

        if self.index is None:
            dim = vectors.shape[1]
            self.index = faiss.IndexFlatL2(dim)

        self.index.add(vectors)

        self.metadata.extend(chunks)

    def search(self, query_embedding, k=5):

        D, I = self.index.search(
            np.array([query_embedding]).astype("float32"),
            k
        )

        return [self.metadata[i] for i in I[0]]

    def save(self, path):

        faiss.write_index(self.index, f"{path}/index.faiss")

        with open(f"{path}/meta.pkl", "wb") as f:
            pickle.dump(self.metadata, f)