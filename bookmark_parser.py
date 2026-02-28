from bs4 import BeautifulSoup

def parse_bookmarks_html(file_path):
    """
    Parses a browser bookmarks HTML file (Safari, Edge, Chrome, etc.)
    and yields tuples of (url, title).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # Most browser bookmark exports use <DT><A HREF="url">Title</A> format
        # Grabbing all 'a' tags with an 'href' is the most robust way across browsers
        links = soup.find_all('a')
        
        for link in links:
            url = link.get('href')
            title = link.text.strip()
            
            if url and url.startswith('http'):
                yield (url, title)
                
    except Exception as e:
        print(f"Error parsing bookmarks file: {e}")
