# GRAG — Generative Retrieval-Augmented Generation 🚀

A **production-ready Document Q&A portal** powered by **FAISS** vector search and **Groq LLM**.
Ask intelligent questions against your uploaded PDFs, textbooks, code docs, and more.

## ✨ Key Features

- 🔍 **Smart Vector Search** - FAISS-based semantic search with 5,271+ indexed chunks
- 🧠 **Generative Answers** - Powered by Groq's llama-3.3-70b LLM for accurate, formatted responses
- 📄 **Multi-Format Support** - PDF, TXT, CSV, DOCX, JSON document loading
- 💻 **Web Interface** - Modern glassmorphic dark-themed UI with real-time status
- 🔧 **Easy Setup** - One-command installation and deployment
- 🐳 **Docker Ready** - Production deployment in minutes
- ⚡ **High Performance** - Sub-second query response times
- 📊 **Source Attribution** - View exact documents used for each answer

## 🎯 Live Demo

Simply run the application and open your browser:

```powershell
cd d:\YTRAG
python main.py --gui
# Opens http://127.0.0.1:8000 automatically
```

**Try These Questions:**
- "What is a pointer in C?"
- "Explain machine learning concepts"
- "How do data structures work?"

## Setup

1. Create a Python 3.13+ virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Groq API key:
   ```text
   GROQ_API_KEY=your_api_key_here
   ```
4. Add documents (PDF, TXT, CSV, DOCX, JSON) to the `data/` folder.

## Run

### Web GUI (recommended)
```powershell
python main.py --gui
# then open http://localhost:8000
```

### CLI mode
```powershell
python main.py --cli
```

### Custom port
```powershell
python main.py --gui --port 9000
```

## FastAPI Server

- Start server:
  ```powershell
  uvicorn gui.server:app --host 127.0.0.1 --port 8000
  ```
- Health check:
  ```powershell
  curl http://127.0.0.1:8000/health
  ```
- System status:
  ```powershell
  curl http://127.0.0.1:8000/api/status
  ```
- Example query:
  ```powershell
  curl -X POST http://127.0.0.1:8000/api/query `
       -H "Content-Type: application/json" `
       -d "{\"query\": \"What is a pointer in C?\", \"top_k\": 5}"
  ```
- Rebuild index:
  ```powershell
  curl -X POST http://127.0.0.1:8000/api/rebuild
  ```

## Deployment

### Docker
```bash
# Build
docker build -t grag-app .

# Run (pass your key as env var — never bake keys into the image)
docker run -p 8000:8000 -e GROQ_API_KEY=your_key grag-app
```

### Makefile shortcuts
```bash
make install   # Create venv and install deps
make run       # Run CLI
make serve     # Start FastAPI server
make test      # Run pytest
make docker    # Build Docker image
```

## CI / GitHub Actions

A GitHub Actions workflow is at `.github/workflows/ci.yml`.
It installs all dependencies (via `requirements-dev.txt` which includes `requirements.txt`)
and runs pytest on every push and pull request.

## Project Structure

```
GRAG/
├── main.py              ← CLI + GUI launcher (argparse)
├── app.py               ← Standalone smoke-test runner
├── server.py            ← Minimal REST API (legacy)
├── gui/
│   ├── server.py        ← Full FastAPI backend (active)
│   └── static/          ← HTML + CSS + JS frontend
├── src/
│   ├── data_loader.py   ← Multi-format document loader
│   ├── embedding.py     ← SentenceTransformer chunking & embedding
│   ├── vectorstore.py   ← FAISS index management
│   └── search.py        ← RAG orchestrator (retrieval + Groq LLM)
├── tests/               ← pytest suite
├── Dockerfile
└── pyproject.toml
```

## Notes

- The vector store is persisted in `faiss_store/`.
- `data/` should contain supported files: `.pdf`, `.txt`, `.csv`, `.docx`, `.json`.
- `.gitignore` excludes `.env`, `.venv`, and persisted vector store files.

---

### 📚 **Resources & Acknowledgments**

Built with inspiration from **[Krish Naik](https://www.youtube.com/@krishnaik06)** — An exceptional educator in the field of Data Science and AI. His comprehensive tutorials on RAG, LLMs, and vector databases were instrumental in the development of GRAG.
