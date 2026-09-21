import asyncio
from booking_system.app.agents.booking_orchestrator import run_booking_mcp_tool

async def main():
    try:
        print("Creating session...")
        session_json = await run_booking_mcp_tool("create_booking_session", {"user_id": "test_user"})
        print("Session:", session_json)
        import json
        session_id = json.loads(session_json)["session_id"]
        print("Adding flight...")
        await run_booking_mcp_tool("add_booking_item", {
            "session_id": session_id,
            "type": "flight",
            "provider": "DemoAir",
            "option_id": "FL-101",
            "price": 2450.0,
            "details_json": json.dumps({"flight_number": "DA-101", "origin": "DEL"})
        })
        
        print("Adding train...")
        await run_booking_mcp_tool("add_booking_item", {
            "session_id": session_id,
            "type": "train",
            "provider": "DemoRail",
            "option_id": "TR-55",
            "price": 2450.0,
            "details_json": json.dumps({"train_name": "Karnataka Express", "class": "3A"})
        })
        
        print("Adding hotel...")
        await run_booking_mcp_tool("add_booking_item", {
            "session_id": session_id,
            "type": "hotel",
            "provider": "DemoHotel",
            "option_id": "HT-991",
            "price": 3600.0,
            "details_json": json.dumps({"hotel_name": "Demo Hotel Delhi", "room_type": "Deluxe"})
        })
        
        print("Proposing booking...")
        proposal_json = await run_booking_mcp_tool("propose_booking", {"session_id": session_id})
        print("Proposal raw output:", repr(proposal_json))
        proposal_parsed = json.loads(proposal_json)
        print("Parsed:", proposal_parsed)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
