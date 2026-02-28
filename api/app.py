import os
import sys
import shutil
import uuid
import json
import asyncio

# The starting page address for the web application is:
# http://localhost:5173

# Fix path for imports when running from within the api directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import existing logic
from bookmark_parser import parse_bookmarks_html
from content_fetcher import fetch_and_extract_content
from llm_processor import process_content_with_llm
from storage import init_supabase, store_bookmark, check_url_exists

load_dotenv()

app = FastAPI(title="Bookmark Processor API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for task progress
tasks_progress: Dict[str, Dict[str, Any]] = {}

# WebSocket manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

async def process_bookmarks_task(task_id: str, file_path: str, model: str, host: str):
    tasks_progress[task_id] = {"status": "processing", "total": 0, "processed": 0, "current_bookmark": ""}
    
    # 1. Initialize Supabase
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase_client = init_supabase(supabase_url, supabase_key)
    
    if not supabase_client:
        tasks_progress[task_id]["status"] = "failed"
        tasks_progress[task_id]["error"] = "Failed to initialize Supabase client"
        await manager.broadcast(json.dumps({"task_id": task_id, "type": "error", "message": "Supabase initialization failed"}))
        return

    # 2. Parse bookmarks
    bookmarks = list(parse_bookmarks_html(file_path))
    tasks_progress[task_id]["total"] = len(bookmarks)
    
    await manager.broadcast(json.dumps({"task_id": task_id, "type": "start", "total": len(bookmarks)}))

    for url, title in bookmarks:
        tasks_progress[task_id]["processed"] += 1
        tasks_progress[task_id]["current_bookmark"] = title
        
        await manager.broadcast(json.dumps({
            "task_id": task_id, 
            "type": "progress", 
            "processed": tasks_progress[task_id]["processed"],
            "total": tasks_progress[task_id]["total"],
            "current": title
        }))

        # Skip if already exists
        if check_url_exists(supabase_client, url):
            continue

        # Fetch and process
        text_content = fetch_and_extract_content(url)
        if text_content:
            llm_result = process_content_with_llm(text_content, model_name=model, ollama_host=host)
            summary = llm_result.get("summary", "")
            category = llm_result.get("category", "")
            
            store_bookmark(supabase_client, title, url, summary, category)
        
        # Small delay to prevent blocking the event loop too much
        await asyncio.sleep(0.1)

    tasks_progress[task_id]["status"] = "completed"
    await manager.broadcast(json.dumps({"task_id": task_id, "type": "complete"}))
    
    # Cleanup file
    if os.path.exists(file_path):
        os.remove(file_path)

@app.post("/upload")
async def upload_bookmarks(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: str = "gemma3",
    host: str = "http://localhost:11434"
):
    task_id = str(uuid.uuid4())
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{task_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(process_bookmarks_task, task_id, file_path, model, host)
    
    return {"task_id": task_id, "message": "Processing started"}

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    return tasks_progress.get(task_id, {"status": "not_found"})

@app.get("/bookmarks")
async def get_bookmarks(q: str = None):
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase_client = init_supabase(supabase_url, supabase_key)
    
    if not supabase_client:
        return {"error": "Supabase not initialized"}
        
    query = supabase_client.table("bookmarks").select("*")
    if q:
        # Simple text search on title, summary, or category
        query = query.or_(f"title.ilike.%{q}%,summary.ilike.%{q}%,category.ilike.%{q}%")
    
    response = query.order("created_at", desc=True).execute()
    return response.data

@app.get("/categories")
async def get_categories():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase_client = init_supabase(supabase_url, supabase_key)
    
    if not supabase_client:
        return {"error": "Supabase not initialized"}
        
    # Get all categories to count them manually (Supabase aggregation is sometimes limited)
    response = supabase_client.table("bookmarks").select("category").execute()
    
    categories = {}
    for item in response.data:
        cat = item.get("category") or "Uncategorized"
        categories[cat] = categories.get(cat, 0) + 1
        
    return [{"name": name, "count": count} for name, count in categories.items()]

if __name__ == "__main__":
    print(" - run api: python api/app.py")
    print(" - run frontend: npm run dev")
    print(" - run security layer active: python security.py")

    print("Visit **http://localhost:5173** to start.") 
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
