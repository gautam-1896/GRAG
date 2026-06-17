from src.search import RAGSearch

def main():
    """
    A simple script to test the YouTube RAG search pipeline.
    It initializes RAGSearch and performs a sample query.
    """
    print("[START] Running RAG Search test...")
    try:
        # Initialize RAGSearch pipeline (automatically builds index if not present)
        rag_search = RAGSearch(persist_dir="faiss_store")
        
        # Test Query
        query = "What is attention mechanism?"
        print(f"\n[QUERY] Searching for: '{query}'")
        summary = rag_search.search_and_summarize(query, top_k=3)
        
        print("\n=== Result Summary ===")
        print(summary)
        print("======================\n")
    except Exception as e:
        print(f"\n[ERROR] Pipeline run failed: {e}")


if __name__ == "__main__":
    main()
