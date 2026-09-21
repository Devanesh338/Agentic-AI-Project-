# ── Multi-Agent Travel Booking System with MCP ────────────────────────────────
#
# LangGraph pipeline:
#   START -> flight_agent -> hotel_agent -> weather_agent -> itinerary_agent -> END
#
# All external data comes through MCP servers (Tavily, AviationStack, Weather).

import os
import sys
import asyncio
from typing import TypedDict, Annotated
import operator

import nest_asyncio

# Only apply nest_asyncio when NOT running under Streamlit.
# Streamlit 1.57+ uses a Starlette-based server whose async event loop
# is broken by nest_asyncio patching (causes NoEventLoopError for static files).
# UPDATE: nest_asyncio also breaks anyio (used by MCP clients) even outside Streamlit.
# if "streamlit" not in sys.modules:
#     nest_asyncio.apply()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from mcp_client import (
    tavily_mcp_search,
    get_airports,
    get_airlines,
    weather_mcp_search,
    forecast_mcp_search,
)

load_dotenv(override=True)

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatGroq(model="openai/gpt-oss-120b")


from pydantic import BaseModel, Field

# ── State ─────────────────────────────────────────────────────────────────────
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    origin: str
    destination: str
    departure_date: str
    return_date: str
    travelers: int
    budget: float
    transport_preference: str
    flight_results: str
    hotel_results: str
    weather_results: str
    itinerary: str
    llm_calls: int

class TripRequest(BaseModel):
    origin: str = Field(description="The city the user is departing from")
    destination: str = Field(description="The city the user is traveling to")
    departure_date: str = Field(default="", description="Departure date if specified")
    return_date: str = Field(default="", description="Return date if specified")
    travelers: int = Field(default=1, description="Number of travelers")
    budget: float = Field(default=0.0, description="Total budget if specified")
    transport_preference: str = Field(default="", description="Preferred mode of transport")


# ── Utility ───────────────────────────────────────────────────────────────────
def extract_destination(query: str) -> str:
    """Use LLM to pull the destination city name from a travel query."""
    response = llm.invoke(
        "Extract ONLY the destination city or country name from the "
        f"following travel query. Return just the name, nothing else.\n\n"
        f"Query: {query}"
    )
    return response.content.strip()


# ── Prompts ───────────────────────────────────────────────────────────────────
FLIGHT_AGENT_PROMPT = """\
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:
1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Return concise travel guidance.
"""


# ── Agent Nodes ───────────────────────────────────────────────────────────────

async def extract_structured_request(state: TravelState):
    """Extract structured travel parameters from the user's query."""
    query = state["user_query"]
    extractor_llm = llm.with_structured_output(TripRequest)
    
    try:
        extracted = extractor_llm.invoke(f"Extract travel parameters from this query: {query}")
        return {
            "origin": extracted.origin,
            "destination": extracted.destination,
            "departure_date": extracted.departure_date,
            "return_date": extracted.return_date,
            "travelers": extracted.travelers,
            "budget": extracted.budget,
            "transport_preference": extracted.transport_preference,
            "messages": [AIMessage(content="Structured request extracted")],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }
    except Exception as e:
        return {
            "origin": "Unknown",
            "destination": "Unknown",
            "messages": [AIMessage(content=f"Extraction failed: {e}")],
        }

async def flight_agent(state: TravelState):
    """Fetch airports & airlines via AviationStack MCP, then ask LLM for advice."""
    query = state["user_query"]

    try:
        airports = await get_airports()
        airlines = await get_airlines()

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000],
        )

        response = llm.invoke([
            SystemMessage(content="You are an expert travel flight planner."),
            HumanMessage(content=prompt),
        ])
        flight_data = response.content

    except Exception as e:
        flight_data = f"Flight information unavailable: {e}"

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight recommendations generated")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


async def hotel_agent(state: TravelState):
    """Search hotels via Tavily MCP."""
    city = state.get("destination") or extract_destination(state["user_query"])
    query = f"top rated hotels to stay in {city}"

    try:
        hotel_results = await tavily_mcp_search(query)
    except Exception as e:
        hotel_results = f"Hotel search unavailable: {e}"

    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content="Hotel information fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


