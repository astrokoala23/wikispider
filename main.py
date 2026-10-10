import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time

# Access all Wikipedia article links
def fetch_links(soup):
    # Get body content, not the whole page (footers, headers etc. are irrelevant)
    main_content = soup.find(id='bodyContent')
    if not main_content:
        print("Couldn't locate main body content!")
        return None

    # Get all links, then filter for articles
    # Set rather than list to avoid duplicates
    links = set()
    for link in main_content.find_all('a'):
        href = link.get('href')

        # Quick pass filter
        if href and \
            ('/wiki/' in href) and \
            (':' not in href.split('/wiki/')[-1]) and \
            ('#' not in href) and \
            ('?' not in href) and \
            ('identifier' not in href):

            url = urljoin("https://en.wikipedia.org", href)
            parsed_url = urlparse(url)

            if parsed_url.netloc == "en.wikipedia.org":
                links.add(url)

    return links

# Get HTML content
def access(url):
    # Add a User-Agent header so my bot doesn't get caught (copied it from https://www.zenrows.com/blog/user-agent-web-scraping)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    # Was the respons successful (code 200)?
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        print(f"Couldn't fetch the page! Your status code is: {response.status_code}")
        return None

    return soup

# Recontstruct path
def backtrack(parents, end):
    path = []
    current = end

    # While we haven't hit our root node
    while current is not None:
        path.append(current)
        current = parents[current]

    return path[::-1] # Reverse path

# BFS crawl
def crawl(start, end, max_depth=3):
    # Queue and visited set for BFS
    queue = [(start, 0)]
    visited = set()

    # Parent tracking for path reconstruction
    # The start node has on parents (it is the root)
    parents = {start: None}

    while queue:
        current, depth = queue.pop(0)

        if current == end:
            print(f"End located: {current}")
            return backtrack(parents, end)

        if depth >= max_depth:
            continue
        else:
            print(f"Depth: {depth}, Current: {current}, Queue length: {len(queue)}")

        neighbours = set(fetch_links(access(current)))

        for neighbour in neighbours:
            if neighbour not in visited:
                visited.add(neighbour)
                parents[neighbour] = current # Record connection
                queue.append((neighbour, depth + 1))

    print("Start and end are not connected!")

    
url = "https://en.wikipedia.org/wiki/Alphabet"
soup = access(url)
trail = crawl(url, "https://en.wikipedia.org/wiki/Tibetan_script")
print(f"Trail: {trail}")
