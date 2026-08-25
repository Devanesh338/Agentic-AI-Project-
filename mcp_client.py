import os
import sys
import traceback
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
WEATHER_SERVER = os.path.join(PROJECT_DIR, "custom_weather_mcp_server.py")
AVIATIONSTACK_DIR = r"C:\\Users\\daksh\\OneDrive\\Desktop\\aviationstack-mcp"

# ── Server configs ─────────────────────────────────────────────────────────────
ALL_SERVERS = {
    "tavily": {
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={os.getenv('TAVILY_API_KEY')}",
        "transport": "streamable_http",
    },
    "aviationstack": {
        "command": "uv",
        "args": ["run", "aviationstack-mcp"],
        "cwd": AVIATIONSTACK_DIR,
        "transport": "stdio",
        "env": {
            "AVIATIONSTACK_API_KEY": os.getenv("AVIATIONSTACK_API_KEY", ""),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
        },
    },
    "weather": {
        "command": sys.executable,  # venv python — guarantees mcp/FastMCP is available
        "args": [WEATHER_SERVER],
        "transport": "stdio",
        "env": {
            "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY", ""),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
        },
    },
}


# ── Helper: parse MCP content-block responses into plain text ──────────────────
def _extract_text(result) -> str:
    """MCP tool.ainvoke() returns a list of content blocks or a plain string."""
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        parts = []
        for block in result:
            if isinstance(block, dict):
                parts.append(block.get("text", str(block)))
            else:
                text = getattr(block, "text", None) or getattr(block, "content", str(block))
                parts.append(str(text))
        return "\n".join(parts)
    return getattr(result, "content", str(result))


# ── Helper: strip markdown control characters from scraped webpage text ────────
def _sanitize_markdown(text: str) -> str:
    """Tavily's `content` field is often raw scraped-page markdown (headings,
    image alt-text placeholders, table pipes). Strip that out so it renders
    as plain text instead of hijacking Streamlit's markdown layout."""
    import re

    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)           # markdown images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # markdown links -> plain text
    text = re.sub(r"Image\s*\d+", "", text)                # leftover image alt-text placeholders
    text = re.sub(r"#{1,6}\s*", "", text)                   # heading markers
    text = re.sub(r"\|", " ", text)                         # table pipes
    text = re.sub(r"\*{1,3}|_{1,3}|`", "", text)             # bold/italic/code markers
    text = re.sub(r"\s+", " ", text).strip()                 # collapse whitespace
    return text


# ── Helper: format Tavily's raw JSON into clean, markdown-safe text ────────────
def _format_tavily_results(raw: str) -> str:
    """Parse Tavily's JSON search response into clean bullet points.
    Prevents Streamlit's markdown auto-linker from mangling bare URLs
    that sit next to quotes/brackets in the raw JSON, and strips scraped
    markdown syntax (headings, tables, image placeholders) from content."""
    import json

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw  # not JSON — return as-is

    results = data.get("results", [])
    if not results:
        return "No hotel results found."

    lines = []
    for r in results:
        title = _sanitize_markdown(r.get("title") or "Untitled")
        url = r.get("url", "")
        content = _sanitize_markdown(r.get("content") or "")
        if len(content) > 220:
            content = content[:220].rsplit(" ", 1)[0] + "..."
        lines.append(f"- **{title}**\n  {content}\n  🔗 {url}")

    return "\n\n".join(lines)


# ── Helper: invoke a named tool on a named server ─────────────────────────────
# Correct API (langchain-mcp-adapters >= 0.1.0):
#   client = MultiServerMCPClient(...)
#   async with client.session(server_name) as session:
#       tools = await load_mcp_tools(session)
async def _call_tool(server_name: str, tool_name: str, args: dict) -> str:
    client = MultiServerMCPClient(ALL_SERVERS)
    async with client.session(server_name) as session:
        tools = await load_mcp_tools(session)
        tool = next((t for t in tools if t.name == tool_name), None)
        if tool is None:
            available = [t.name for t in tools]
            return f"Tool '{tool_name}' not found on '{server_name}'. Available: {available}"
        return _extract_text(await tool.ainvoke(args))


# ── Public wrappers ────────────────────────────────────────────────────────────

async def tavily_mcp_search(query: str) -> str:
    """Search the web via Tavily MCP."""
    try:
        client = MultiServerMCPClient(ALL_SERVERS)
        async with client.session("tavily") as session:
            tools = await load_mcp_tools(session)
            # Tavily tool is named "tavily_search" or similar
            tool = next((t for t in tools if "search" in t.name.lower()), None)
            if tool is None:
                return f"Tavily search tool not found. Available: {[t.name for t in tools]}"
            raw = _extract_text(await tool.ainvoke({"query": query}))
            return _format_tavily_results(raw)
    except Exception:
        traceback.print_exc()
        return "Tavily search failed — see server logs for full traceback."


async def get_airports() -> str:
    """List airports via AviationStack MCP."""
    try:
        return await _call_tool("aviationstack", "list_airports", {})
    except Exception:
        traceback.print_exc()
        return "Airport lookup failed — see server logs for full traceback."


async def get_airlines() -> str:
    """List airlines via AviationStack MCP."""
    try:
        return await _call_tool("aviationstack", "list_airlines", {})
    except Exception:
        traceback.print_exc()
        return "Airline lookup failed — see server logs for full traceback."


async def weather_mcp_search(city: str) -> str:
    """Get current weather for a city via Weather MCP."""
    try:
        return await _call_tool("weather", "get_current_weather", {"city": city})
    except Exception:
        traceback.print_exc()
        return f"Weather lookup failed for '{city}' — see server logs for full traceback."


async def forecast_mcp_search(city: str) -> str:
    """Get 5-day forecast for a city via Weather MCP."""
    try:
        return await _call_tool("weather", "get_forecast", {"city": city})
    except Exception:
        traceback.print_exc()
        return f"Forecast lookup failed for '{city}' — see server logs for full traceback."