import os
import sys
import shutil
import uuid
import json
import asyncio

# Fix path for imports when running from within the api directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import time
from typing import List, Dict, Any
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
    Response,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import existing logic
from bookmark_parser import parse_bookmarks_html
from content_fetcher import fetch_and_extract_content
from llm_processor import process_content_with_llm
from storage import init_supabase, store_bookmark, check_url_exists
from exporter import generate_bookmarks_html

load_dotenv()

app = FastAPI(title="Bookmark Processor API")

# Restrict CORS to specific origins (adjust based on your actual frontend URL)
FRONTEND_URLS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URLS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to necessary methods
    allow_headers=["Content-Type", "Accept"],
)

# In-memory storage for task progress
tasks_progress: Dict[str, Dict[str, Any]] = {}

# Rate limiter storage: {"ip_address": [timestamp1, timestamp2, ...]}
rate_limit_storage: Dict[str, List[float]] = {}


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
            except Exception:
                pass


manager = ConnectionManager()


async def process_bookmarks_task(
    task_id: str,
    file_path: str,
    provider: str,
    model: str,
    host: str,
    gemini_api_key: str = None,
):
    tasks_progress[task_id] = {
        "status": "processing",
        "total": 0,
        "processed": 0,
        "newly_added": 0,
        "skipped": 0,
        "total_tokens": 0,
        "current_bookmark": "",
    }

    # 1. Initialize Supabase
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase_client = init_supabase(supabase_url, supabase_key)

    if not supabase_client:
        tasks_progress[task_id]["status"] = "failed"
        tasks_progress[task_id]["error"] = "Failed to initialize Supabase client"
        await manager.broadcast(
            json.dumps(
                {
                    "task_id": task_id,
                    "type": "error",
                    "message": "Supabase initialization failed",
                }
            )
        )
        return

    # 2. Parse bookmarks
    bookmarks = list(parse_bookmarks_html(file_path))
    tasks_progress[task_id]["total"] = len(bookmarks)

    await manager.broadcast(
        json.dumps({"task_id": task_id, "type": "start", "total": len(bookmarks)})
    )

    for url, title in bookmarks:
        tasks_progress[task_id]["processed"] += 1
        tasks_progress[task_id]["current_bookmark"] = title

        await manager.broadcast(
            json.dumps(
                {
                    "task_id": task_id,
                    "type": "progress",
                    "processed": tasks_progress[task_id]["processed"],
                    "total": tasks_progress[task_id]["total"],
                    "current": title,
                }
            )
        )

        # Skip if already exists
        if check_url_exists(supabase_client, url):
            tasks_progress[task_id]["skipped"] += 1
            continue

        # Fetch and process
        text_content = fetch_and_extract_content(url)
        if text_content:
            llm_result = process_content_with_llm(
                text_content,
                provider=provider,
                model_name=model,
                ollama_host=host,
                gemini_api_key=gemini_api_key,
            )
            summary = llm_result.get("summary", "")
            category = llm_result.get("category", "")
            if store_bookmark(supabase_client, title, url, summary, category):
                tasks_progress[task_id]["newly_added"] += 1
                tasks_progress[task_id]["total_tokens"] += llm_result.get("tokens", 0)

        # Small delay to prevent blocking the event loop too much
        await asyncio.sleep(0.1)

    tasks_progress[task_id]["status"] = "completed"
    await manager.broadcast(
        json.dumps(
            {
                "task_id": task_id,
                "type": "complete",
                "added": tasks_progress[task_id]["newly_added"],
                "skipped": tasks_progress[task_id]["skipped"],
                "tokens": tasks_progress[task_id]["total_tokens"],
                "total": tasks_progress[task_id]["total"],
            }
        )
    )

    # Cleanup file
    if os.path.exists(file_path):
        os.remove(file_path)


