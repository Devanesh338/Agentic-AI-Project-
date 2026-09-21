from sqlalchemy.orm import Session
from app.models.booking import BookingSession, Payment, Booking
from app.services.booking_service import get_booking_session
from app.providers.mock_provider import get_provider
import uuid

def process_payment(db: Session, session_id: str) -> Payment:
    session = get_booking_session(db, session_id)
    if not session:
        raise ValueError("Booking session not found")
        
    if session.status != "PAYMENT_AUTHORIZED":
        raise PermissionError("Explicit user payment consent is required. Cannot process payment.")
        
    payment = Payment(
        booking_session_id=session_id,
        amount=session.total_amount,
        currency=session.currency,
        status="SUCCESS",
        provider_reference=f"PAY-{str(uuid.uuid4())[:8].upper()}"
    )
    db.add(payment)
    session.status = "BOOKED"
    db.commit()
    db.refresh(payment)
    return payment

def confirm_bookings(db: Session, session_id: str) -> list[Booking]:
    session = get_booking_session(db, session_id)
    if not session:
        raise ValueError("Booking session not found")
        
    # Check if payment was successful
    payment = db.query(Payment).filter(
        Payment.booking_session_id == session_id,
        Payment.status == "SUCCESS"
    ).first()
    
    if not payment:
        raise PermissionError("Payment has not been completed successfully.")
        
    confirmed_bookings = []
    
    for item in session.booking_items:
        # Check idempotency: see if booking already exists for this item
        existing_booking = db.query(Booking).filter(
            Booking.booking_session_id == session_id,
            Booking.booking_type == item.type,
            Booking.provider == item.provider
        ).first()
        
        if existing_booking:
            confirmed_bookings.append(existing_booking)
            continue
            
        provider = get_provider(item.type)
        idempotency_key = f"{session_id}:{item.id}:confirm"
        
        # In a real app we'd use the booking token from prepare_booking
        confirmation = provider.confirm_booking(f"token_{item.id}", idempotency_key)
        
        import json
        try:
            details_dict = json.loads(item.details) if isinstance(item.details, str) else item.details
        except:
            details_dict = {}
            
        booking = Booking(
            booking_session_id=session_id,
            booking_type=item.type,
            provider=item.provider,
            external_reference=confirmation.get("pnr", confirmation.get("booking_id", "REF-UNKNOWN")),
            from_location=confirmation.get("from", details_dict.get("from")),
            to_location=confirmation.get("to", details_dict.get("to")),
            departure=confirmation.get("departure", details_dict.get("departure")),
            arrival=confirmation.get("arrival", details_dict.get("arrival")),
            price=confirmation.get("price", item.price),
            status="CONFIRMED",
            confirmation_data=str(confirmation)
        )
        db.add(booking)
        item.status = "CONFIRMED"
        confirmed_bookings.append(booking)
        
    db.commit()
    return confirmed_bookings
