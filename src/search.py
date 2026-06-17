import os
from pathlib import Path
from dotenv import load_dotenv
from src.vectorstore import FaissVectorStore
from src.data_loader import load_all_documents
from langchain_groq import ChatGroq

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


class RAGSearch:
    """
    RAGSearch coordinates the Retrieval-Augmented Generation (RAG) workflow.
    It retrieves relevant context chunks from the FaissVectorStore and utilizes
    ChatGroq (LLM) to answer questions based on the retrieved context.
    """

    def __init__(
        self,
        persist_dir: str = "faiss_store",
        embedding_model: str = "all-MiniLM-L6-v2",
        llm_model: str = "llama-3.3-70b-versatile",
    ):
        if not os.path.isabs(persist_dir):
            persist_dir = str((ROOT_DIR / persist_dir).resolve())

        self.vectorstore = FaissVectorStore(persist_dir, embedding_model)

        # Paths to vector index and metadata
        faiss_path = os.path.join(persist_dir, "faiss.index")
        meta_path = os.path.join(persist_dir, "metadata.pkl")

        # Automatically build the index if it doesn't exist on startup
        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
            print(f"[INFO] Vector store not found in '{persist_dir}'. Auto-building from data/ ...")
            docs = load_all_documents(str(ROOT_DIR / "data"))
            if not docs:
                print("[WARNING] No documents found in data/ folder to build vector store.")
            else:
                self.vectorstore.build_from_documents(docs)
        else:
            self.vectorstore.load()

        # Retrieve the API key from the environment (.env)
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        if groq_api_key:
            self.llm = ChatGroq(api_key=groq_api_key, model=llm_model)
            self.llm_ready = True
            print(f"[INFO] Groq LLM initialized with model: {llm_model}")
        else:
            self.llm = None
            self.llm_ready = False
            print("[WARNING] GROQ_API_KEY not set. LLM generation is disabled.")

    def search_and_summarize(self, query: str, top_k: int = 7) -> str:
        """
        Retrieves top_k context chunks from vector store and invokes the Groq LLM to
        produce a detailed, structured answer.  Uses an improved prompt that extracts
        maximum useful information from the retrieved context.
        """
        # 1. Retrieve most similar text chunks from the vector store
        results = self.vectorstore.query(query, top_k=top_k)

        # 2. Extract non-trivial text chunks (skip tiny/empty hits)
        texts = []
        for r in results:
            if r.get("metadata") and r["metadata"].get("text"):
                chunk_text = r["metadata"]["text"].strip()
                if len(chunk_text) > 30:
                    texts.append(chunk_text)

        context = "\n\n---\n\n".join(texts)
        if not context:
            return (
                "⚠️ No relevant content found in the indexed documents for your query.\n"
                "Please make sure documents are uploaded to the data/ folder and click 'Rebuild Index'."
            )

        # 3. Strong context-aware prompt — instructs LLM to be detailed and helpful
        prompt = (
            "You are an expert technical assistant with access to indexed study materials "
            "(textbooks, documentation, code examples, and notes). Your job is to give a thorough, "
            "accurate, and well-structured answer to the user's question based on the provided context.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Answer using ONLY the CONTEXT provided below. Do not use external knowledge.\n"
            "2. If the context contains relevant information, provide a complete, detailed answer.\n"
            "3. Use clear formatting: bullet points, numbered lists, code blocks, or sections as needed.\n"
            "4. Include examples or code snippets from the context when relevant.\n"
            "5. If context partially answers the question, provide the best answer possible with what's available.\n"
            "6. ONLY state 'I cannot answer' if the context has zero relevant information to the question.\n"
            "7. Never apologize or add disclaimers about limitations unless the context is truly empty.\n"
            "8. Be concise but comprehensive — avoid unnecessary fluff.\n\n"
            f"USER QUESTION: {query}\n\n"
            "RETRIEVED CONTEXT (from indexed documents):\n"
            "───────────────────────────────────────\n"
            f"{context}\n"
            "───────────────────────────────────────\n\n"
            "ANSWER (based on the context above):"
        )

        if not self.llm_ready:
            return (
                "⚠️ GROQ_API_KEY is not configured. Add it to your .env file.\n\n"
                "Retrieved context (without LLM answer):\n\n"
                f"{context}"
            )

        try:
            response = self.llm.invoke(prompt)
            return getattr(response, "content", str(response))
        except Exception as e:
            return (
                f"⚠️ Groq LLM call failed: {e}\n\n"
                "Please verify your GROQ_API_KEY in .env and the selected Groq model."
            )


# Example usage — run directly for a quick smoke test
if __name__ == "__main__":
    rag = RAGSearch()
    q = "What is a pointer in C?"
    print("Answer:", rag.search_and_summarize(q, top_k=5))
