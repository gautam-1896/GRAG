from typing import List, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
from src.data_loader import load_all_documents


class EmbeddingPipeline:
    """
    EmbeddingPipeline handles text splitting (chunking) and embedding generation.
    It prepares raw documents for indexing in a vector store.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", chunk_size: int = 1000, chunk_overlap: int = 200):
        # Configuration for text splitting
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Initialize local SentenceTransformer model (downloads on first run if not cached)
        self.model = SentenceTransformer(model_name)
        print(f"[INFO] Loaded embedding model: {model_name}")

    def chunk_documents(self, documents: List[Any]) -> List[Any]:
        """
        Splits loaded LangChain Document objects into smaller chunks
        based on the chunk_size and chunk_overlap settings.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        print(
            f"[INFO] Split {len(documents)} documents into {len(chunks)} chunks.")
        return chunks

    def embed_chunks(self, chunks: List[Any]) -> np.ndarray:
        """
        Generates dense vector embeddings for list of Document chunks using SentenceTransformer.
        """
        texts = [chunk.page_content for chunk in chunks]
        print(f"[INFO] Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        print(f"[INFO] Embeddings shape: {embeddings.shape}")
        return embeddings


# Example usage
if __name__ == "__main__":
    docs = load_all_documents("data")
    emb_pipe = EmbeddingPipeline()
    chunks = emb_pipe.chunk_documents(docs)
    embeddings = emb_pipe.embed_chunks(chunks)
    
    # Safely print example embedding shape or None
    if len(embeddings) > 0:
        print(f"[INFO] Example embeddings shape: {embeddings.shape}")
    else:
        print("[INFO] No embeddings generated.")
