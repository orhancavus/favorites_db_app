from supabase import create_client, Client
import os

def init_supabase(url, key):
    """Initialize the Supabase client."""
    if not url or not key:
        return None
    try:
        supabase: Client = create_client(url, key)
        return supabase
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        return None

def check_url_exists(supabase: Client, url):
    """
    Checks if a URL already exists in the bookmarks table.
    """
    if not supabase:
        return False
    try:
        response = supabase.table('bookmarks').select('url').eq('url', url).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking if URL exists: {e}")
        return False

def store_bookmark(supabase: Client, title, url, summary, category):
    """
    Upserts the bookmark data into the Supabase database.
    """
    if not supabase:
        print("Warning: Supabase client not initialized. Skipping DB insert.")
        return False
        
    try:
        # Use upsert to avoid Unique violation on URL if the script is run multiple times
        data, count = supabase.table('bookmarks').upsert({
            'title': title,
            'url': url,
            'summary': summary,
            'category': category
        }, on_conflict='url').execute()
        
        return True
    except Exception as e:
        print(f"Failed to store bookmark {url}: {e}")
        return False
