# RAG Chatbot - Interview Preparation Assistant

A dual-persona RAG (Retrieval-Augmented Generation) chatbot designed for interview preparation, supporting both AI/ML/Data Engineering (Krishna) and Business Intelligence/Analytics Engineering (Tejuu) profiles.

## 🏗️ Project Structure

```
rag-chatbot/
├── api/                          # Backend API modules
│   ├── chat.py                   # Chat endpoint handlers
│   ├── health.py                 # Health check endpoints
│   ├── transcribe.py             # Audio transcription
│   ├── utils.py                  # Core RAG logic and utilities
│   ├── embeddings.npy            # Vector embeddings
│   ├── faiss.index              # FAISS vector index
│   └── meta.json                # Metadata for embeddings
├── core/                         # Core application logic
│   ├── answer_v2.py             # Enhanced answer generation
│   ├── enhanced_answer.py       # Template-based answering
│   ├── memory.py                # Conversation memory
│   ├── profile_ctx.py           # Profile context management
│   ├── router.py                # Intent routing
│   └── templates/               # Template system
│       ├── fragments/           # Template fragments
│       ├── loader.py            # Template loader
│       ├── prompter.py          # Template processor
│       └── registry.py          # Template registry
├── frontend/                     # React frontend
│   ├── src/                     # Source code
│   ├── public/                  # Static assets
│   ├── build/                   # Production build
│   └── package.json             # Frontend dependencies
├── kb_krishna/                  # Krishna's knowledge base
│   ├── ai_ml/                   # AI/ML content
│   └── data_engineering/        # Data Engineering content
├── kb_tejuu/                    # Tejuu's knowledge base
│   ├── analytics_mode/          # Analytics Engineering content
│   └── business_mode/           # Business Intelligence content
├── content/                     # Profile configurations
│   ├── metrics/                 # Performance metrics
│   └── profiles/                # Profile definitions
├── config/                      # Deployment configurations
│   ├── vercel.json             # Vercel deployment config
│   ├── render.yaml             # Render deployment config
│   ├── Procfile                # Heroku deployment config
│   └── runtime.txt             # Python runtime version
├── scripts/                     # Utility scripts
│   ├── generate_embeddings.py   # Generate embeddings
│   ├── generate_multi_profile_embeddings.py
│   └── ingest.py               # Knowledge base ingestion
├── tests/                       # Test files
│   └── phase2_runner.py        # Phase 2 test runner
├── docs/                        # Documentation
│   └── *.md                    # All documentation files
├── store/                       # Data storage
│   ├── embeddings.npy          # Vector embeddings
│   ├── faiss.index             # FAISS vector index
│   └── meta.json               # Metadata
├── server.py                    # Main FastAPI server (local dev)
├── render_app.py               # Render deployment server
├── requirements.txt            # Python dependencies
└── build.sh                    # Build script
```

## 🚀 Quick Start

### Local Development

1. **Install Dependencies**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

2. **Set Environment Variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

3. **Start the Application**
   ```bash
   # Start backend server
   python server.py
   
   # In another terminal, start frontend
   cd frontend
   npm start
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

### Production Deployment

#### Render Deployment
```bash
# Uses render_app.py and config/render.yaml
# Automatically builds frontend and serves both
```

#### Vercel Deployment
```bash
# Frontend only - uses config/vercel.json
# Backend should be deployed separately
```

## 🎯 Features

### Dual Persona Support
- **Krishna**: AI/ML Engineer & Data Engineer
- **Tejuu**: Business Intelligence Developer & Analytics Engineer

### Intelligent Routing
- Auto-detects question type and domain
- Routes to appropriate persona and mode
- Supports manual profile/mode selection

### Advanced RAG
- Vector similarity search with FAISS
- Context-aware retrieval
- Citation support with source tracking

### Template System
- Structured response generation
- Follow-up question detection
- Humanized conversation flow

### Audio Support
- Voice input via OpenAI Whisper
- Real-time transcription

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI API access
- `RETRIEVAL_TOPK`: Number of top results to retrieve (default: 6)
- `USE_LLM`: Enable/disable LLM generation (default: false)

### Profile Configuration
- Profiles defined in `content/profiles/`
- Metrics tracked in `content/metrics/`

## 📚 Knowledge Base

### Krishna's Knowledge Base (`kb_krishna/`)
- AI/ML topics: RAG systems, LangChain, ML pipelines
- Data Engineering: PySpark, Databricks, ETL/ELT patterns

### Tejuu's Knowledge Base (`kb_tejuu/`)
- Analytics Engineering: dbt, data modeling, cloud platforms
- Business Intelligence: Power BI, Tableau, stakeholder management

## 🧪 Testing

Run the Phase 2 test suite:
```bash
export API_URL="http://localhost:8000"
python tests/phase2_runner.py
```

## 📖 Documentation

All documentation is organized in the `docs/` folder:
- Deployment guides
- Feature documentation
- Quality reports
- Interview preparation guides

## 🔄 Development Workflow

1. **Add Knowledge Base Content**
   - Add markdown files to appropriate `kb_*/` directory
   - Run `python scripts/generate_embeddings.py` to update embeddings

2. **Update Templates**
   - Modify templates in `core/templates/fragments/`
   - Update template registry as needed

3. **Test Changes**
   - Use `tests/phase2_runner.py` for comprehensive testing
   - Test both local and production deployments

## 🚀 Deployment

### Local Development
- Use `server.py` for full-stack development
- Frontend runs on port 3000, backend on port 8000

### Production
- **Render**: Uses `render_app.py` with `config/render.yaml`
- **Vercel**: Frontend-only with `config/vercel.json`
- **Heroku**: Uses `config/Procfile`

## 📝 License

MIT License - see LICENSE file for details
