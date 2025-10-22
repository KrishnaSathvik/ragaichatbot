# RAG Chatbot - Advanced Interview Preparation Assistant

A sophisticated dual-persona RAG (Retrieval-Augmented Generation) chatbot designed for comprehensive interview preparation, featuring two professional profiles with specialized expertise in AI/ML/Data Engineering and Business Intelligence/Analytics Engineering. Built with modern React frontend and FastAPI backend, optimized for mobile responsiveness and production deployment.

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
├── kb_profile_a/                # Profile A knowledge base
│   ├── ai_ml/                   # AI/ML content
│   └── data_engineering/        # Data Engineering content
├── kb_profile_b/                # Profile B knowledge base
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

### 🧠 Dual Persona System
- **Profile A**: AI/ML Engineer & Data Engineer with 6+ years experience
  - **AI/ML Mode**: LangChain, LangGraph, RAG systems, MLOps, FastAPI
  - **Data Engineering Mode**: PySpark, Databricks, Azure Data Factory, ETL/ELT
- **Profile B**: Business Intelligence Developer & Analytics Engineer with 6+ years experience
  - **Business Intelligence Mode**: Power BI, Tableau, DAX, stakeholder management
  - **Analytics Engineering Mode**: dbt, data modeling, Azure/AWS cloud platforms

### 🎯 Intelligent Question Routing
- **Auto-detection**: Automatically identifies question type and domain
- **Smart Modes**: 4 specialized modes (Code, SQL, Interview, General)
- **Profile Selection**: Manual or automatic profile/mode selection
- **Generic Profiles**: Two professional profiles (A & B) with distinct expertise areas
- **Context Awareness**: Routes based on technical keywords and question patterns

### 🚀 Advanced RAG System
- **Vector Search**: High-performance semantic search with scikit-learn
- **Knowledge Base**: 557+ curated chunks across 4 specialized domains
- **Source Citations**: Transparent source tracking and references
- **Quality Filtering**: Profile-specific content filtering and ranking

### 💬 Interview-Optimized Responses
- **Structured Format**: APPROACH → CODE → EXPLANATION → PRO TIP format
- **STAR Method**: Situation, Task, Action, Result for behavioral questions
- **Humanized Output**: Natural, conversational tone with contractions
- **Performance Metrics**: Real project numbers and quantifiable results

### 🎤 Audio & Voice Features
- **Voice Recording**: Real-time audio capture with MediaRecorder API
- **Whisper Integration**: OpenAI Whisper-1 for accurate transcription
- **Auto-Send**: Transcribed text automatically sent to chat
- **Mobile Optimized**: Touch-friendly recording controls

### 📱 Mobile-First Design
- **Fully Responsive**: Optimized for all screen sizes (320px - 1920px+)
- **Touch-Friendly**: 44px minimum touch targets
- **Safe Area Support**: iPhone X+ notch and dynamic island support
- **Progressive Web App**: Installable on mobile devices

### 🎨 Modern UI/UX
- **React 19 + TypeScript**: Latest React with full type safety
- **TailwindCSS**: Utility-first styling with dark/light themes
- **Framer Motion**: Smooth animations and transitions
- **Real-time Chat**: Instant message display with typing indicators

### 💾 Advanced Chat Management
- **Persistent History**: Local storage with conversation management
- **Delete Chats**: Individual chat deletion with confirmation
- **Conversation Export**: Copy messages and code snippets
- **Session Management**: Profile-specific conversation contexts

### ⚡ Performance Optimizations
- **Fast Responses**: 5-6 second average response time (gpt-4o-mini)
- **Caching**: LRU cache for embeddings and API responses
- **Code Splitting**: Optimized bundle sizes for faster loading
- **Streaming**: Real-time response generation (prepared)

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI API access
- `RETRIEVAL_TOPK`: Number of top results to retrieve (default: 6)
- `USE_LLM`: Enable/disable LLM generation (default: false)

