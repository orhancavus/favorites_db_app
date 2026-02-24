# Bookmark Processor & AI Summarizer

A modern web application to process Safari bookmarks, generate AI summaries using local LLMs (Ollama), and store them in a Supabase database.

## 🚀 Features
- **File Upload**: Upload `bookmarks.html` directly via a web interface.
- **Local AI**: Uses local LLMs (default: `gemma3`) via Ollama for privacy and speed.
- **Real-time Dashboard**: Track processing progress with a live progress bar.
- **Supabase Integration**: Automatically stores title, URL, summary, and category.
- **Modern UI**: Sleek glassmorphism design built with React and Vanilla CSS.

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite (JS)
- **AI**: Ollama (Local)
- **Database**: Supabase (PostgreSQL)

## 📖 Quick Start

### 1. Configure Environment
Ensure `.env` in the root has your credentials:
```env
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

### 2. Start Backend
```bash
python3 api/app.py
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit **http://localhost:5173** to start.

## 🔗 Project Structure
- `api/app.py`: FastAPI backend implementation.
- `frontend/`: React application.
- `main.py`: Original CLI tool implementation.
- `*.py`: Supporting logic for parsing, fetching, and LLM processing.
