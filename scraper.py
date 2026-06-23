import requests
from bs4 import BeautifulSoup
from chunk import chunk_text
from config import URLS

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def clean_soup(soup: BeautifulSoup):
    """
    Remove unwanted elements.
    """

    remove_tags = [
        "script",
        "style",
        "noscript",
        "svg",
        "iframe",
        "footer",
        "nav",
        "form",
    ]

    for tag in soup(remove_tags):
        tag.decompose()

    return soup


def extract_main_content(soup: BeautifulSoup):
    """
    Try to find the main content area first.
    """

    selectors = [
        "main",
        "article",
        "[role='main']",
        ".content",
        ".main-content",
        "#content",
        "#main",
    ]

    for selector in selectors:
        element = soup.select_one(selector)

        if element:
            return element.get_text("\n", strip=True)

    return soup.get_text("\n", strip=True)


def extract_text_from_url(url: str) -> str:
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        soup = clean_soup(soup)

        text = extract_main_content(soup)

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        return "\n".join(lines)

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""


def scrape_entire_site():
    all_chunks = []

    for url in URLS:
        print(f"Scraping: {url}")

        content = extract_text_from_url(url)

        if not content:
            continue

        chunks = chunk_text(content)

        for idx, chunk in enumerate(chunks):
            all_chunks.append({
                "source": url,
                "chunk_id": idx,
                "chunk": chunk
            })

    return all_chunks