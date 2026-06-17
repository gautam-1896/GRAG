import os
import threading
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Resolve paths relative to this file — works from any CWD / inside Docker
SERVER_DIR = Path(__file__).resolve().parent
STATIC_DIR = SERVER_DIR / "static"
ROOT_DIR = SERVER_DIR.parent

# Load environment variables from project root .env
load_dotenv(ROOT_DIR / ".env")

# Lazy import of heavy RAG components (deferred until first API call)
from src.search import RAGSearch
from src.data_loader import load_all_documents

app = FastAPI(
    title="GRAG - Document Q&A API",
    description="Backend API supporting the premium glassmorphic Document Q&A interface",
    version="2.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global configuration & state ──────────────────────────────────────────────
persist_dir = str(ROOT_DIR / "faiss_store")
current_config = {
    "model_name": "llama-3.3-70b-versatile",
    "top_k": 7,
    "persist_dir": persist_dir,
}

rag_pipeline = None
pipeline_lock = threading.Lock()

rebuild_state = {
    "status": "idle",       # idle | building | completed | error
    "message": "System ready.",
    "document_count": 0,
    "chunk_count": 0,
}
rebuild_lock = threading.Lock()


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_pipeline():
    """Lazily initialise and return the shared RAGSearch instance."""
    global rag_pipeline
    with pipeline_lock:
        if rag_pipeline is None:
            try:
                rag_pipeline = RAGSearch(
                    persist_dir=current_config["persist_dir"],
                    llm_model=current_config["model_name"],
                )
            except Exception as e:
                print(f"[ERROR] Failed to load RAG pipeline: {e}")
        return rag_pipeline


def async_rebuild_worker():
    """Background thread: scan data/, embed, and rebuild the FAISS index."""
    global rag_pipeline

    with rebuild_lock:
        rebuild_state["status"] = "building"
        rebuild_state["message"] = "Scanning documents in data/ directory..."

    try:
        docs = load_all_documents(str(ROOT_DIR / "data"))

        if not docs:
            with rebuild_lock:
                rebuild_state["status"] = "completed"
                rebuild_state["message"] = (
                    "No files found in data/. "
                    "Add PDF/TXT/CSV files to the data/ folder and try again."
                )
            return

        with rebuild_lock:
            rebuild_state["message"] = (
                f"Loaded {len(docs)} document chunks. Building embeddings..."
            )
            rebuild_state["document_count"] = len(docs)

        pipeline = get_pipeline()
        pipeline.vectorstore.build_from_documents(docs)
        pipeline.vectorstore.load()

        with rebuild_lock:
            rebuild_state["status"] = "completed"
            rebuild_state["message"] = (
                f"Index rebuilt! {len(pipeline.vectorstore.metadata)} chunks indexed."
            )
            rebuild_state["chunk_count"] = len(pipeline.vectorstore.metadata)

    except Exception as e:
        with rebuild_lock:
            rebuild_state["status"] = "error"
            rebuild_state["message"] = f"Rebuild failed: {e}"
        print(f"[ERROR] Rebuild thread: {e}")


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None


class ConfigUpdateRequest(BaseModel):
    model_name: Optional[str] = None
    top_k: Optional[int] = None


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """Health check — used by Docker, load-balancers, and README curl examples."""
    return {"status": "ok", "message": "GRAG API is live and ready."}


@app.get("/api/status")
def get_status():
    """Return index status, loaded document list, and active configuration."""
    pipeline = get_pipeline()
    idx_exists = False
    chunks_len = 0
    docs_metadata = []

    if pipeline and pipeline.vectorstore and pipeline.vectorstore.index is not None:
        idx_exists = True
        chunks_len = len(pipeline.vectorstore.metadata)
        sources = set()
        for meta in pipeline.vectorstore.metadata:
            source = meta.get("source", "unknown")
            if source:
                sources.add(os.path.basename(source))
        docs_metadata = list(sources)

    with rebuild_lock:
        return {
            "index_exists": idx_exists,
            "chunk_count": chunks_len,
            "documents": docs_metadata,
            "config": current_config,
            "rebuild": rebuild_state,
        }


@app.post("/api/query")
def run_query(payload: QueryRequest):
    """Vector-search then LLM-summarise the query against indexed documents."""
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    pipeline = get_pipeline()
    if not pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline is not ready. Check server logs.",
        )

    top_k = payload.top_k or current_config["top_k"]

    try:
        results = pipeline.vectorstore.query(payload.query, top_k=top_k)
        answer = pipeline.search_and_summarize(payload.query, top_k=top_k)

        sources = [
            {
                "index": r["index"],
                "distance": r["distance"],
                "text": r["metadata"].get("text", "") if r["metadata"] else "",
                "source": (
                    os.path.basename(r["metadata"].get("source", "unknown"))
                    if r["metadata"]
                    else "unknown"
                ),
            }
            for r in results
        ]

        return {"query": payload.query, "answer": answer, "sources": sources}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rebuild")
def trigger_rebuild():
    """Kick off an asynchronous FAISS index rebuild in a background thread."""
    with rebuild_lock:
        if rebuild_state["status"] == "building":
            return {
                "status": "already_building",
                "message": "Rebuild already in progress.",
            }

    thread = threading.Thread(target=async_rebuild_worker, daemon=True)
    thread.start()
    return {"status": "started", "message": "Background rebuild started."}


@app.post("/api/config")
def update_config(payload: ConfigUpdateRequest):
    """Dynamically update the LLM model or top-k retrieval count."""
    global rag_pipeline

    if payload.model_name:
        current_config["model_name"] = payload.model_name
        with pipeline_lock:
            rag_pipeline = None   # force re-init with new model

    if payload.top_k is not None:
        current_config["top_k"] = payload.top_k

    return {"status": "success", "config": current_config}


# ── Static files ──────────────────────────────────────────────────────────────
os.makedirs(str(STATIC_DIR), exist_ok=True)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
