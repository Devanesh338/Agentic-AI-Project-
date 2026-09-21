# 📊 Project Analysis Report — Multi-Agent Travel Planning & Autonomous Booking System with MCP

**Generated:** 2026-09-18  
**Project:** `Multi_Agent_System_With_Mcp2`

---

## 🏗️ Project Overview

A **Multi-Agent AI Travel Planning & Autonomous Booking System** powered by **LangGraph**, **Groq LLM (LLaMA 3.3 70B)**, and **MCP (Model Context Protocol)** servers. The system takes a user's travel query, orchestrates multiple specialized AI agents to produce a complete travel plan (flights, hotels, weather, itinerary), and then utilizes an **Autonomous Booking Agent** to negotiate with providers and prepare a finalized booking checkout flow for the user.

---

## 📁 Project Structure

```
Multi_Agent_System_With_Mcp2/
├── main.py                     ← LangGraph agent pipeline + CLI entry point
├── frontend.py                 ← Streamlit UI (travel planner + booking trigger)
├── mcp_client.py               ← MCP client connecting to external tools
├── custom_weather_mcp_server.py← Custom local MCP server for weather
├── booking_system/             ← NEW: Autonomous Booking Engine
│   ├── app/
│   │   ├── main.py             ← FastAPI Backend for Checkout
│   │   ├── agents/
│   │   │   └── booking_orchestrator.py  ← Booking StateGraph agent
│   │   ├── api/
│   │   │   └── booking_routes.py        ← API routes for the checkout portal
│   │   ├── models/
│   │   │   └── booking.py               ← SQLAlchemy database models
│   │   ├── schemas/
│   │   │   └── booking_schema.py        ← Pydantic schema validations
│   │   ├── services/
│   │   │   ├── booking_service.py       ← Core booking persistence
│   │   │   ├── consent_service.py       ← User consent processing
│   │   │   └── payment_service.py       ← Mock payment and confirmation
│   │   ├── providers/
│   │   │   ├── base_provider.py         ← Abstract interface for travel providers
│   │   │   └── mock_provider.py         ← Mock Flight/Train/Bus/Hotel providers
│   │   └── static/
│   │       ├── index.html               ← Secure Checkout Portal UI
│   │       ├── app.js                   ← Checkout logic & Ticket rendering
│   │       └── style.css                ← Checkout UI styling
│   └── mcp_server/
│       └── booking_mcp_server.py        ← FastMCP server wrapping booking actions
└── venv/                       ← Python virtual environment
```

---

## 📄 File-by-File Analysis (Key Components)

### 1. [main.py](file:///c:/Users/daksh/OneDrive/Desktop/Multi_Agent_System_With_Mcp/main.py) — Core Planning Pipeline

| Aspect | Details |
|--------|---------|
| **Role** | Defines the initial LangGraph state machine with 5 planning agents |
| **LLM** | Groq — `llama-3.3-70b-versatile` |
| **Updates** | Added `extract_structured_request` to parse the `TripRequest` deterministically (origin, destination, dates, budget). |

**Agent Pipeline (Sequential):**
```mermaid
graph LR
    START --> extract_structured_request --> flight_agent --> hotel_agent --> weather_agent --> itinerary_agent --> END
```

---

### 2. Autonomous Booking System (`booking_system/`)

The newly introduced booking system operates via a secondary LangGraph orchestrated in `booking_orchestrator.py`. 

| Component | Description |
|-----------|-------------|
| **Booking Orchestrator** | (`booking_orchestrator.py`) StateGraph that runs the `orchestrator_agent`, pauses for a `consent_gate`, and finishes with a `confirmation_agent`. |
| **FastAPI Backend** | (`booking_system/app/main.py`) Serves the API routes and mounts the static Secure Checkout Portal. |
| **Database** | (`models/booking.py`) SQLite/SQLAlchemy schema storing `BookingSession`, `BookingItem`, and `Booking`. Recently upgraded to retain robust route fields (`origin`, `destination`, `from_location`, `to_location`). |
| **Providers** | (`mock_provider.py`) Simulates interactions with travel APIs. Upgraded to normalize responses so all transport types (Flight, Train, Bus) reliably output uniform ticket details. |
| **Booking MCP Server** | (`booking_mcp_server.py`) Exposes internal booking backend functions (search, add item, propose, confirm) as MCP tools so the `booking_orchestrator` can invoke them seamlessly. |

---

### 3. [frontend.py](file:///c:/Users/daksh/OneDrive/Desktop/Multi_Agent_System_With_Mcp/frontend.py) & Checkout UI

| Aspect | Details |
|--------|---------|
| **Streamlit Planner** | Captures the user's initial prompt, streams the agent thought process, and presents the Final Travel Plan. Now extracts and stores `trip_data` in session state to pass down to the booking layer. |
| **Secure Checkout Portal** | (`app.js`, `index.html`) A dedicated web interface loaded after the Booking Orchestrator proposes a plan. Users approve payments here, and the final confirmed Tickets (Flights, Trains, Buses, Hotels) are generated and rendered natively with origin/destination parsing. |

---

## 🧰 Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Orchestration** | LangGraph (StateGraph) for both Planning & Booking pipelines |
| **LLM** | Groq Cloud — LLaMA 3.3 70B Versatile |
| **Tool Protocol** | MCP (Model Context Protocol) via `langchain-mcp-adapters` and `FastMCP` |
| **Persistence** | SQLAlchemy (SQLite local instance for MVP) |
| **Frontend/UI** | Streamlit (Planner) + Vanilla JS/HTML/CSS (Checkout Portal) |
| **Backend API** | FastAPI (Checkout API) |

---

## 📈 Current State Metrics & Enhancements

| Metric | Details |
|--------|---------|
| **Data Flow Fix** | Successfully eliminated the "Origin/Destination lost" bug by passing structured Pydantic data down the pipeline rather than recursively relying on LLMs to parse generated text. |
| **UI Resiliency** | Added fallback logic in `app.js` and JavaScript console warnings to monitor missing routes instead of rendering "N/A" on tickets. |
| **New Integrations** | Bus booking option added to the ticket rendering suite. |

> [!TIP]
> The SQLite database was recently reset to correctly initialize the updated `BookingSession` and `Booking` schema columns (`origin`, `destination`, `from_location`, `to_location`, `departure`, `arrival`). If migrating to PostgreSQL in the future, consider using Alembic for dynamic schema migrations.
