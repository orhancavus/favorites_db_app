from bs4 import BeautifulSoup

def parse_safari_bookmarks(file_path):
    """
    Parses a Safari bookmarks HTML file and yields tuples of (url, title).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # Safari bookmarks export uses <DT><A HREF="url">Title</A> format usually
        # But grabbing all 'a' tags with an 'href' is the most robust way
        links = soup.find_all('a')
        
        for link in links:
            url = link.get('href')
            title = link.text.strip()
            
            if url and url.startswith('http'):
                yield (url, title)
                
    except Exception as e:
        print(f"Error parsing bookmarks file: {e}")
