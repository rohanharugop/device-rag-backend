import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError("TAVILY_API_KEY not found in .env")

client = TavilyClient(api_key=api_key)


def web_search(query, max_results=3):
    print(f"\n🌐 [TOOL] Searching: {query}\n")

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results
    )

    # Clean results (important)
    cleaned = []
    for r in response.get("results", []):
        cleaned.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "summary": r.get("content")
        })

    return cleaned