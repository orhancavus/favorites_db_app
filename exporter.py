import time

def generate_bookmarks_html(bookmarks):
    """
    Generates a Netscape Bookmark File format (HTML) string.
    Groups bookmarks by their categories into folders.
    """
    # Group bookmarks by category
    categories = {}
    for b in bookmarks:
        cat = b.get('category') or "Uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(b)

    # HTML Header
    lines = [
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
        '<!-- This is an automatically generated file.',
        '     It will be read and classified by LLM. -->',
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        '<TITLE>Bookmarks</TITLE>',
        '<H1>Bookmarks</H1>',
        '<DL><p>'
    ]

    timestamp = int(time.time())

    # Build category folders
    for cat, items in categories.items():
        lines.append(f'    <DT><H3 ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}">{cat}</H3>')
        lines.append('    <DL><p>')
        
        for item in items:
            title = item.get('title') or "Untitled"
            url = item.get('url', "")
            add_date = timestamp # We could use item.created_at if we parse it to epoch
            lines.append(f'        <DT><A HREF="{url}" ADD_DATE="{add_date}">{title}</A>')
            
        lines.append('    </DL><p>')

    lines.append('</DL><p>')
    
    return '\n'.join(lines)
