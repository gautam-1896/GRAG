from pathlib import Path
from typing import List, Any
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader


def load_all_documents(data_dir: str) -> List[Any]:
    """
    Load all supported files from the data directory and convert them to LangChain Document structures.
    Supported: PDF, TXT, CSV, Excel (xlsx), Word (docx), JSON
    
    If optional parser libraries (unstructured, docx2txt, openpyxl) are missing,
    the loader will print a warning and skip those files rather than crashing.
    """
    root_path = Path(__file__).resolve().parents[1]
    data_path = Path(data_dir)
    if not data_path.is_absolute():
        data_path = (root_path / data_path).resolve()

    print(f"[DEBUG] Data path resolved to: {data_path}")
    documents = []

    if not data_path.exists():
        print(f"[WARNING] Data directory not found at {data_path}. Please create it or update the path.")
        return documents

    # 1. PDF Files
    pdf_files = list(data_path.glob('**/*.pdf'))
    print(f"[DEBUG] Found {len(pdf_files)} PDF files: {[f.name for f in pdf_files]}")
    for pdf_file in pdf_files:
        print(f"[DEBUG] Loading PDF: {pdf_file.name}")
        try:
            loader = PyPDFLoader(str(pdf_file))
            loaded = loader.load()
            print(f"[DEBUG] Loaded {len(loaded)} PDF pages from {pdf_file.name}")
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Failed to load PDF {pdf_file.name}: {e}")

    # 2. Text (TXT) Files
    txt_files = list(data_path.glob('**/*.txt'))
    print(f"[DEBUG] Found {len(txt_files)} TXT files: {[f.name for f in txt_files]}")
    for txt_file in txt_files:
        print(f"[DEBUG] Loading TXT: {txt_file.name}")
        try:
            loader = TextLoader(str(txt_file), encoding='utf-8')
            loaded = loader.load()
            print(f"[DEBUG] Loaded {len(loaded)} TXT docs from {txt_file.name}")
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Failed to load TXT {txt_file.name}: {e}")

    # 3. CSV Files
    csv_files = list(data_path.glob('**/*.csv'))
    print(f"[DEBUG] Found {len(csv_files)} CSV files: {[f.name for f in csv_files]}")
    for csv_file in csv_files:
        print(f"[DEBUG] Loading CSV: {csv_file.name}")
        try:
            loader = CSVLoader(str(csv_file))
            loaded = loader.load()
            print(f"[DEBUG] Loaded {len(loaded)} CSV records from {csv_file.name}")
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Failed to load CSV {csv_file.name}: {e}")

    # 4. Excel (XLSX) Files - Dynamically loaded
    xlsx_files = list(data_path.glob('**/*.xlsx'))
    print(f"[DEBUG] Found {len(xlsx_files)} Excel files: {[f.name for f in xlsx_files]}")
    if xlsx_files:
        try:
            # Check for required Excel-parsing dependencies
            import unstructured
            import openpyxl
            from langchain_community.document_loaders.excel import UnstructuredExcelLoader
            
            for xlsx_file in xlsx_files:
                print(f"[DEBUG] Loading Excel: {xlsx_file.name}")
                try:
                    loader = UnstructuredExcelLoader(str(xlsx_file))
                    loaded = loader.load()
                    print(f"[DEBUG] Loaded {len(loaded)} Excel rows/docs from {xlsx_file.name}")
                    documents.extend(loaded)
                except Exception as e:
                    print(f"[ERROR] Failed to load Excel {xlsx_file.name}: {e}")
        except ImportError:
            print("[WARNING] Skipping Excel files. Please run `pip install openpyxl unstructured` to enable Excel loading.")

    # 5. Word (DOCX) Files - Dynamically loaded
    docx_files = list(data_path.glob('**/*.docx'))
    print(f"[DEBUG] Found {len(docx_files)} Word files: {[f.name for f in docx_files]}")
    if docx_files:
        try:
            # Check for Word-parsing dependency
            import docx2txt
            from langchain_community.document_loaders import Docx2txtLoader
            
            for docx_file in docx_files:
                print(f"[DEBUG] Loading Word: {docx_file.name}")
                try:
                    loader = Docx2txtLoader(str(docx_file))
                    loaded = loader.load()
                    print(f"[DEBUG] Loaded {len(loaded)} Word paragraphs from {docx_file.name}")
                    documents.extend(loaded)
                except Exception as e:
                    print(f"[ERROR] Failed to load Word {docx_file.name}: {e}")
        except ImportError:
            print("[WARNING] Skipping Word files. Please run `pip install docx2txt` to enable Word loading.")

    # 6. JSON Files - Dynamically loaded and schema error protected
    json_files = list(data_path.glob('**/*.json'))
    print(f"[DEBUG] Found {len(json_files)} JSON files: {[f.name for f in json_files]}")
    if json_files:
        try:
            from langchain_community.document_loaders import JSONLoader
            
            for json_file in json_files:
                print(f"[DEBUG] Loading JSON: {json_file.name}")
                try:
                    # By default JSONLoader requires a jq schema. We provide a simple fallback if schema/jq fails
                    loader = JSONLoader(str(json_file), jq_schema=".[]", text_content=False)
                    loaded = loader.load()
                    print(f"[DEBUG] Loaded {len(loaded)} JSON elements from {json_file.name}")
                    documents.extend(loaded)
                except Exception as e:
                    print(f"[WARNING] JSONLoader failed with jq schema: {e}. Falling back to simple TextLoader.")
                    try:
                        loader = TextLoader(str(json_file), encoding='utf-8')
                        loaded = loader.load()
                        documents.extend(loaded)
                    except Exception as fe:
                        print(f"[ERROR] JSON fallback text loader failed: {fe}")
        except ImportError:
            print("[WARNING] Skipping JSON files. JSONLoader import failed.")

    print(f"[DEBUG] Total loaded document chunks: {len(documents)}")
    return documents


# Example usage
if __name__ == "__main__":
    docs = load_all_documents("data")
    print(f"Total loaded: {len(docs)} documents.")
    if docs:
        print("Example document preview (first 200 chars):")
        print(docs[0].page_content[:200])
