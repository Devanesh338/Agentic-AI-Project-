from sqlalchemy.orm import Session
from app.models.booking import BookingSession, BookingItem, User
from app.schemas.booking_schema import BookingSessionCreate, BookingItemSchema
from app.providers.mock_provider import get_provider
import uuid
from typing import List, Dict, Any
from datetime import datetime, timedelta

def create_booking_session(db: Session, session_data: BookingSessionCreate) -> BookingSession:
    # Verify user exists or create a mock user for demo
    user = db.query(User).filter(User.id == session_data.user_id).first()
    if not user:
        unique_email = f"test_{session_data.user_id}@example.com"
        user = User(id=session_data.user_id, name="Test User", email=unique_email)
        db.add(user)
        db.commit()

    db_session = BookingSession(
        user_id=session_data.user_id,
        itinerary_id=session_data.itinerary_id,
        origin=session_data.origin,
        destination=session_data.destination,
        departure_date=session_data.departure_date,
        return_date=session_data.return_date,
        travelers=session_data.travelers,
        status="PLANNING"
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_booking_session(db: Session, session_id: str) -> BookingSession:
    return db.query(BookingSession).filter(BookingSession.id == session_id).first()

def search_options(provider_type: str, request: Dict[str, Any]) -> List[Dict[str, Any]]:
    provider = get_provider(provider_type)
    return provider.search(request)

def add_booking_item(db: Session, session_id: str, item_data: BookingItemSchema) -> BookingItem:
    session = get_booking_session(db, session_id)
    if not session:
        raise ValueError("Session not found")
    
    db_item = BookingItem(
        booking_session_id=session_id,
        type=item_data.type,
        provider=item_data.provider,
        option_id=item_data.option_id,
        details=str(item_data.details),
        price=item_data.price,
        status="PREPARED"
    )
    db.add(db_item)
    
    # Update session total amount
    session.total_amount += item_data.price
    session.status = "OPTIONS_FOUND"
    
    db.commit()
    db.refresh(db_item)
    return db_item

def create_booking_proposal(db: Session, session_id: str) -> BookingSession:
    session = get_booking_session(db, session_id)
    if not session:
        raise ValueError("Session not found")
    
    session.status = "AWAITING_PAYMENT_CONSENT"
    # Expires in 15 mins
    session.expires_at = datetime.utcnow() + timedelta(minutes=15) 
    db.commit()
    db.refresh(session)
    return session
