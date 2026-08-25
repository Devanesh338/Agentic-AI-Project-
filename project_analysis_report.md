# 📊 Project Analysis Report — Multi-Agent Travel Booking System with MCP

**Generated:** 2026-07-07  
**Project:** `Multi_Agent_System_With_Mcp`

---

## 🏗️ Project Overview

You've built a **Multi-Agent AI Travel Booking System** powered by **LangGraph**, **Groq LLM (LLaMA 3.3 70B)**, and **MCP (Model Context Protocol)** servers. The system takes a user's travel query and orchestrates multiple specialized AI agents in a pipeline to produce a complete travel plan — including flights, hotels, weather, and a final itinerary.

---

## 📁 Project Structure

```
Multi_Agent_System_With_Mcp/
├── main.py              ← LangGraph agent pipeline + CLI entry point
├── mcp_client.py        ← MCP client connecting to 3 external servers
├── frontend.py          ← Streamlit UI (dark-themed, premium design)
├── tools/
│   ├── __init__.py      ← Package marker
│   ├── flight_tool.py   ← Legacy direct AviationStack REST client (now replaced by MCP)
│   └── tavily_tool.py   ← Legacy direct Tavily REST client (now replaced by MCP)
└── venv/                ← Python virtual environment
```

---

## 📄 File-by-File Analysis

### 1. [main.py](file:///c:/Users/daksh/OneDrive/Desktop/Multi_Agent_System_With_Mcp/main.py) — Core Agent Pipeline

| Aspect | Details |
|--------|---------|
| **Lines** | 297 |
| **Role** | Defines the LangGraph state machine with 4 agents |
| **LLM** | Groq — `llama-3.3-70b-versatile` |
| **Persistence** | PostgreSQL via `PostgresSaver` (long-term memory / checkpointing) |

**State Schema (`TravelState`):**
- `messages` — Conversation message history (accumulates via `operator.add`)
- `user_query` — The raw travel request
- `flight_results` — Output from the flight agent
- `hotel_results` — Output from the hotel agent
- `weather_results` — Output from the weather agent
- `itinerary` — Final generated itinerary
- `llm_calls` — Counter tracking total LLM invocations

**Agent Pipeline (Sequential):**

```mermaid
graph LR
    START --> flight_agent --> hotel_agent --> weather_agent --> itinerary_agent --> END
```

| Agent | What It Does |
|-------|-------------|
| **Flight Agent** | Calls `list_airports` + `list_airlines` via AviationStack MCP, then asks the LLM to generate flight recommendations using a structured prompt |
| **Hotel Agent** | Searches `"Best hotels for {query}"` via Tavily MCP |
| **Weather Agent** | Extracts destination city (via LLM), then fetches current weather + forecast via custom Weather MCP |
| **Itinerary Agent** | Combines all prior results + user query and asks the LLM to create a complete travel itinerary |

> [!NOTE]
> The old `search_flights()` (direct API) and `tavily_search()` (direct SDK) are commented out — you've fully migrated to MCP-based tool calling.

---

### 2. [mcp_client.py](file:///c:/Users/daksh/OneDrive/Desktop/Multi_Agent_System_With_Mcp/mcp_client.py) — MCP Client Layer

| Aspect | Details |
|--------|---------|
| **Lines** | 278 |
| **Role** | Connects to 3 MCP servers and exposes async wrapper functions |
| **Library** | `langchain_mcp_adapters.client.MultiServerMCPClient` |

**MCP Servers Connected:**

| Server | Transport | Purpose |
|--------|-----------|---------|
| **Tavily** | `streamable_http` (remote) | Web search for hotels & general travel info |
| **AviationStack** | `stdio` (local subprocess) | Airport/airline data via `aviationstack_mcp` |
| **Weather** | `stdio` (local subprocess) | Custom weather MCP server (`custom_weather_mcp_server.py`) |

**Exported Functions:**

| Function | Description |
|----------|-------------|
| `tavily_mcp_search(query)` | Searches the web via Tavily MCP |
| `aviation_mcp_call(tool_name, tool_args)` | Generic caller for any AviationStack tool |
| `get_airports()` | Fetches airport list |
| `get_airlines()` | Fetches airline list |
| `weather_mcp_search(city)` | Gets current weather for a city |
| `forecast_mcp_search(city)` | Gets weather forecast for a city |
| `extract_destination(query)` | Uses Groq LLM to extract the destination city name from the user query |

> [!IMPORTANT]
> The MCP client initializes tools lazily — `initialize_mcp()` and `initialize_weather_tools()` are called once on first use, then cached globally.

---

### 3. [frontend.py](file:///c:/Users/daksh/OneDrive/Desktop/Multi_Agent_System_With_Mcp/frontend.py) — Streamlit Web UI

| Aspect | Details |
|--------|---------|
| **Lines** | 496 |
| **Role** | Premium dark-themed travel planning interface |
| **Framework** | Streamlit |

**UI Features Built:**

