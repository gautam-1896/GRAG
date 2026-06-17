import tempfile
from pathlib import Path
from src.data_loader import load_all_documents
from src.vectorstore import FaissVectorStore


def test_load_all_documents_from_text_file():
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "sample.txt"
        path.write_text("Hello GRAG test content.")
        documents = load_all_documents(str(tmp_dir))
        assert len(documents) == 1
        assert "Hello GRAG test content." in documents[0].page_content


def test_faiss_vectorstore_initializes(tmp_path):
    store_dir = tmp_path / "store"
    store = FaissVectorStore(str(store_dir))
    assert store.persist_dir.exists()
    assert store.index is None
    assert store.metadata == []
