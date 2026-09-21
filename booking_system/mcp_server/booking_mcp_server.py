import os
import json
import asyncio
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP

from app.database.database import SessionLocal, engine
from app.models.booking import Base
from app.services import booking_service, consent_service, payment_service
from app.schemas.booking_schema import BookingSessionCreate, BookingItemSchema, ConsentRequest

# Ensure tables are created
Base.metadata.create_all(bind=engine)

# Create FastMCP server
mcp = FastMCP("Travel Booking System")

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

@mcp.tool()
def search_transport(provider_type: str, origin: str, destination: str, date: str) -> str:
    """
    Search for transport options (flight, train, bus).
    provider_type: 'flight', 'train', 'bus'
    """
    try:
        db = get_db()
        # provider_type like 'flight', 'train'
        options = booking_service.search_options(provider_type, {"origin": origin, "destination": destination, "date": date})
        return json.dumps(options, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def search_hotels(destination: str, checkin_date: str, checkout_date: str) -> str:
    """
    Search for hotel options.
    """
    try:
        db = get_db()
        options = booking_service.search_options("hotel", {"destination": destination, "checkin": checkin_date, "checkout": checkout_date})
        return json.dumps(options, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def create_booking_session(
    user_id: str, 
    itinerary_id: str = None,
    origin: str = None,
    destination: str = None,
    departure_date: str = None,
    return_date: str = None,
    travelers: int = 1
) -> str:
    """
    Create a new booking session for a user.
    """
    try:
        db = get_db()
        session = booking_service.create_booking_session(db, BookingSessionCreate(
            user_id=user_id, 
            itinerary_id=itinerary_id,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            travelers=travelers
        ))
        return json.dumps({"session_id": session.id, "status": session.status})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def add_booking_item(session_id: str, type: str, provider: str, option_id: str, price: float, details_json: str) -> str:
    """
    Add a selected option (flight, hotel, etc.) to the booking session.
    """
    try:
        db = get_db()
        item = BookingItemSchema(
            type=type,
            provider=provider,
            option_id=option_id,
            price=price,
            details=json.loads(details_json)
        )
        db_item = booking_service.add_booking_item(db, session_id, item)
        return json.dumps({"item_id": db_item.id, "status": db_item.status})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def propose_booking(session_id: str) -> str:
    """
    Finalize the items and propose the booking. Changes status to AWAITING_PAYMENT_CONSENT.
    """
    try:
        db = get_db()
        session = booking_service.create_booking_proposal(db, session_id)
        return json.dumps({
            "session_id": session.id, 
            "status": session.status, 
            "total_amount": session.total_amount,
            "currency": session.currency
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def confirm_booking(session_id: str) -> str:
    """
    Attempt to process payment and confirm booking. 
    THIS WILL FAIL IF USER HAS NOT EXPLICITLY GIVEN CONSENT.
    """
    try:
        db = get_db()
        # First process payment (this checks consent/authorization)
        payment_service.process_payment(db, session_id)
        # Then confirm bookings
        bookings = payment_service.confirm_bookings(db, session_id)
        
        session = booking_service.get_booking_session(db, session_id)
        result_bookings = []
        import ast
        for b in bookings:
            item = next((i for i in session.booking_items if i.type == b.booking_type), None)
            item_details = {}
            if item and item.details:
                try:
                    item_details = json.loads(item.details)
                except json.JSONDecodeError:
                    item_details = ast.literal_eval(item.details)
            
            
            result_bookings.append({
                "booking_id": b.id,
                "reference": b.external_reference,
                "type": b.booking_type,
                "data": b.confirmation_data,
                "details": item_details
            })
            
        return json.dumps({"success": True, "bookings": result_bookings})
    except Exception as e:
        # Expected to raise PermissionError if no consent
        return json.dumps({"error": str(e), "success": False})

if __name__ == "__main__":
    mcp.run()
