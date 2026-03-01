import argparse
import os
from dotenv import load_dotenv

from bookmark_parser import parse_bookmarks_html
from content_fetcher import fetch_and_extract_content
from llm_processor import process_content_with_llm
from storage import init_supabase, store_bookmark, check_url_exists

def main():
    parser = argparse.ArgumentParser(description="Process Browser Bookmarks (Safari, Edge, Chrome), summarize and categorize using local LLM, and store in Supabase.")
    parser.add_argument("file_path", help="Path to the Bookmarks HTML file.")
    parser.add_argument("--model", default="gemma3", help="Name of the Ollama model to use (default: gemma3)")
    parser.add_argument("--host", default="http://localhost:11434", help="Ollama host URL (default: http://localhost:11434)")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "gemini"], help="LLM provider to use (default: ollama)")
    parser.add_argument("--gemini-api-key", help="Google Gemini API Key (can also be set via GEMINI_API_KEY env var)")
    parser.add_argument("--dry-run", action="store_true", help="Print results instead of saving to database.")
    
    args = parser.parse_args()
    
    # Load environment variables (Supabase credentials)
    load_dotenv()
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    supabase_client = None
    if not args.dry_run:
        supabase_client = init_supabase(supabase_url, supabase_key)
        if not supabase_client:
            print("Failed to initialize Supabase client. Running in dry-run mode.")
            args.dry_run = True

    print(f"Parsing bookmarks from {args.file_path}...")
    
    success_count = 0
    new_links_count = 0
    skipped_count = 0
    error_count = 0
    total_tokens = 0

    for url, title in parse_bookmarks_html(args.file_path):
        print(f"\nProcessing: {title} ({url})")
        
        # Check if already exists
        if not args.dry_run and check_url_exists(supabase_client, url):
            print(f"  - Skipping: URL already in database.")
            skipped_count += 1
            success_count += 1
            continue
            
        # 1. Fetch content
        print("  - Fetching content...")
        text_content = fetch_and_extract_content(url)
        
        if not text_content:
            print("  - Failed to extract meaningful text content. Skipping.")
            error_count += 1
            continue
            
        # 2. Process with LLM
        print(f"  - Summarizing with {args.provider}...")
        api_key = args.gemini_api_key or os.environ.get("GEMINI_API_KEY")
        
        llm_result = process_content_with_llm(
            text_content, 
            provider=args.provider, 
            model_name=args.model, 
            ollama_host=args.host,
            gemini_api_key=api_key
        )
        total_tokens += llm_result.get("tokens", 0)
        
        summary = llm_result.get("summary", "")
        category = llm_result.get("category", "")
        
        print(f"  - Category: {category}")
        print(f"  - Summary: {summary}")
        
        # 3. Store in Database
        if args.dry_run:
            print("  - Dry run enabled: Skipping database insert.")
            success_count += 1
        else:
            print("  - Saving to Database...")
            if store_bookmark(supabase_client, title, url, summary, category):
                print("  - Saved successfully.")
                new_links_count += 1
                success_count += 1
            else:
                print("  - Error saving to database.")
                error_count += 1
                
    print(f"\nDone! Processed {success_count} bookmarks.")
    print(f"  - Newly added: {new_links_count}")
    print(f"  - Skipped (already exists): {skipped_count}")
    print(f"  - Failed: {error_count}")
    print(f"  - Total Tokens Used: {total_tokens}")

if __name__ == "__main__":
    main()
