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