### Profile Configuration
- Profiles defined in `content/profiles/`
- Metrics tracked in `content/metrics/`

## 📚 Knowledge Base

### Profile A Knowledge Base (`kb_profile_a/`)
- **AI/ML Content** (109 chunks): LangChain, LangGraph, RAG systems, MLOps, FastAPI, MLflow
- **Data Engineering Content** (219 chunks): PySpark, Databricks, Azure Data Factory, ETL/ELT patterns, Delta Lake, streaming data

### Profile B Knowledge Base (`kb_profile_b/`)
- **Analytics Engineering Content** (122 chunks): dbt, data modeling, star schemas, Azure/AWS platforms
- **Business Intelligence Content** (107 chunks): Power BI, Tableau, DAX, stakeholder management, KPI frameworks

### Content Quality
- **557+ Total Chunks**: Comprehensive coverage across all domains
- **Real Project Examples**: Based on actual work experience across healthcare, retail, and financial sectors
- **Interview-Ready**: Structured for technical and behavioral interview preparation
- **Performance Metrics**: Includes quantifiable results and project outcomes

## 🧪 Testing & Quality Assurance

### Comprehensive Test Suite
```bash
# Run Phase 2 test suite
export API_URL="http://localhost:8000"
python tests/phase2_runner.py

# Run quality assessment
python scripts/quality_assessment.py

# Performance testing
python scripts/performance_test.py
```

### Quality Metrics
- **100% Success Rate**: All 20 test questions pass quality standards
- **93% Excellence Rate**: 74/80 quality criteria met across all modes
- **Zero Generic Intros**: No repetitive "I'm a [role] with X years..." responses
- **Technical Depth**: Specific tools, technologies, and implementations
- **Real Metrics**: Quantifiable project outcomes and performance improvements

### Test Coverage
- **Profile A AI Mode**: 8/8 questions (100% excellent)
- **Profile A DE Mode**: 4/4 questions (100% pass)
- **Profile B BI Mode**: 4/4 questions (100% pass)
- **Profile B AE Mode**: 4/4 questions (100% pass)

## 📖 Documentation

Comprehensive documentation organized in the `docs/` folder:

### 🚀 Deployment & Setup
- `DEPLOYMENT_SUCCESS.md` - Complete deployment guide
- `RENDER_DEPLOYMENT.md` - Render platform deployment
- `HYBRID_DEPLOYMENT.md` - Frontend/backend separation
- `PRODUCTION_CHECKLIST.md` - Production readiness checklist

### 🎯 Feature Documentation
- `INTERVIEW_MODE_FEATURES.md` - Interview-optimized answer format
- `MOBILE_RESPONSIVENESS_GUIDE.md` - Mobile optimization guide
- `INTERVIEW_PREPARATION_GUIDE.md` - Comprehensive interview prep
- `LATEST_IMPROVEMENTS.md` - Recent feature updates

### 📊 Quality & Testing
- `ALL_MODES_QUALITY_REPORT.md` - Complete quality assessment
- `FINAL_QUALITY_REPORT.md` - Final quality metrics
- `COMPLETE_SUCCESS_SUMMARY.md` - Success metrics and achievements

### 🔧 Technical Guides
- `KNOWLEDGE_BASE_SUMMARY.md` - Knowledge base organization
- `PROFILE_FIX.md` - Profile system fixes and improvements
- `CLEANUP_SUMMARY.md` - Code cleanup and optimization

## 🔄 Development Workflow

### 📝 Adding Knowledge Base Content
1. **Add Content**: Add markdown files to appropriate `kb_profile_a/` or `kb_profile_b/` directory
2. **Generate Embeddings**: Run `python scripts/generate_embeddings_complete.py`
3. **Test Quality**: Run `python scripts/quality_assessment.py`
4. **Deploy**: Commit and push changes for automatic deployment

