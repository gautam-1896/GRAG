import os
from pathlib import Path
import faiss
import numpy as np
import pickle
from typing import List, Any
from sentence_transformers import SentenceTransformer
from src.embedding import EmbeddingPipeline


class FaissVectorStore:
    """
    FaissVectorStore implements a vector database interface using Facebook AI Similarity Search (FAISS).
    It manages the index creation, document embedding addition, vector persistence (saving/loading),
    and similarity search queries.
    """
    def __init__(self, persist_dir: str = "faiss_store", embedding_model: str = "all-MiniLM-L6-v2", chunk_size: int = 1500, chunk_overlap: int = 300):
        self.persist_dir = Path(persist_dir)
        if not self.persist_dir.is_absolute():
            self.persist_dir = Path(__file__).resolve().parents[1] / self.persist_dir
        self.persist_dir = self.persist_dir.resolve()
        # Ensure directories exist
        os.makedirs(self.persist_dir, exist_ok=True)
        self.index = None
        self.metadata = []
        self.embedding_model = embedding_model
        # SentenceTransformer to convert incoming string queries to embeddings locally
        self.model = SentenceTransformer(embedding_model)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print(f"[INFO] Loaded embedding model for search: {embedding_model}")

    def build_from_documents(self, documents: List[Any]):
        """
        Takes raw document objects, chunks them, generates embeddings,
        adds them to FAISS, and automatically persists the data.
        """
        print(f"[INFO] Building vector store from {len(documents)} raw documents...")
        emb_pipe = EmbeddingPipeline(model_name=self.embedding_model, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        chunks = emb_pipe.chunk_documents(documents)
        embeddings = emb_pipe.embed_chunks(chunks)
        # Store raw page contents in metadata associated with each vector index
        metadatas = [{"text": chunk.page_content, "source": chunk.metadata.get("source", "unknown")} for chunk in chunks]
        self.add_embeddings(np.array(embeddings).astype('float32'), metadatas)
        self.save()
        print(f"[INFO] Vector store built and saved to {self.persist_dir}")

    def add_embeddings(self, embeddings: np.ndarray, metadatas: List[Any] = None):
        """
        Adds vector embeddings and metadata to the internal FAISS index and local metadata store.
        """
        dim = embeddings.shape[1]
        if self.index is None:
            # L2 distance metric IndexFlatL2 for standard Euclidean similarity
            self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)
        if metadatas:
            self.metadata.extend(metadatas)
        print(f"[INFO] Added {embeddings.shape[0]} vectors to Faiss index.")

    def save(self):
        """
        Saves the FAISS index structure and metadata pickle file to disk.
        """
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        faiss.write_index(self.index, faiss_path)
        with open(meta_path, "wb") as f:
            pickle.dump(self.metadata, f)
        print(f"[INFO] Saved Faiss index and metadata to {self.persist_dir}")

    def load(self):
        """
        Loads the FAISS index structure and metadata pickle file from disk.
        """
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
            raise FileNotFoundError(f"Index or metadata not found in {self.persist_dir}")
        self.index = faiss.read_index(faiss_path)
        with open(meta_path, "rb") as f:
            self.metadata = pickle.load(f)
        print(f"[INFO] Loaded Faiss index and metadata from {self.persist_dir}")

    def search(self, query_embedding: np.ndarray, top_k: int = 5):
        """
        Queries FAISS using the raw vector embedding and returns the top k closest matches.
        """
        if self.index is None:
            raise ValueError("FAISS index has not been initialized or loaded.")
        D, I = self.index.search(query_embedding, top_k)
        results = []
        # Return results along with document text metadata and search distance metrics
        for idx, dist in zip(I[0], D[0]):
            meta = self.metadata[idx] if (idx >= 0 and idx < len(self.metadata)) else None
            results.append({"index": int(idx), "distance": float(dist), "metadata": meta})
        return results

    def query(self, query_text: str, top_k: int = 5):
        """
        Takes a string query, converts it to a vector, and queries the vector store.
        """
        print(f"[INFO] Querying vector store for: '{query_text}'")
        query_emb = self.model.encode([query_text]).astype('float32')
        return self.search(query_emb, top_k=top_k)


# Example usage
if __name__ == "__main__":
    from src.data_loader import load_all_documents
    docs = load_all_documents("data")
    store = FaissVectorStore("faiss_store")
    store.build_from_documents(docs)
    store.load()
    print(store.query("What is attention mechanism?", top_k=3))
