FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY src/ ./src/
COPY gui/ ./gui/
COPY main.py ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Create data and faiss_store directories
RUN mkdir -p data faiss_store

EXPOSE 8000
# Run the correct full GUI FastAPI server (not the root stub)
CMD ["uvicorn", "gui.server:app", "--host", "0.0.0.0", "--port", "8000"]
