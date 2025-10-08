# 🚀 Hybrid Deployment: Vercel Frontend + Render Backend

## 📋 **Deployment Steps**

### 🎨 **Step 1: Deploy Frontend to Vercel**
```bash
# From your project directory
vercel --prod
```
- ✅ Frontend deployed to Vercel
- ✅ Gets a URL like: `https://ragaichatbot.vercel.app`

### ⚙️ **Step 2: Deploy Backend to Render**
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Connect your repository
4. Create new **Web Service**:
   - **Name**: `rag-chatbot-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python render_app.py`
   - **Plan**: Free
5. Add environment variable: `OPENAI_API_KEY`
6. Deploy!

### 🔗 **Step 3: Connect Frontend to Backend**
1. Get your Render URL (e.g., `https://rag-chatbot-api.onrender.com`)
2. Update `index.html` line 362:
   ```javascript
   : "https://your-actual-render-url.onrender.com";
   ```
3. Redeploy frontend to Vercel:
   ```bash
   vercel --prod
   ```

## 🎯 **Final Architecture**
```
User → Vercel Frontend → Render Backend → OpenAI API
```

## ✅ **Benefits**
- ✅ **Vercel**: Fast static hosting, CDN, custom domains
- ✅ **Render**: Reliable Python runtime, persistent server
- ✅ **Separation**: Frontend and backend can scale independently
- ✅ **Cost**: Both free tiers available

## 🔧 **Files Structure**
```
├── index.html          → Vercel (Frontend)
├── render_app.py       → Render (Backend)
├── api/               → Render (Backend)
├── requirements.txt   → Render (Backend)
└── vercel.json       → Vercel (Frontend)
```

## 🚀 **Ready to Deploy!**
Both platforms are configured and ready for deployment!
