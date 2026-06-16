import requests
from bs4 import BeautifulSoup
from config import URLS


def extract_text_from_url(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        return " ".join(text.split())
    
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
    
def scrape_entire_site() -> str:
    all_content = []

    for url in URLS:
        print(f"Scraping: {url}")
        content = extract_text_from_url(url)

        if content and "Error" not in content:
            all_content.append(f"\n\nSOURCE: {url}\n{content[:4000]}")
    return "\n".join(all_content)