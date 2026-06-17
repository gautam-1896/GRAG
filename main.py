import argparse
import os
import sys

def run_cli():
    """
    Runs the interactive Command Line Interface (CLI) for RAG querying.
    """
    print("\n" + "="*50)
    print("Welcome to YouTube RAG CLI!")
    print("Type your questions below. Commands available:")
    print("  /rebuild  - Rebuild the vector database from files in data/")
    print("  /config   - View or change configuration settings (e.g. top_k)")
    print("  /exit     - Exit the CLI tool")
    print("="*50 + "\n")
    
    # Lazy import to avoid loading models if arguments are wrong
    from src.search import RAGSearch
    
    persist_dir = "faiss_store"
    top_k = 5
    llm_model = "llama-3.3-70b-versatile"
    
    try:
        rag_search = RAGSearch(persist_dir=persist_dir, llm_model=llm_model)
    except Exception as e:
        print(f"[ERROR] Failed to initialize search pipeline: {e}")
        print("[INFO] Make sure you have your GROQ_API_KEY in .env and data files in data/")
        return

    while True:
        try:
            query = input("RAG Question > ").strip()
            if not query:
                continue
                
            if query.lower() == "/exit":
                print("Goodbye!")
                break
                
            elif query.lower() == "/rebuild":
                print("\n[INFO] Rebuilding index...")
                from src.data_loader import load_all_documents
                docs = load_all_documents("data")
                if not docs:
                    print("[WARNING] No documents found in 'data/' to build index.")
                else:
                    rag_search.vectorstore.build_from_documents(docs)
                continue
                
            elif query.lower() == "/config":
                print(f"\nCurrent Configuration:")
                print(f"  Vector Store Path: {persist_dir}")
                print(f"  Top K retrieved chunks: {top_k}")
                print(f"  LLM Model: {llm_model}")
                
                try:
                    new_k = input("Enter new top_k (or Enter to keep current): ").strip()
                    if new_k:
                        top_k = int(new_k)
                    new_model = input("Enter new model name (or Enter to keep current): ").strip()
                    if new_model:
                        llm_model = new_model
                        # Re-initialize LLM
                        from langchain_groq import ChatGroq
                        groq_api_key = os.getenv("GROQ_API_KEY")
                        rag_search.llm = ChatGroq(groq_api_key=groq_api_key or "", model_name=llm_model)
                    print("[SUCCESS] Configuration updated.")
                except ValueError:
                    print("[ERROR] Invalid value entered.")
                continue

            print("[INFO] Retrieving context and thinking...")
            answer = rag_search.search_and_summarize(query, top_k=top_k)
            print("\nAnswer:")
            print(answer)
            print("\n" + "-"*50 + "\n")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"[ERROR] Query failed: {e}\n")


def run_gui_server(port=8000):
    """
    Runs the FastAPI Web GUI Server.
    """
    import uvicorn
    print(f"[INFO] Starting Web GUI Server on http://localhost:{port}...")
    uvicorn.run("gui.server:app", host="127.0.0.1", port=port, reload=True)


def main():
    parser = argparse.ArgumentParser(description="YouTube RAG Command Center")
    parser.add_argument("--gui", action="store_true", help="Launch the Web GUI showcase")
    parser.add_argument("--cli", action="store_true", help="Launch interactive terminal CLI")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the GUI server on")
    
    args = parser.parse_args()
    
    # Default behavior: if no arguments are provided, launch CLI mode
    if args.gui:
        run_gui_server(port=args.port)
    else:
        run_cli()


if __name__ == "__main__":
    main()
