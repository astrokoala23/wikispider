import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def access(url):
    # Add a User-Agent header so my bot doesn't get caught (copied it from https://www.zenrows.com/blog/user-agent-web-scraping)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    # Was the respons successful (code 200)?
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        print(f"Couldn't fetch the page! Your status code is: {response.status_code}")
        return None

url = "https://www.wikipedia.org/wiki/United_Arab_Emirates"
soup = access(url)

print(soup)
