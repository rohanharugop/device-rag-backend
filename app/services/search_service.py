import os
from serpapi import GoogleSearch


class SearchService:

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        print("✅ SearchService initialized")

    # -------------------------------
    # PRIMARY (CURATED QUERIES)
    # -------------------------------
    def primary_search(self, device_name):

        queries = [
            f"{device_name} gsmarena specifications",
            f"{device_name} official specs",
            f"{device_name} internal components",
            f"{device_name} teardown ifixit",
            f"{device_name} sensors list smartphone"
        ]

        urls = []

        for q in queries:
            urls.extend(self.run_serp(q))

        print(f"🔍 Primary search URLs: {len(urls)}")

        return urls

    # -------------------------------
    # FALLBACK (LIVE SEARCH)
    # -------------------------------
    def fallback_search(self, device_name):

        print("⚡ FALLBACK SEARCH TRIGGERED")

        queries = [
            f"{device_name} specs",
            f"{device_name} hardware details",
            f"{device_name} chipset battery camera"
        ]

        urls = []

        for q in queries:
            urls.extend(self.run_serp(q))

        print(f"🌐 Fallback URLs: {len(urls)}")

        return urls

    # -------------------------------
    # SERP API CALL
    # -------------------------------
    def run_serp(self, query):

        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        links = []

        for r in results.get("organic_results", [])[:5]:
            links.append({
                "title": r.get("title"),
                "link": r.get("link"),
                "snippet": r.get("snippet")
            })

        return links

    # -------------------------------
    # MAIN ENTRY
    # -------------------------------
    def run(self, device_name):

        urls = self.primary_search(device_name)

        if not urls:
            urls = self.fallback_search(device_name)

        return urls