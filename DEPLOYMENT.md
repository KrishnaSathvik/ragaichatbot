# Vercel Deployment Guide for RAG Chatbot

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Push your code to GitHub
3. **OpenAI API Key**: Get your API key from [platform.openai.com](https://platform.openai.com)

## Deployment Steps

### 1. Push to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit for Vercel deployment"
git remote add origin https://github.com/yourusername/rag-chatbot.git
git push -u origin main
```

### 2. Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "New Project"
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (leave default)
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty

### 3. Set Environment Variables

In your Vercel project dashboard:

1. Go to **Settings** → **Environment Variables**
2. Add the following variables:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Upload Knowledge Base Files

**Important**: You need to upload your knowledge base files (`kb_index.faiss` and `kb_metadata.json`) to the project root.

**Option A: Manual Upload via Vercel Dashboard**
1. Go to your project's file explorer
2. Upload `kb_index.faiss` and `kb_metadata.json` to the root directory

**Option B: Include in Git Repository**
```bash
# Make sure these files are committed
git add kb_index.faiss kb_metadata.json
git commit -m "Add knowledge base files"
git push
```

### 5. Deploy

1. Click **Deploy** in Vercel
2. Wait for deployment to complete
3. Your app will be available at `https://your-project-name.vercel.app`

### 6. Connect Custom Domain (ragaichatbot.com)

1. In your Vercel project dashboard, go to **Settings** → **Domains**
2. Click **Add Domain**
3. Enter `ragaichatbot.com`
4. Follow Vercel's DNS configuration instructions
5. Update your domain's DNS settings with the provided records
6. Wait for DNS propagation (usually 5-15 minutes)
7. Your app will be live at `https://ragaichatbot.com`

## File Structure for Vercel

```
rag-chatbot/
├── api/
│   ├── chat.py          # Chat endpoint
│   ├── transcribe.py    # Audio transcription endpoint
│   ├── health.py        # Health check endpoint
│   └── utils.py         # Shared utilities
├── frontend/
│   └── index.html       # Frontend application
├── kb_index.faiss       # FAISS vector index
├── kb_metadata.json     # Knowledge base metadata
├── vercel.json          # Vercel configuration
├── requirements.txt     # Python dependencies
├── package.json         # Node.js metadata
└── .vercelignore        # Files to ignore
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key for GPT and Whisper | Yes |

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/chat` - Chat with the AI
- `POST /api/transcribe` - Transcribe audio files

## Troubleshooting

### Common Issues

1. **Knowledge Base Not Loading**
   - Ensure `kb_index.faiss` and `kb_metadata.json` are in the root directory
   - Check file permissions and size limits

2. **API Timeout**
   - Vercel has a 30-second timeout for serverless functions
   - The current configuration should handle most requests within this limit

3. **CORS Issues**
   - CORS headers are configured in the API handlers
   - Ensure your frontend is served from the same domain

### Monitoring

- Check Vercel's function logs for debugging
- Monitor API usage and response times
- Set up alerts for function errors

## Local Development

To test locally before deploying:

```bash
# Install Vercel CLI
npm i -g vercel

# Run locally
vercel dev

# This will start the development server at http://localhost:3000
```

## Cost Considerations

- Vercel Pro plan recommended for production use
- Monitor OpenAI API usage costs
- Consider implementing rate limiting for heavy usage

## Security Notes

- Never commit API keys to your repository
- Use Vercel's environment variables for sensitive data
- Consider implementing authentication if needed