| Feature | Description |
|---------|-------------|
| 🎨 **Dark Theme** | Fully custom CSS — dark navy/slate palette (`#080d14`, `#0e1623`, etc.) with Inter font |
| 🖼️ **Hero Banner** | Full-width image with overlay text and badge |
| 🌍 **Destination Strip** | 5 clickable city cards (Tokyo, Paris, Bangkok, Rome, Dubai) with Unsplash images |
| ⚡ **Quick Prompts** | Pre-filled travel queries ("7-day Japan under ₹2L", "Paris trip for 5 days", etc.) |
| 📝 **Text Input** | Styled textarea for custom travel requests |
| 🚀 **Generate Button** | Gradient blue button with hover glow and lift animation |
| 🤖 **Live Pipeline** | Real-time `st.status` widgets showing each agent's output as it streams |
| 📊 **Metrics Row** | Shows agents run, LLM calls count, and status |
| 📄 **Final Plan Card** | Styled card displaying the complete travel plan |
| 💾 **Auto-Save** | Saves plans to `travel_plans/` as markdown files |
| ⬇️ **Download** | Download button for the generated plan |
| 🔧 **Sidebar** | User ID input, tech stack chips, agent pipeline steps |

---

### 4. [tools/flight_tool.py](file:///c:/Users/daksh/OneDrive/Desktop/Multi_Agent_System_With_Mcp/tools/flight_tool.py) — Legacy Flight Tool

| Aspect | Details |
|--------|---------|
| **Lines** | 62 |
| **Status** | ⚠️ **Legacy / Unused** — replaced by AviationStack MCP |

Direct REST API client that calls `api.aviationstack.com/v1/flights`. Returns airline, departure, arrival, and status for up to 5 flights. This was the **v1 approach** before migrating to MCP.

---

### 5. [tools/tavily_tool.py](file:///c:/Users/daksh/OneDrive/Desktop/Multi_Agent_System_With_Mcp/tools/tavily_tool.py) — Legacy Tavily Tool

| Aspect | Details |
|--------|---------|
| **Lines** | 47 |
| **Status** | ⚠️ **Legacy / Unused** — replaced by Tavily MCP |

Direct Tavily SDK client (`TavilyClient`) that searches with `max_results=5` and formats results as numbered markdown. This was the **v1 approach** before migrating to MCP.

---

## 🔄 Evolution / What You've Done

The project shows a clear **migration path from v1 → v2**:

### Phase 1 — Direct API Calls
- Built `flight_tool.py` (direct AviationStack REST)
- Built `tavily_tool.py` (direct Tavily SDK)
- Agents called these tools directly

### Phase 2 — MCP Migration
- Introduced `mcp_client.py` with `MultiServerMCPClient`
- Connected 3 MCP servers (Tavily, AviationStack, Weather)
- Replaced direct tool calls in agents with MCP-based async calls
- Commented out old imports in `main.py`

### Phase 3 — Weather Agent
- Added a **custom Weather MCP server** (external file: `custom_weather_mcp_server.py`)
- Built `weather_agent` using `get_current_weather` and `get_forecast` MCP tools
- Added `extract_destination()` to intelligently pull city names from queries via LLM
- Added `weather_results` to the state schema

### Phase 4 — Premium Frontend
- Built a full Streamlit UI (`frontend.py`) with ~300 lines of custom CSS
- Dark glassmorphism theme with Inter font
- Live streaming agent pipeline visualization
- Auto-save + download functionality
- Quick-fill destination suggestions

### Phase 5 — Long-Term Memory
- Added PostgreSQL checkpointing via `PostgresSaver`
- Each session gets a `thread_id` for conversation persistence
- CLI mode uses `uuid.uuid4()` for fresh sessions; Streamlit uses a user-configurable ID

---

## 🧰 Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Orchestration** | LangGraph (StateGraph) |
| **LLM** | Groq Cloud — LLaMA 3.3 70B Versatile |
| **Tool Protocol** | MCP (Model Context Protocol) via `langchain-mcp-adapters` |
| **Web Search** | Tavily MCP (remote, streamable HTTP) |
| **Flight Data** | AviationStack MCP (local stdio subprocess) |
| **Weather Data** | Custom OpenWeather MCP (local stdio subprocess) |
| **Persistence** | PostgreSQL + LangGraph `PostgresSaver` |
| **Frontend** | Streamlit (custom dark theme) |
| **Environment** | Python, dotenv, psycopg |

---

## 📈 Current State

| Metric | Value |
|--------|-------|
| Total source files | **5** (+ 1 external weather MCP server) |
| Total lines of code | **~1,180** |
| Active agents | **4** (Flight, Hotel, Weather, Itinerary) |
| MCP servers | **3** (Tavily, AviationStack, Weather) |
| Entry points | **2** (CLI via `main.py`, Web via `streamlit run frontend.py`) |
| Legacy files | **2** (`flight_tool.py`, `tavily_tool.py` — no longer imported) |

> [!TIP]
> The legacy `tools/flight_tool.py` and `tools/tavily_tool.py` are fully replaced by MCP and could be removed or archived to keep the codebase clean.
