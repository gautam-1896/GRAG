# 🚀 GRAG Quick Start Guide

## Get Started in 5 Minutes

### Step 1: Clone & Setup
```powershell
# Navigate to project
cd GRAG

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Key
```powershell
# Edit .env file
notepad .env

# Add your Groq API key (get free at https://console.groq.com)
GROQ_API_KEY=gsk_your_actual_key_here
```

### Step 3: Add Documents
```powershell
# Create data folder if needed
mkdir -p data\text_files

# Copy your documents to data/ folder
# Supports: .pdf, .txt, .csv, .docx, .json
```

### Step 4: Start the Portal
```powershell
# Launch GUI
python main.py --gui

# Or use FastAPI directly
uvicorn gui.server:app --host 127.0.0.1 --port 8000
```

### Step 5: Open in Browser
```
http://localhost:8000
```

---

## GUI Features

### 🔍 Search
1. Type your question in the search box
2. Press Enter or click Search
3. System retrieves relevant chunks and generates answer

### 📊 Sidebar Status
- **Vector Database Status** - Shows if index is loaded
- **Chunks Indexed** - Total document chunks available
- **Rebuild Index** - Reprocess documents after adding new files

### 📄 Source Drawer
- Shows which documents were used to answer
- Displays relevance distance
- Preview of retrieved text chunks

### ⚙️ Configuration Panel
- Change LLM model
- Adjust top_k (number of chunks to retrieve)
- View system status

---

## Command Line Usage

### Start CLI Mode
```powershell
python main.py --cli
```

### Query via API
```powershell
$query = @{query="What is machine learning?"; top_k=7} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/api/query `
  -Method Post -ContentType "application/json" -Body $query
```

### Check Server Status
```powershell
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost:8000/api/status
```

### Rebuild Index
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/rebuild -Method Post
```

---

## Troubleshooting

### Issue: "Invalid API Key"
- ✅ **Solution**: Add valid Groq API key to `.env`
- Get free key at https://console.groq.com

### Issue: "No relevant content found"
- ✅ **Solution**: Add documents to `data/` folder and rebuild index
- Click "Rebuild Index" button in GUI

### Issue: "Module not found"
- ✅ **Solution**: Activate virtual environment
  ```powershell
  .\.venv\Scripts\activate
  ```

### Issue: Port 8000 already in use
- ✅ **Solution**: Use different port
  ```powershell
  uvicorn gui.server:app --port 9000
  ```

---

## Document Formats

| Format | Support | Notes |
|--------|---------|-------|
| PDF | ✅ | Single & multi-page |
| TXT | ✅ | UTF-8 encoded |
| CSV | ✅ | Comma-separated values |
| DOCX | ✅ | Word documents |
| JSON | ✅ | Valid JSON structure |
| XLSX | ✅ | Excel files |

---

## Performance Tips

1. **Larger Documents**
   - System chunks documents (1500 chars per chunk)
   - More chunks = better context coverage

2. **Better Answers**
   - Use specific, detailed questions
   - Ask about topics covered in your documents
   - System retrieves 7 best chunks by default

3. **Faster Responses**
   - Keep document count reasonable
   - Remove irrelevant documents
   - Use specific model (Groq models are fast)

---

## Deployment

### Docker
```bash
# Build image
docker build -t grag-app .

# Run container
docker run -p 8000:8000 -e GROQ_API_KEY=your_key grag-app

# Access at http://localhost:8000
```

### Environment Variables
```
GROQ_API_KEY=your_api_key_here
```

---

## Resources

- 📚 **Full Documentation**: See README.md
- 🔧 **Technical Details**: See IMPROVEMENTS.md
- 📊 **Architecture**: See GRAG_COMPLETION_REPORT.md
- 🎓 **Learn More**: [Krish Naik YouTube](https://www.youtube.com/@krishnaik06)

---

## Common Questions

**Q: Can I use different LLM models?**  
A: Yes! Update `model_name` in GUI config panel. Groq supports multiple models.

**Q: What's the maximum file size?**  
A: No strict limit, but very large files (>100MB) may take time to process.

**Q: Can I delete documents?**  
A: Remove files from `data/` and click "Rebuild Index".

**Q: Does it work offline?**  
A: No, it requires Groq API access for LLM generation. Vector search works locally.

---

## Next Steps

1. ✅ Add your documents to `data/` folder
2. ✅ Click "Rebuild Index" to process them
3. ✅ Start asking questions!
4. ✅ Use source drawer to verify answers
5. ✅ Adjust top_k if needed for better context

---

**Happy Learning with GRAG! 🎉**
