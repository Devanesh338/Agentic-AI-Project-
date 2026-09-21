import json
import sys
import os
from typing import TypedDict, Annotated, List, Any
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from dotenv import load_dotenv

# Reliably find project root using __file__
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, "..", "..", ".."))

# Load .env explicitly from project root
load_dotenv(dotenv_path=os.path.join(_project_root, ".env"), override=True)

llm = ChatGroq(model="openai/gpt-oss-120b")

class BookingState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_id: str
    itinerary: str
    origin: str
    destination: str
    departure_date: str
    return_date: str
    travelers: int
    budget: float
    session_id: str
    consent_status: str
    booking_status: str
    booking_details: str

async def run_booking_mcp_tool(tool_name: str, arguments: dict):
    # This runs the booking_mcp_server.py as a subprocess MCP server
    env = os.environ.copy()
    
    # Reliably find project root using __file__ instead of os.getcwd()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    
    env["PYTHONPATH"] = os.path.join(project_root, "booking_system")
    
    # Handle global Streamlit execution by forcing venv python if available
    venv_python = os.path.join(project_root, "venv", "Scripts", "python.exe")
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
    
    server_script = os.path.join(project_root, "booking_system", "mcp_server", "wrapper.py")
    
    server_params = StdioServerParameters(
        command=python_cmd,
        args=[server_script],
        env=env
    )
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                
                if result.isError:
                    # If MCP itself returns an error
                    error_text = result.content[0].text if result.content else "Unknown MCP Error"
                    return json.dumps({"error": f"MCP Error: {error_text}"})
                    
                if not result.content:
                    return json.dumps({"error": f"Tool {tool_name} returned empty content!"})
                    
                return result.content[0].text
    except Exception as e:
        return json.dumps({"error": f"Subprocess exception: {str(e)}"})

async def orchestrator_agent(state: BookingState):
    """
    Search and prepare bookings using MCP tools.
    """
    prompt = f"""
You are an autonomous Travel Booking Orchestrator.
Your goal is to book the following itinerary for user {state['user_id']}.
Itinerary:
{state['itinerary']}

Steps:
1. Create a booking session using `create_booking_session` tool.
2. Search for transport (flight/train/bus) and hotels.
3. Select the best options and add them using `add_booking_item`.
4. Propose the booking using `propose_booking`.

Provide the final proposed session ID and total amount.
"""
    # For a real implementation, we'd bind the MCP tools to the LLM. 
    # Here, for brevity, we will manually call the tools to simulate the AI actions.
    
    # 1. Create Session
    session_resp = json.loads(await run_booking_mcp_tool("create_booking_session", {
        "user_id": state["user_id"],
        "origin": state.get("origin", ""),
        "destination": state.get("destination", ""),
        "departure_date": state.get("departure_date", ""),
        "return_date": state.get("return_date", ""),
        "travelers": state.get("travelers", 1)
    }))
    if "error" in session_resp:
        raise ValueError(f"Failed to create booking session: {session_resp['error']}")
    session_id = session_resp.get("session_id")
    
    # 2. Add Mock Items (simulating LLM searching and selecting)
    origin = state.get("origin", "Origin")
    destination = state.get("destination", "Destination")

    await run_booking_mcp_tool("add_booking_item", {
        "session_id": session_id,
        "type": "train",
        "provider": "DemoRail",
        "option_id": "TR-8821",
        "price": 2450.0,
        "details_json": json.dumps({
            "train_name": "Karnataka Express", 
            "class": "3A", 
            "from": origin, 
            "to": destination
        })
    })
    
    await run_booking_mcp_tool("add_booking_item", {
        "session_id": session_id,
        "type": "hotel",
        "provider": "DemoHotel",
        "option_id": "HT-991",
        "price": 3600.0,
        "details_json": json.dumps({
            "hotel_name": "Demo Hotel Delhi", 
            "room_type": "Deluxe", 
            "location": destination
        })
    })
    
    # 3. Propose
    raw_proposal = await run_booking_mcp_tool("propose_booking", {"session_id": session_id})
    try:
        proposal_resp = json.loads(raw_proposal)
    except json.JSONDecodeError:
        proposal_resp = {"error": f"Failed to parse propose_booking response: {repr(raw_proposal)}"}
    
    message = f"Booking proposed. Total: {proposal_resp.get('total_amount')} {proposal_resp.get('currency')}. Session ID: {session_id}"
    
    return {
        "messages": [AIMessage(content=message)],
        "session_id": session_id,
        "booking_status": "AWAITING_CONSENT"
    }

def consent_gate(state: BookingState):
    """
    Interrupt the graph here to wait for human consent.
    """
    pass

async def confirmation_agent(state: BookingState):
    """
    Attempt to confirm the booking. 
    This will fail if consent wasn't given.
    """
    try:
        # We try to confirm using the tool. 
        # The backend logic enforces consent!
        confirm_resp = json.loads(await run_booking_mcp_tool("confirm_booking", {"session_id": state["session_id"]}))
        
        if confirm_resp.get("success"):
            return {
                "booking_status": "CONFIRMED",
                "booking_details": json.dumps(confirm_resp.get("bookings")),
                "messages": [AIMessage(content="Booking successfully confirmed!")]
            }
        else:
            return {
                "booking_status": "FAILED",
                "messages": [AIMessage(content=f"Booking failed: {confirm_resp.get('error')}")]
            }
    except Exception as e:
         return {
            "booking_status": "FAILED",
            "messages": [AIMessage(content=f"Booking failed: {str(e)}")]
        }

booking_graph = StateGraph(BookingState)
booking_graph.add_node("orchestrator", orchestrator_agent)
booking_graph.add_node("consent_gate", consent_gate)
booking_graph.add_node("confirmation", confirmation_agent)

booking_graph.add_edge(START, "orchestrator")
booking_graph.add_edge("orchestrator", "consent_gate")
booking_graph.add_edge("consent_gate", "confirmation")
booking_graph.add_edge("confirmation", END)

# We use an interrupt before the confirmation step
booking_app = booking_graph.compile(checkpointer=MemorySaver(), interrupt_before=["confirmation"])
