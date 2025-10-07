# RAG Chatbot - AI/ML & Data Engineering Assistant

A sophisticated Retrieval-Augmented Generation (RAG) chatbot with dual persona support for AI/ML and Data Engineering domains. Features text chat and audio-to-text transcription with intelligent query classification and context-aware responses.

## 🚀 Features

- **Dual Persona Support**: Automatically classifies queries as AI/ML or Data Engineering focused
- **Audio Input**: Record audio questions that get transcribed using OpenAI Whisper
- **RAG Architecture**: Retrieves relevant context from knowledge base before generating responses
- **FAISS Vector Search**: Fast similarity search using Facebook's FAISS library
- **Modern UI**: Clean, responsive web interface with real-time chat
- **Source Attribution**: Shows which knowledge base files influenced each response

## 📁 Project Structure

```
rag-chatbot/
├── kb/                    # Knowledge base files
│   ├── ai_ml/            # AI/ML related documents
│   └── data_eng/         # Data Engineering documents
├── store/                # Generated vector index and metadata
├── frontend/             # Web UI
│   └── index.html       # Chat interface
├── ingest.py            # Knowledge ingestion script
├── server.py            # FastAPI server
├── requirements.txt     # Python dependencies
└── .env.example        # Environment variables template
```

## 🛠️ Setup Instructions

**Requires Python 3.9 or higher**

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Example `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o
```

### 3. Add Knowledge Base Files

Place your `.md` or `.txt` files in the appropriate directories:
- `kb/ai_ml/` - AI/ML related documents
- `kb/data_eng/` - Data Engineering documents

Files can include YAML frontmatter for tags:
```markdown
---
tags: [rag, embeddings, vector-db]
---

Your content here...
```

### 4. Ingest Knowledge Base

```bash
python ingest.py
```

This will:
- Read all files from `kb/ai_ml/` and `kb/data_eng/`
- Chunk the text with overlapping windows
- Generate embeddings using OpenAI
- Build a FAISS vector index
- Save index and metadata to `store/`

### 5. Start the Server

```bash
uvicorn server:app --reload --port 8000
```

### 6. Open the Frontend

Open `frontend/index.html` in your browser or serve it with a simple HTTP server:

```bash
cd frontend
python -m http.server 3000
```

Then visit `http://localhost:3000`

## 🎯 Usage

### Text Chat
1. Type your question in the input field
2. Select mode: Auto, AI/ML Focus, or Data Engineering Focus
3. Click Send or press Enter

### Audio Input
1. Click the Record button
2. Speak your question
3. Click Stop to transcribe
4. Review the transcript and click "Use This" or let it auto-send

### Mode Selection
- **Auto**: Server automatically classifies your query as AI/ML or Data Engineering
- **AI/ML Focus**: Forces responses to use AI/ML persona and knowledge
- **Data Engineering Focus**: Forces responses to use Data Engineering persona and knowledge

## 🔧 API Endpoints

### POST /chat
Main chat endpoint with RAG functionality.

**Request:**
```json
{
  "message": "How do I optimize a PySpark DataFrame?",
  "mode": "auto",
  "conversation_history": []
}
```

**Response:**
```json
{
  "answer": "To optimize a PySpark DataFrame...",
  "sources": [
    {
      "file": "databricks_pyspark.md",
      "preview": "PySpark performance optimization strategies..."
    }
  ],
  "mode_used": "de"
}
```

### POST /transcribe
Transcribe audio using OpenAI Whisper.

**Request:** Multipart form with audio file

**Response:**
```json
{
  "transcript": "How do I set up a data pipeline?"
}
```

## 🧠 How It Works

1. **Knowledge Ingestion**: Documents are chunked and embedded using OpenAI's embedding model
2. **Query Classification**: Incoming queries are classified as AI/ML or Data Engineering focused
3. **Retrieval**: FAISS searches for relevant chunks based on semantic similarity
4. **Context Building**: Retrieved chunks are combined with persona-specific prompts
5. **Generation**: GPT-4 generates responses grounded in the retrieved context
6. **Response**: Returns answer, sources, and mode used

## 🔄 Updating Knowledge

1. Add or edit files in `kb/ai_ml/` or `kb/data_eng/`
2. Re-run `python ingest.py` to rebuild the index
3. Restart the server: `uvicorn server:app --reload --port 8000`

**Quick update command:**
```bash
python ingest.py && uvicorn server:app --reload --port 8000
```

## 🛡️ Security Considerations

- Set up proper CORS origins in production
- Add authentication tokens for API endpoints
- Validate and sanitize all user inputs
- Implement rate limiting for API calls
- Use environment variables for sensitive configuration

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
OPENAI_API_KEY=your_api_key
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o
```

## 📊 Performance Optimization

- **Chunking**: Optimize chunk size (default: 1000 tokens) and overlap (default: 200 tokens)
- **Embeddings**: Use appropriate embedding model for your domain
- **Caching**: Cache frequently accessed embeddings and responses
- **Indexing**: Regularly optimize FAISS index for better performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your knowledge base files or improvements
4. Test your changes
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT and Whisper APIs
- Facebook AI Research for FAISS
- FastAPI for the web framework
- The open-source community for various libraries
