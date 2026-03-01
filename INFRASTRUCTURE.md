# Technical Infrastructure Report: Favorite Bookmarks App

This document provides a detailed overview of the technical architecture, technology stack, and design philosophy used in the Favorite Bookmarks project.

## 1. System Architecture
The application follows a modern decoupled architecture consisting of a **FastAPI** backend and a **React** frontend, with real-time communication facilitated by **WebSockets**.

### Core Workflow:
1.  **Ingestion**: User uploads a Safari/Chrome/Edge bookmarks HTML file.
2.  **Parsing**: Python backend parses the HTML to extract URLs and Titles.
3.  **Processing**:
    -   **Fetching**: Backend retrieves the page content and extracts the main text using `readability-lxml`.
    -   **Enrichment**: A Large Language Model (local via Ollama or cloud via Google Gemini) summarizes the content and categorizes the bookmark.
4.  **Storage**: Metadata and summaries are stored in **Supabase**.
5.  **Visualization**: The React dashboard displays the enriched bookmarks with search, category filtering, and distribution charts.

---

## 2. Backend Infrastructure (Python)

### Core Technologies:
-   **FastAPI**: A high-performance web framework for building APIs with Python 3.10+.
-   **Uvicorn**: An ASGI server to handle asynchronous requests and WebSockets.
-   **Supabase**: Managed backend-as-a-service providing a PostgreSQL database and an easy-to-use client library for data persistence.
-   **Content Retrieval**:
    -   `requests`: For fetching web content.
    -   `beautifulsoup4`: For initial HTML parsing.
    -   `readability-lxml`: For cleaning and extracting meaningful text from web pages (stripping navs, ads, etc.).

### AI & LLM Integration:
-   **Ollama**: Used for local LLM inference (e.g., `gemma3`, `llama3`).
-   **Google Generative AI (Gemini)**: Integrated as a cloud-based alternative for summarization and classification.

---

## 3. Frontend Infrastructure (React)

### Core Technologies:
-   **React 19**: Utilizing the latest React features and modern Hook-based state management.
-   **Vite**: The build tool and development server for fast HMR and optimized production builds.
-   **Recharts**: A composable charting library used to visualize bookmark distribution across categories.
-   **Communication**:
    -   **Fetch API**: For standard RESTful operations (GET bookmarks, POST upload).
    -   **WebSockets**: For real-time processing updates (progress bars, current processing status).

### Design & Styling (Design System):
The frontend adheres to a "Premium Cyber-Dark" aesthetic with a custom CSS design system:
-   **Typography**: Inter (Google Fonts) with fallback to system-ui.
-   **Color Palette**:
    -   Primary: Indigo (`#6366f1`)
    -   Background: Slate/Navy (`#0f172a`)
    -   Success: Emerald (`#10b981`)
    -   Gradients: Linear text-clips (`#818cf8` to `#c084fc`) and radial background accents.
-   **Aesthetics**: Glassmorphism (blur filters), high-contrast borders, and subtle micro-animations (hover lifts, heartbeat pulses).

---

## 4. Key Files & Responsibilities
-   `main.py`: Entry point for FastAPI, defining endpoints and WebSocket logic.
-   `llm_processor.py`: Service layer for interacting with LLM providers.
-   `storage.py`: Handles Supabase operations.
-   `frontend/src/App.jsx`: Main React component managing tabs, forms, and the dashboard.
-   `frontend/src/index.css`: Global design tokens and component-level CSS.

---

## 5. Security & Environment
-   **Environment Variables**: Managed via `.env` (Supabase keys, API tokens).
-   **Security Wrapper**: `security.py` provides rate limiting and basic protection for API endpoints.
