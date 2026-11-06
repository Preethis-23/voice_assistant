import webbrowser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from app.tools.base import register_tool, ToolResult
from app.core.logging import logger

@register_tool(
    name="search_web",
    description="Searches the live web using DuckDuckGo (free, real-time news, documentation, courses, articles).",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query keywords"},
            "max_results": {"type": "integer", "description": "Number of results to return (default: 5)"}
        },
        "required": ["query"]
    }
)
def search_web(query: str, max_results: int = 5) -> ToolResult:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })

        if results:
            return ToolResult(
                tool_name="search_web",
                success=True,
                output={"query": query, "count": len(results), "results": results}
            )
        
        # Fallback to Wikipedia if DuckDuckGo returns empty (rate limited)
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&utf8=&format=json&srlimit={max_results}"
        headers = {"User-Agent": "KiraAssistant/1.0"}
        wiki_resp = requests.get(wiki_url, headers=headers, timeout=5)
        if wiki_resp.status_code == 200:
            wiki_data = wiki_resp.json()
            for item in wiki_data.get("query", {}).get("search", []):
                # Clean HTML tags from Wikipedia snippet
                soup = BeautifulSoup(item.get("snippet", ""), "html.parser")
                clean_snippet = soup.get_text()
                results.append({
                    "title": item.get("title", ""),
                    "snippet": clean_snippet,
                    "url": f"https://en.wikipedia.org/wiki/{item.get('title', '').replace(' ', '_')}"
                })
                
        if results:
            return ToolResult(
                tool_name="search_web",
                success=True,
                output={"query": query, "count": len(results), "results": results, "source": "wikipedia_fallback"}
            )
        else:
            return ToolResult(
                tool_name="search_web",
                success=False,
                output=None,
                error=f"No results found for query '{query}' on DDG or Wikipedia.",
                recoverable=True
            )
    except Exception as e:
        logger.error(f"search_web error: {e}")
        return ToolResult(tool_name="search_web", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="open_url",
    description="Opens a URL directly in the user's default desktop web browser (e.g. YouTube, GitHub, documentation).",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL to open (e.g., 'https://youtube.com')"}
        },
        "required": ["url"]
    }
)
def open_url(url: str) -> ToolResult:
    try:
        target_url = url.strip()
        if not target_url.startswith(("http://", "https://")):
            target_url = "https://" + target_url

        webbrowser.open(target_url)
        return ToolResult(
            tool_name="open_url",
            success=True,
            output=f"Opened URL '{target_url}' in browser."
        )
    except Exception as e:
        return ToolResult(tool_name="open_url", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="open_url_in_edge",
    description="Opens any URL directly in Microsoft Edge browser. Use this to open YouTube searches, Google searches, or any specific webpage in Edge.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL including https:// (e.g. https://youtube.com/results?search_query=ted+talks)"}
        },
        "required": ["url"]
    }
)
def open_url_in_edge(url: str) -> ToolResult:
    try:
        target_url = url.strip()
        if not target_url.startswith(("http://", "https://")):
            target_url = "https://" + target_url
        import subprocess
        subprocess.Popen(f'start msedge "{target_url}"', shell=True)
        return ToolResult(
            tool_name="open_url_in_edge",
            success=True,
            output=f"Opened '{target_url}' in Microsoft Edge."
        )
    except Exception as e:
        return ToolResult(tool_name="open_url_in_edge", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="search_and_open_youtube",
    description="Searches YouTube for a query and opens the results page directly in Edge browser. Use this when user says 'play X on youtube' or 'open youtube and search X'.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for on YouTube (e.g. 'ted talks 2024', 'lofi music', 'python tutorial')"}
        },
        "required": ["query"]
    }
)
def search_and_open_youtube(query: str) -> ToolResult:
    try:
        import subprocess
        import urllib.parse
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        subprocess.Popen(f'start msedge "{url}"', shell=True)
        return ToolResult(
            tool_name="search_and_open_youtube",
            success=True,
            output=f"Opened YouTube search for '{query}' in Edge."
        )
    except Exception as e:
        return ToolResult(tool_name="search_and_open_youtube", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="fetch_page_content",
    description="Fetches and extracts readable text from a webpage URL to analyze or summarize its contents.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL of the webpage to scrape and read"},
            "max_characters": {"type": "integer", "description": "Max text length to extract (default: 3000)"}
        },
        "required": ["url"]
    }
)
def fetch_page_content(url: str, max_characters: int = 3000) -> ToolResult:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove script and style tags
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        text = " ".join(soup.stripped_strings)
        truncated_text = text[:max_characters]

        return ToolResult(
            tool_name="fetch_page_content",
            success=True,
            output={"title": soup.title.string if soup.title else "", "content": truncated_text, "url": url}
        )
    except Exception as e:
        return ToolResult(tool_name="fetch_page_content", success=False, output=None, error=str(e), recoverable=True)