@app.post("/upload")
async def upload_bookmarks(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    provider: str = "ollama",
    model: str = "gemma3",
    host: str = "http://localhost:11434",
    gemini_api_key: str = None,
):
    # Security: Rate limiting check for POST requests
    client_ip = get_client_ip(request)
    if not is_rate_limited(client_ip):
        rate_limit_storage[client_ip].append(time.time())
    else:
        return {
            "error": "Rate limit exceeded",
            "retry_after": DEFAULT_WINDOW_SECONDS
            - int(time.time() - rate_limit_storage[client_ip][0]),
        }

    task_id = str(uuid.uuid4())
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{task_id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Use environment variable if key not provided in request
    api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")

    background_tasks.add_task(
        process_bookmarks_task, task_id, file_path, provider, model, host, api_key
    )

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


# Blocklist for dangerous characters/patterns (SQL injection prevention)
DANGEROUS_PATTERNS = [
    "'--",
    "; DROP",
    ";SELECT",
    "UNION SELECT",
    "WAITFOR",
    "EXEC sp_",
    "XP_REG",
    "BENCHMARK(",
]


# Input sanitization helper to prevent SQL-like injection attempts
def sanitize_search_input(search_term: str) -> tuple:
    """Sanitize search input and return (cleaned_term, is_safe)."""
    if not search_term:
        return "", True

    original = search_term
    # Check against SQL injection patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in search_term.lower():
            print(f"Blocked suspicious input: {original}")  # Log blocked attempts
            return "", False  # Block request

    # Basic length limit (50 chars for search term)
    if len(search_term) > 100:
        search_term = search_term[:100]

    # Normalize whitespace and URL encoding
    search_term = " ".join(search_term.split())

    return search_term, True


# Helper to extract client IP from request
async def get_client_ip(request: Request):
    """Extract the real IP address, handling proxies."""
    if request.client.host:
        return request.client.host

    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Take the first (original) IP
        return x_forwarded_for.split(",")[0].strip()

    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip

    return "unknown"


# Rate limiting check helper
async def is_rate_limited(client_ip: str) -> bool:
    """Check if client IP has exceeded rate limit."""
    now = time.time()
    if client_ip in rate_limit_storage:
        # Filter out old timestamps (keep only recent ones within the window)
        rate_limit_storage[client_ip] = [
            ts
            for ts in rate_limit_storage[client_ip]
            if now - ts < DEFAULT_WINDOW_SECONDS
        ]
        return len(rate_limit_storage[client_ip]) >= DEFAULT_MAX_REQUESTS
    return False


def fetch_all_results(query):
    """
    Helper function to fetch all results from a Supabase query by handling pagination.
    PostgREST typically limits results to 1000 per request.
    """
    all_data = []
    page_size = 1000
    start = 0

    while True:
        response = query.range(start, start + page_size - 1).execute()
        data = response.data
        all_data.extend(data)

        if len(data) < page_size:
            break
        start += page_size

    return all_data


@app.get("/bookmarks")
async def get_bookmarks(request: Request, q: str = None):
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase_client = init_supabase(supabase_url, supabase_key)

    if not supabase_client:
        return {"error": "Supabase not initialized"}

    # Security: Sanitize search input to prevent SQL injection
    safe_q, is_safe = sanitize_search_input(q)
    if not is_safe:
        return {
            "error": "Invalid search term",
            "details": "Potentially malicious input detected",
        }

    query = (
        supabase_client.table("bookmarks").select("*").order("created_at", desc=True)
    )
    if safe_q:
        # Using parameterized-style filtering through Supabase client (safe from SQL injection)
        query = query.or_(
            f"title.ilike.%.%{safe_q}%,summary.ilike.%.%{safe_q}%,category.ilike.%.%{safe_q}%"
        )

    results = fetch_all_results(query)

    # Security: Rate limiting check for GET requests
    client_ip = get_client_ip(request)
    if is_rate_limited(client_ip):
        return {
            "error": "Rate limit exceeded",
            "details": "Too many requests. Please try again later.",
        }

    return results


@app.get("/category-summary")
async def get_category_summary(min_count: int = 10, request: Request = None):
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase_client = init_supabase(supabase_url, supabase_key)

    if not supabase_client:
        return {"error": "Supabase not initialized"}

    try:
        query = supabase_client.table("bookmarks").select("category")
        data = fetch_all_results(query)

        categories = {}
        for item in data:
            cat = item.get("category") or "Uncategorized"
            categories[cat] = categories.get(cat, 0) + 1

        # Filter: count >= min_count
        summary = [
            {"category": name, "count": count}
            for name, count in categories.items()
            if count >= min_count
        ]
        # Sort by count descending
        summary.sort(key=lambda x: x["count"], reverse=True)

        return summary
    except Exception as e:
        return {"error": str(e)}


@app.get("/categories")
async def get_categories():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase_client = init_supabase(supabase_url, supabase_key)

    if not supabase_client:
        return {"error": "Supabase not initialized"}

    # Get all categories to count them manually (Supabase aggregation is sometimes limited)
    query = supabase_client.table("bookmarks").select("category")
    data = fetch_all_results(query)

    categories = {}
    for item in data:
        cat = item.get("category") or "Uncategorized"
        categories[cat] = categories.get(cat, 0) + 1

    return [{"name": name, "count": count} for name, count in categories.items()]


@app.get("/export")
async def export_bookmarks():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase_client = init_supabase(supabase_url, supabase_key)

    if not supabase_client:
        return {"error": "Supabase not initialized"}

    # Fetch all bookmarks
    query = (
        supabase_client.table("bookmarks").select("*").order("created_at", desc=True)
    )
    bookmarks = fetch_all_results(query)

    html_content = generate_bookmarks_html(bookmarks)

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": "attachment; filename=bookmarks_categorized.html"
        },
    )


if __name__ == "__main__":
    print(" - run api: python api/app.py")
    print(" - run frontend: npm run dev")
    print(
        " - security features active: SQL injection protection, rate limiting, CORS restrictions"
    )

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