async def weather_agent(state: TravelState):
    """Fetch current weather + forecast via Weather MCP."""
    try:
        city = state.get("destination") or extract_destination(state["user_query"])
        weather_data = await weather_mcp_search(city)
        forecast_data = await forecast_mcp_search(city)

        combined = (
            f"Current Weather for {city}:\n{weather_data}\n\n"
            f"5-Day Forecast:\n{forecast_data}"
        )
    except Exception as e:
        combined = f"Weather information unavailable: {e}"

    return {
        "weather_results": combined,
        "messages": [AIMessage(content="Weather information fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


async def itinerary_agent(state: TravelState):
    """Combine all data and ask LLM to build a travel itinerary."""
    prompt = f"""\
Create a detailed, well-structured travel itinerary.

User Query:
{state['user_query']}

Flight Information:
{state.get('flight_results', 'N/A')}

Hotel Information:
{state.get('hotel_results', 'N/A')}

Weather Information:
{state.get('weather_results', 'N/A')}

Include day-by-day plan, estimated costs, and practical tips.
"""

    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner."),
        HumanMessage(content=prompt),
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ── Graph Construction ────────────────────────────────────────────────────────
graph = StateGraph(TravelState)

graph.add_node("extract_structured_request", extract_structured_request)
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)

graph.add_edge(START, "extract_structured_request")
graph.add_edge("extract_structured_request", "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "weather_agent")
graph.add_edge("weather_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", END)

# ── Checkpointer ──────────────────────────────────────────────────────────────
checkpointer = MemorySaver()

app = graph.compile(checkpointer=checkpointer)


# ── CLI Entry Point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uuid
    from booking_system.app.agents.booking_orchestrator import booking_app
    from booking_system.app.database.database import Base, engine
    
    # Initialize Booking DB
    Base.metadata.create_all(bind=engine)

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    user_input = input("Enter travel request: ")

    # 1. Travel Planning
    result = asyncio.run(
        app.ainvoke(
            {
                "messages": [HumanMessage(content=user_input)],
                "user_query": user_input,
                "origin": "",
                "destination": "",
                "departure_date": "",
                "return_date": "",
                "travelers": 1,
                "budget": 0.0,
                "transport_preference": "",
                "flight_results": "",
                "hotel_results": "",
                "weather_results": "",
                "itinerary": "",
                "llm_calls": 0,
            },
            config=config,
        )
    )

    print("\n" + "=" * 60)
    print("FINAL TRAVEL PLAN")
    print("=" * 60)
    print(result.get("itinerary", "No itinerary generated."))
    print("\n" + "=" * 60)
    
    # 2. Booking Phase
    do_book = input("Do you want to proceed to booking this itinerary? (yes/no): ")
    if do_book.lower() in ['yes', 'y']:
        booking_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        
        # Start booking graph (stops at confirmation for consent)
        print("\n--- Starting Autonomous Booking Agent ---")
        book_res = asyncio.run(
            booking_app.ainvoke(
                {
                    "messages": [],
                    "user_id": "demo_user_1",
                    "itinerary": result.get("itinerary", ""),
                    "origin": result.get("origin", ""),
                    "destination": result.get("destination", ""),
                    "departure_date": result.get("departure_date", ""),
                    "return_date": result.get("return_date", ""),
                    "travelers": result.get("travelers", 1),
                    "budget": result.get("budget", 0.0),
                    "session_id": "",
                    "consent_status": "PENDING",
                    "booking_status": "",
                    "booking_details": ""
                },
                config=booking_config
            )
        )
        
        # Will print the proposal message
        for msg in book_res.get("messages", []):
            print(f"AI: {msg.content}")
            
        # The graph is now interrupted. Awaiting human consent.
        # We simulate the UI consent here via CLI
        print("\n--- CONSENT GATE ---")
        session_id = book_res.get("session_id")
        print("ATTENTION: Explicit payment consent is required to finalize booking.")
        consent = input(f"Approve payment for session {session_id}? (yes/no): ")
        
        if consent.lower() in ['yes', 'y']:
            from booking_system.app.database.database import SessionLocal
            from booking_system.app.services.consent_service import request_consent, approve_consent
            from booking_system.app.schemas.booking_schema import ConsentRequest
            
            db = SessionLocal()
            try:
                # Backend enforcement: Create and approve consent record in DB
                c_req = ConsentRequest(user_id="demo_user_1", amount=6050.0, currency="INR") # hardcoded amount for CLI demo
                c_rec = request_consent(db, session_id, c_req)
                approve_consent(db, session_id, c_rec.id)
                print("Payment Approved.")
            except Exception as e:
                print(f"Consent Error: {e}")
            finally:
                db.close()
                
            # Resume graph
            print("\n--- Resuming Booking Agent ---")
            final_res = asyncio.run(booking_app.ainvoke(None, config=booking_config))
            for msg in final_res.get("messages", []):
                print(f"AI: {msg.content}")
            if final_res.get("booking_details"):
                print(f"\nBooking Details:\n{final_res['booking_details']}")
        else:
            print("Payment rejected. Booking aborted.")