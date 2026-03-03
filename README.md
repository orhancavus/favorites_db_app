# 🔖 Favorite Bookmarks App
### *Intelligent Bookmark Enrichment & Discovery*

Transform your static browser bookmarks into a dynamic, AI-powered knowledge base. Import Safari/Chrome/Edge bookmarks, fetch page contents, and generate intelligent summaries and categories using Local LLMs (Ollama) or Google Gemini.

---

## 🖼️ Screenshots

<div align="center">
  <h3>Upload & Real-Time Processing</h3>
  <img src="media/bp_upload.png" alt="Upload View" width="800">
  <br><br>
  <h3>Premium Dashboard & Search</h3>
  <img src="media/bp_dashboard.png" alt="Dashboard View" width="800">
</div>

---

## ✨ Features

- **🚀 Real-Time Ingestion**: Upload `bookmarks.html` and watch the processing in real-time via WebSockets.
- **🧠 Hybrid AI Processing**: 
  - **Local**: Private, local inference using **Ollama** (`gemma3`, `llama3`).
  - **Cloud**: High-performance processing via **Google Gemini**.
- **🔍 Deep Content Extraction**: Uses `readability-lxml` to strip ads and navigation, focusing purely on the article content.
- **📊 Interactive Dashboard**: 
  - Search by title, URL, or AI-generated summary.
  - Category-based filtering with dynamic result counts.
  - Visual distribution of your bookmarks.
- **💎 Premium Design**: Sleek "Cyber-Dark" aesthetic featuring glassmorphism, Inter typography, and smooth micro-animations.
- **🔋 Persistent Storage**: Metadata, summaries, and categories stored securely in **Supabase**.

---

## 🛠️ Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Frontend**: [React 19](https://react.dev/) + [Vite](https://vitejs.dev/)
- **AI/LLM**: [Ollama](https://ollama.com/) & [Google Gemini](https://ai.google.dev/)
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
- **Styling**: Vanilla CSS (Custom Design System)

---

## 📖 Quick Start

### 1. Configure Environment
Create a `.env` file in the root directory:
```env
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
GEMINI_API_KEY=your_gemini_key (optional)
```

### 2. Start Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python3 api/app.py
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit **http://localhost:5173** to start processing.

---

## 🔗 Project Structure

- `api/app.py`: FastAPI backend and WebSocket hub.
- `frontend/`: Modern React dashboard and upload interface.
- `llm_processor.py`: Intelligent layer for Ollama/Gemini integration.
- `content_fetcher.py`: Content extraction logic using `readability-lxml`.
- `storage.py`: Data persistence layer for Supabase.
- `main.py`: Original CLI core logic.

---
