from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.search import RAGSearch


class SearchRequest(BaseModel):
    query: str = Field(..., example="What is attention mechanism?")
    top_k: int = Field(5, ge=1, le=20)


class SearchResponse(BaseModel):
    query: str
    top_k: int
    answer: str


app = FastAPI(
    title="GRAG API",
    version="1.0.0",
    description="FastAPI endpoint for the GRAG retrieval-augmented generation pipeline."
)


@app.on_event("startup")
async def startup_event():
    app.state.rag_search = RAGSearch(persist_dir="faiss_store")


@app.get("/health")
async def health():
    return {"status": "ok", "message": "GRAG FastAPI is ready."}


@app.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    rag_search = getattr(app.state, "rag_search", None)
    if rag_search is None:
        raise HTTPException(status_code=500, detail="RAG search pipeline is not initialized.")

    answer = rag_search.search_and_summarize(request.query, top_k=request.top_k)
    return SearchResponse(query=request.query, top_k=request.top_k, answer=answer)
