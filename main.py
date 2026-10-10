from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import asyncio
import httpx
from collections import deque

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
# Updated access function with retry logic for 429 Too Many Requests
async def access(client, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.get(url, headers=headers, timeout=10, follow_redirects=True)
            
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'lxml')
            elif response.status_code == 429:
                # Rate limited! Back off exponentially before retrying
                wait_time = (2 ** attempt) + 1  # Pause before retry
                print(f"Rate limited (429) on {url}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"Couldn't fetch the page! Status code: {response.status_code}")
                break
        except Exception as error:
            print(f"Something went wrong for {url}: {error}")
            break
            
    return None

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
async def crawl(start, end, max_depth=100):
    visited = {start}
    parents = {start: None}
    
    # Store current frontier as a list of (url, depth)
    current_level = [(start, 0)]

    # Limit concurrent requests so Wikipedia doesn't block your User-Agent
    semaphore = asyncio.Semaphore(4)

    async with httpx.AsyncClient() as client:
        while current_level:
            next_level = []

            # Define a worker to fetch a single page asynchronously
            async def fetch_and_extract(url, depth):
                if url == end:
                    return url, None
                
                async with semaphore:
                    soup = await access(client, url)
                
                if not soup:
                    return url, None
                
                links = fetch_links(soup)
                return url, links

            # Fire off requests for the entire current level simultaneously
            print(f"Processing level with {len(current_level)} concurrent requests...")
            results = await asyncio.gather(*(fetch_and_extract(url, depth) for url, depth in current_level))

            for current, children in results:
                if current == end:
                    print(f"End located: {current}")
                    return backtrack(parents, end)

                if not children:
                    continue

                # Find the depth of the current node from our tracking
                current_depth = next((d for u, d in current_level if u == current), 0)

                if current_depth >= max_depth:
                    continue

                for child in children:
                    if child not in visited:
                        visited.add(child)
                        parents[child] = current
                        
                        if child == end:
                            print(f"End located: {child}")
                            return backtrack(parents, end)
                        
                        next_level.append((child, current_depth + 1))

            current_level = next_level

    print("Start and end are not connected!")
    return None


async def main():
    url = "https://en.wikipedia.org/wiki/Alphabet"
    trail = await crawl(url, "https://en.wikipedia.org/wiki/Zebra")
    print(f"Trail: {trail}")


asyncio.run(main())
