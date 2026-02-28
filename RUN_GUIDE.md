# How to Run the Application

Follow these steps to get the Bookmark Processor and Dashboard up and running.

## Prerequisites
- **Ollama**: Ensure Ollama is running (`ollama serve`).
- **Supabase**: Ensure your `.env` file has the correct `SUPABASE_URL` and `SUPABASE_KEY`.

## 1. Start the Backend (API)
The backend handles LLM processing and database communication.

```bash
# From the project root
python3 api/app.py
```
*The API will be available at http://localhost:8000*

## 2. Start the Frontend (UI)
The frontend provides the modern web interface.

```bash
# Open a new terminal tab/window
cd frontend
npm install  # Only needed the first time
npm run dev
```
*The Web App will be available at http://localhost:5173*

## 3. Usage
1. Open [http://localhost:5173](http://localhost:5173) in your browser.
2. **Upload Tab**: Drag and drop your `bookmarks.html` and click "Start Analysis".
3. **Dashboard Tab**: Search through your saved bookmarks, filter by category, and click any card to expand details or open the link.
