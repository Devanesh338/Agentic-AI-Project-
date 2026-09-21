import asyncio, uuid, os
from booking_system.app.agents.booking_orchestrator import booking_app

async def test_invoke():
    booking_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    book_res = await booking_app.ainvoke(
        {
            "messages": [],
            "user_id": "test_user",
            "itinerary": "Test Itinerary",
            "session_id": "",
            "consent_status": "PENDING",
            "booking_status": "",
            "booking_details": ""
        },
        config=booking_config
    )
    print("Result:", book_res)

if __name__ == "__main__":
    asyncio.run(test_invoke())
