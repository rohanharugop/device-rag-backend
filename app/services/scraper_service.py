import httpx
from bs4 import BeautifulSoup
import asyncio
import re
from typing import List


class ScraperService:

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; DeviceBot/1.0)"
        }

        self.timeout = httpx.Timeout(10.0)

        print("✅ ScraperService initialized")

    # -------------------------------
    # FETCH HTML (ASYNC)
    # -------------------------------
    async def fetch(self, client, url):
        try:
            print(f"🌐 Fetching: {url}")

            response = await client.get(url, headers=self.headers)
            response.raise_for_status()

            print(f"✅ Fetched: {url} ({len(response.text)} chars)")

            return response.text

        except Exception as e:
            print(f"❌ Failed to fetch {url}: {e}")
            return None

    # -------------------------------
    # CLEAN TEXT
    # -------------------------------
    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^a-zA-Z0-9\s.,:%()-]', '', text)
        return text.strip()

    # -------------------------------
    # GENERIC PARSER
    # -------------------------------
    def parse_generic(self, html):
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ")

        return self.clean_text(text)

    # -------------------------------
    # DOMAIN-SPECIFIC PARSERS
    # -------------------------------
    def parse_gsmarena(self, html):
        soup = BeautifulSoup(html, "html.parser")

        specs = soup.select(".specs-list")

        text = " ".join(s.get_text(" ", strip=True) for s in specs)

        return self.clean_text(text)

    def parse_ifixit(self, html):
        soup = BeautifulSoup(html, "html.parser")

        steps = soup.select(".step")

        text = " ".join(s.get_text(" ", strip=True) for s in steps)

        return self.clean_text(text)

    def parse_apple(self, html):
        soup = BeautifulSoup(html, "html.parser")

        sections = soup.select("section")

        text = " ".join(s.get_text(" ", strip=True) for s in sections)

        return self.clean_text(text)

    # -------------------------------
    # ROUTER
    # -------------------------------
    def parse(self, url, html):

        print(f"🧠 Parsing URL: {url}")

        if "gsmarena" in url:
            return self.parse_gsmarena(html)

        elif "ifixit" in url:
            return self.parse_ifixit(html)

        elif "apple.com" in url:
            return self.parse_apple(html)

        else:
            return self.parse_generic(html)

    # -------------------------------
    # CONTENT VALIDATION (NEW)
    # -------------------------------
    def is_valid_content(self, text):

        if not text or len(text) < 200:
            return False

        # ONLY block hard junk
        if "login" in text.lower() or "sign up" in text.lower():
            return False

        return True

    # -------------------------------
    # MAIN RUN (ASYNC PIPELINE)
    # -------------------------------
    async def scrape_all(self, urls: List[dict]):

        print("\n🚀 SCRAPING PIPELINE STARTED\n")

        async with httpx.AsyncClient(timeout=self.timeout) as client:

            tasks = [
                self.fetch(client, u["link"])
                for u in urls
            ]

            html_pages = await asyncio.gather(*tasks)

        results = []
        seen_urls = set()

        for i, html in enumerate(html_pages):

            if not html:
                continue

            url = urls[i]["link"]
            if "youtube" in url:
                print("❌ Skipping YouTube")
                continue

            # 🔁 Deduplicate
            if url in seen_urls:
                continue
            seen_urls.add(url)

            parsed = self.parse(url, html)

            print("\n📄 PARSED CONTENT PREVIEW:")
            print(parsed[:200], "\n")

            # ✅ Validation
            if not self.is_valid_content(parsed):
                continue

            results.append({
                "url": url,
                "content": parsed
            })

        print(f"\n📦 FINAL SCRAPED PAGES: {len(results)}")

        return results

    # -------------------------------
    # SYNC WRAPPER (for FastAPI)
    # -------------------------------
    def run(self, urls: List[dict]):

        results = asyncio.run(self.scrape_all(urls))

        # 🚨 NEW: fallback signal
        if not results:
            print("⚠️ No usable content scraped")

        return results