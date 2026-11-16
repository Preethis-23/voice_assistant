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

import os
import subprocess
import urllib.parse

BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def open_in_target_browser(url: str, browser: Optional[str] = None) -> str:
    """Launches URL in requested browser (Brave, Chrome, Edge) or default system browser."""
    b = (browser or "").lower().strip()
    target_url = url.strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    if "brave" in b:
        if os.path.exists(BRAVE_PATH):
            subprocess.Popen([BRAVE_PATH, target_url])
            return "Brave Browser"
        else:
            subprocess.Popen(f'start brave "{target_url}"', shell=True)
            return "Brave Browser"
    elif "chrome" in b:
        if os.path.exists(CHROME_PATH):
            subprocess.Popen([CHROME_PATH, target_url])
            return "Google Chrome"
        else:
            subprocess.Popen(f'start chrome "{target_url}"', shell=True)
            return "Google Chrome"
    elif "edge" in b:
        subprocess.Popen(f'start msedge "{target_url}"', shell=True)
        return "Microsoft Edge"
    else:
        # Default system browser
        webbrowser.open(target_url)
        return "Default Browser"

@register_tool(
    name="open_url",
    description="Opens any URL in the user's web browser. Can target specific browsers like 'brave', 'chrome', or 'edge'.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL to open (e.g. 'https://youtube.com')"},
            "browser": {"type": "string", "description": "Target browser: 'brave', 'chrome', 'edge', or 'default' (default: 'default')"}
        },
        "required": ["url"]
    }
)
def open_url(url: str, browser: Optional[str] = None) -> ToolResult:
    try:
        browser_used = open_in_target_browser(url, browser)
        return ToolResult(
            tool_name="open_url",
            success=True,
            output=f"Opened '{url}' in {browser_used}."
        )
    except Exception as e:
        return ToolResult(tool_name="open_url", success=False, output=None, error=str(e), recoverable=True)

@register_tool(
    name="open_url_in_edge",
    description="Opens any URL directly in Microsoft Edge browser.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL including https://"}
        },
        "required": ["url"]
    }
)
def open_url_in_edge(url: str) -> ToolResult:
    return open_url(url, browser="edge")

@register_tool(
    name="search_and_open_youtube",
    description="Searches YouTube for a song or video and opens it. Supports specific browsers (e.g. 'brave' for automatic ad-blocking, 'edge', 'chrome').",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Song, artist, or video title to search and play"},
            "browser": {"type": "string", "description": "Target browser: 'brave' (recommended for ad-blocking), 'edge', or 'chrome'"}
        },
        "required": ["query"]
    }
)
def search_and_open_youtube(query: str, browser: Optional[str] = None) -> ToolResult:
    try:
        encoded = urllib.parse.quote_plus(query)
        # Filter for direct video results
        url = f"https://www.youtube.com/results?search_query={encoded}"
        target_browser = browser or ("brave" if os.path.exists(BRAVE_PATH) else "edge")
        browser_used = open_in_target_browser(url, target_browser)
        return ToolResult(
            tool_name="search_and_open_youtube",
            success=True,
            output=f"Opened YouTube search for '{query}' in {browser_used}. (Ad-blocking active via Brave Shields if Brave is used)."
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
