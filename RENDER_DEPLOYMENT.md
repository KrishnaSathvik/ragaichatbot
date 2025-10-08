# Render Deployment Guide

## 🚀 Deploy to Render

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Connect your GitHub repository

### Step 2: Deploy Web Service
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Use these settings:
   - **Name**: `rag-chatbot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python render_app.py`
   - **Plan**: Free

### Step 3: Set Environment Variables
In the Render dashboard, add these environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `PYTHON_VERSION`: `3.12.0`

### Step 4: Deploy
Click "Create Web Service" and wait for deployment.

### Step 5: Update Frontend
Once deployed, update the frontend's API URL to point to your Render service URL.

## 🔧 Files Created for Render
- `render_app.py` - FastAPI application
- `render.yaml` - Render configuration
- `requirements.txt` - Updated with FastAPI dependencies

## ✅ What Works
- ✅ Health endpoint: `GET /api/health`
- ✅ Chat endpoint: `POST /api/chat`
- ✅ Frontend serving: `GET /`
- ✅ CORS enabled for frontend
- ✅ FAISS integration working

## 🎯 Next Steps
1. Deploy to Render
2. Set environment variables
3. Test the deployed API
4. Update frontend API URL
5. Test end-to-end functionality
