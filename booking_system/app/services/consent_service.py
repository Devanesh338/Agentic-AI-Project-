from sqlalchemy.orm import Session
from app.models.booking import BookingSession, ConsentRecord
from app.schemas.booking_schema import ConsentRequest
from app.services.booking_service import get_booking_session
from datetime import datetime, timedelta

def request_consent(db: Session, session_id: str, request: ConsentRequest) -> ConsentRecord:
    session = get_booking_session(db, session_id)
    if not session:
        raise ValueError("Booking session not found")
    
    if session.status != "AWAITING_PAYMENT_CONSENT":
        raise ValueError(f"Session is not awaiting consent. Current status: {session.status}")
    
    # Check if a pending consent already exists, if so expire it
    existing = db.query(ConsentRecord).filter(
        ConsentRecord.booking_session_id == session_id,
        ConsentRecord.status == "PENDING"
    ).all()
    for ex in existing:
        ex.status = "EXPIRED"
        
    consent = ConsentRecord(
        booking_session_id=session_id,
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency,
        status="PENDING",
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent

def approve_consent(db: Session, session_id: str, consent_id: str) -> ConsentRecord:
    consent = db.query(ConsentRecord).filter(ConsentRecord.id == consent_id).first()
    if not consent:
        raise ValueError("Consent record not found")
        
    if consent.status != "PENDING":
        raise ValueError(f"Consent cannot be approved. Current status: {consent.status}")
        
    if consent.expires_at and consent.expires_at < datetime.utcnow():
        consent.status = "EXPIRED"
        db.commit()
        raise ValueError("Consent request has expired")
        
    session = get_booking_session(db, session_id)
    
    # Critical revalidation step: Price check
    # In a real app we'd re-call the providers here, but for this mock we just check the session total amount
    # vs the consent amount.
    if session.total_amount != consent.amount:
        consent.status = "REJECTED"
        db.commit()
        raise ValueError(f"Price changed from {consent.amount} to {session.total_amount}. New consent required.")
        
    consent.status = "APPROVED"
    session.status = "PAYMENT_AUTHORIZED"
    
    db.commit()
    db.refresh(consent)
    return consent

def get_consent_status(db: Session, session_id: str) -> ConsentRecord:
    return db.query(ConsentRecord).filter(
        ConsentRecord.booking_session_id == session_id
    ).order_by(ConsentRecord.created_at.desc()).first()
