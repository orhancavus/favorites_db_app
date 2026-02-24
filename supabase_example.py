import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env
load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

def simple_example():
    # 1. Initialize the client
    supabase: Client = create_client(URL, KEY)
    print("--- 1. Client Initialized ---")

    # 2. Insert data (Create)
    # Using the 'bookmarks' table from your schema.sql
    new_bookmark = {
        "url": "https://example.com",
        "title": "Example Domain",
        "summary": "This is a placeholder for a domain used in illustrative examples.",
        "category": "Education"
    }
    
    print("\n--- 2. Inserting Data ---")
    try:
        response = supabase.table("bookmarks").insert(new_bookmark).execute()
        print(f"Inserted: {response.data}")
    except Exception as e:
        print(f"Insert failed (maybe unique URL violation?): {e}")

    # 3. Read data
    print("\n--- 3. Reading Data ---")
    response = supabase.table("bookmarks").select("*").limit(5).execute()
    for row in response.data:
        print(f"ID: {row['id']} | Title: {row['title']} | URL: {row['url']}")

    # 4. Update data
    print("\n--- 4. Updating Data ---")
    try:
        response = supabase.table("bookmarks").update({"category": "Reference"}).eq("url", "https://example.com").execute()
        print(f"Updated: {response.data}")
    except Exception as e:
        print(f"Update failed: {e}")

    # 5. Delete data
    # print("\n--- 5. Deleting Data ---")
    # response = supabase.table("bookmarks").delete().eq("url", "https://example.com").execute()
    # print(f"Deleted rows: {len(response.data)}")

if __name__ == "__main__":
    if not URL or not KEY:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    else:
        simple_example()
