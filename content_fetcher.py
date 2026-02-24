import requests
from readability import Document

def fetch_and_extract_content(url, timeout=10):
    """
    Fetches the HTML of a URL and extracts the main text content 
    using readability-lxml to remove boilerplate.
    """
    try:
        # User-Agent to help prevent basic blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Check if content type is textual (ignore pdfs, images, etc)
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and 'text/plain' not in content_type:
             return None

        # Use readability to extract the main article content
        doc = Document(response.text)
        main_html = doc.summary() 
        
        # Readability returns HTML containing the main content block. 
        # We need to strip the HTML tags out to purely text for the LLM
        # using a quick beautifulsoup parse:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(main_html, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        
        return text_content
        
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
