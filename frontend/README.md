# RAG AI Chat - Modern React Frontend

A modern, responsive React frontend for the RAG AI Chatbot with multi-profile support.

## Features

- 🎨 **Modern UI/UX**: Built with React, TypeScript, and TailwindCSS
- 📱 **Fully Responsive**: Mobile-first design that works on all devices
- 👥 **Multi-Profile Support**: Switch between Krishna (Data Engineer/ML) and Tejuu (Business Analyst/BI)
- 🌙 **Dark/Light Mode**: Toggle between themes
- 💬 **Real-time Chat**: Smooth messaging experience with typing indicators
- 🎯 **Smart Modes**: Auto-detect question types or manually select modes
- 💾 **Persistent Chat**: Chat history saved locally and persists across sessions
- 🚀 **Fast & Optimized**: Built for performance with code splitting

## Tech Stack

- **React 19** with TypeScript
- **TailwindCSS** for styling
- **Lucide React** for icons
- **React Markdown** for message rendering
- **Axios** for API calls

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=https://rag-chatbot-api-33r9.onrender.com
```

## Project Structure

```
frontend/
├── public/
├── src/
│   ├── App.tsx          # Main application component
│   ├── App.css          # Custom styles
│   ├── index.css        # TailwindCSS imports
│   └── index.tsx        # App entry point
├── tailwind.config.js   # TailwindCSS configuration
├── postcss.config.js    # PostCSS configuration
├── vercel.json          # Vercel deployment config
└── package.json
```

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Set the build command: `npm run build`
3. Set the output directory: `build`
4. Add environment variable: `REACT_APP_API_URL`

### Manual Build

```bash
npm run build
# Upload the build/ folder to your hosting provider
```

## Features Overview

### Profile System
- **Krishna**: Data Engineer & ML specialist with PySpark, Databricks, AWS, Azure experience
- **Tejuu**: Business Analyst & BI developer with Power BI, Tableau, SQL, KPIs expertise

### Response Modes
- **🤖 Smart Mode**: Auto-detect question type (SQL, Code, Interview, General)
- **🎯 Interview Mode**: STAR pattern responses for behavioral questions
- **💾 SQL Mode**: Database queries and optimization
- **💻 Code Mode**: Programming and algorithms

### UI Components
- **Responsive Sidebar**: Profile and mode selection
- **Message Bubbles**: Different styles for user/assistant messages
- **Loading States**: Typing indicators and smooth animations
- **Dark Mode**: Toggle between light and dark themes

## API Integration

The frontend communicates with the backend API:

- **Endpoint**: `/api/chat`
- **Method**: POST
- **Payload**: `{ message, mode, profile }`
- **Response**: `{ answer, mode_used, auto_detected }`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details