### 🎨 Updating Templates & Prompts
1. **Modify Templates**: Edit templates in `core/templates/fragments/`
2. **Update Prompts**: Modify prompt templates in `api/utils.py`
3. **Test Responses**: Use quality assessment to verify improvements
4. **Deploy Changes**: Push to trigger automatic deployment

### 🧪 Testing & Quality Assurance
1. **Local Testing**: Run `python tests/phase2_runner.py`
2. **Quality Assessment**: Execute `python scripts/quality_assessment.py`
3. **Performance Testing**: Run `python scripts/performance_test.py`
4. **Production Testing**: Test deployed endpoints and frontend

### 🚀 Deployment Process
1. **Automatic Deployment**: Changes auto-deploy to Render (backend) and Vercel (frontend)
2. **Manual Deployment**: Use `vercel --prod` for frontend, Render dashboard for backend
3. **Health Checks**: Verify endpoints with `curl` commands
4. **Monitoring**: Check logs in Render dashboard and Vercel analytics

## 🚀 Deployment

### 🌐 Production URLs
- **Frontend (Vercel)**: `https://ragaichatbot-dznt1l2mm-shadowdevils-projects-ae938de8.vercel.app`
- **Backend (Render)**: `https://rag-chatbot-api-33r9.onrender.com`

### 🏠 Local Development
```bash
# Backend (FastAPI)
python server.py
# Runs on http://localhost:8000

# Frontend (React)
cd frontend
npm start
# Runs on http://localhost:3000
```

### ☁️ Production Deployment
- **Backend (Render)**: Automatic deployment from main branch
  - Uses `render_app.py` with `config/render.yaml`
  - Python 3.13.4 runtime
  - Auto-scaling and health monitoring
- **Frontend (Vercel)**: Automatic deployment from main branch
  - Uses `config/vercel.json` configuration
  - Global CDN distribution
  - Automatic HTTPS and custom domains

### 🔧 Environment Configuration
- **Required**: `OPENAI_API_KEY` environment variable
- **Optional**: `RETRIEVAL_TOPK`, `USE_LLM`, `BYPASS_HTTP_PROXY_FOR_OPENAI`
- **Frontend**: `REACT_APP_API_URL` for backend connection

## 🔌 API Endpoints

### Chat Endpoint
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Your question here",
  "mode": "auto|de|ai|bi|ae",
  "profile": "auto|profile_a|profile_b",
  "session_id": "default"
}
```

### Health Check
```bash
GET /api/health
# Returns: {"ok": true, "embeddings": true, "error": null}
```

### Audio Transcription
```bash
POST /api/transcribe
Content-Type: application/json

{
  "audio_data": "base64_encoded_audio"
}
```

## 🆕 Recent Improvements

### ✨ Latest Features (2024)
- **Delete Chat Functionality**: Individual chat deletion with confirmation dialogs
- **Audio Transcription**: Voice-to-text using OpenAI Whisper API
- **Performance Optimization**: 50% faster responses (gpt-4o-mini)
- **Mobile Responsiveness**: Complete mobile optimization for all screen sizes
- **Interview Mode**: Structured APPROACH → CODE → EXPLANATION → PRO TIP format
- **Enhanced Knowledge Base**: 557+ curated chunks with real project examples

### 🚀 Performance Improvements
- **Response Time**: Reduced from 10-15s to 5-6s average
- **Model Optimization**: Switched to gpt-4o-mini for speed and cost efficiency
- **Caching**: LRU cache for embeddings and API responses
- **Mobile Performance**: Optimized for mobile networks and touch interactions

### 🎯 Quality Enhancements
- **Zero Generic Intros**: Eliminated repetitive "I'm a [role] with X years..." responses
- **Technical Depth**: Specific tools, technologies, and real project metrics
- **Humanized Output**: Natural, conversational tone with contractions
- **Source Citations**: Transparent source tracking and references

## 📝 License

MIT License - see LICENSE file for details
