from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.booking_schema import (
    BookingSessionCreate, BookingSessionResponse, BookingItemSchema,
    ConsentRequest, ConsentResponse, PaymentRequest, PaymentResponse
)
from app.services import booking_service, consent_service, payment_service
from typing import List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
from typing import List
from pydantic import BaseModel

class FrontendPaymentRequest(BaseModel):
    session_id: str
    thread_id: str
    amount: float
    currency: str


router = APIRouter()

@router.post("/sessions", response_model=BookingSessionResponse)
def create_session(session_data: BookingSessionCreate, db: Session = Depends(get_db)):
    return booking_service.create_booking_session(db, session_data)

@router.get("/sessions/{session_id}", response_model=BookingSessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    from app.database.database import db_path
    
    logger.info(f"Requested session_id: {session_id}")
    logger.info(f"Database path: {db_path}")
    
    session = booking_service.get_booking_session(db, session_id)
    
    logger.info(f"Session exists: {session is not None}")
    
    if not session:
        return JSONResponse(status_code=404, content={
            "success": False,
            "error": "BOOKING_SESSION_NOT_FOUND",
            "message": "Booking session not found",
            "session_id": session_id
        })
        
    logger.info(f"Session status: {session.status}")
    logger.info(f"Number of booking items: {len(session.booking_items)}")
    logger.info(f"Total amount: {session.total_amount}")
    
    return session

@router.post("/sessions/{session_id}/items")
def add_item(session_id: str, item_data: BookingItemSchema, db: Session = Depends(get_db)):
    try:
        return booking_service.add_booking_item(db, session_id, item_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/sessions/{session_id}/propose", response_model=BookingSessionResponse)
def propose_booking(session_id: str, db: Session = Depends(get_db)):
    try:
        return booking_service.create_booking_proposal(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/sessions/{session_id}/consent", response_model=ConsentResponse)
def request_consent(session_id: str, request: ConsentRequest, db: Session = Depends(get_db)):
    try:
        return consent_service.request_consent(db, session_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sessions/{session_id}/consent/{consent_id}/approve", response_model=ConsentResponse)
def approve_consent(session_id: str, consent_id: str, db: Session = Depends(get_db)):
    try:
        return consent_service.approve_consent(db, session_id, consent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sessions/{session_id}/payment", response_model=PaymentResponse)
def process_payment(session_id: str, request: PaymentRequest, db: Session = Depends(get_db)):
    try:
        return payment_service.process_payment(db, session_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sessions/{session_id}/confirm")
def confirm_booking(session_id: str, db: Session = Depends(get_db)):
    try:
        return payment_service.confirm_bookings(db, session_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payment/approve")
def approve_payment_frontend(request: FrontendPaymentRequest, db: Session = Depends(get_db)):
    try:
        session = booking_service.get_booking_session(db, request.session_id)
        if not session:
            return JSONResponse(status_code=404, content={
                "success": False, 
                "error": "BOOKING_SESSION_NOT_FOUND", 
                "message": "Booking session not found", 
                "session_id": request.session_id
            })
            
        # Revalidate price
        if request.amount != session.total_amount:
            return JSONResponse(status_code=400, content={
                "success": False,
                "error": "PRICE_CHANGED",
                "message": f"Price changed from {request.amount} to {session.total_amount}. New consent required."
            })

        # Get or create consent
        consent = consent_service.get_consent_status(db, session.id)
        if not consent or consent.status != "PENDING" or consent.amount != session.total_amount:
            # Create new consent request
            consent_req = ConsentRequest(user_id=session.user_id, amount=session.total_amount, currency=session.currency)
            consent = consent_service.request_consent(db, session.id, consent_req)
            
        # Approve consent
        try:
            consent_service.approve_consent(db, session.id, consent.id)
        except Exception as e:
            return JSONResponse(status_code=400, content={"success": False, "error": "CONSENT_FAILED", "message": str(e)})

        # Process payment and confirm bookings
        payment = payment_service.process_payment(db, request.session_id)
        confirmed = payment_service.confirm_bookings(db, request.session_id)

        # Format tickets for frontend
        import json
        import ast
        tickets = []
        for booking, item in zip(confirmed, session.booking_items):
            item_details = {}
            if isinstance(item.details, str):
                try:
                    item_details = json.loads(item.details)
                except Exception:
                    try:
                        item_details = ast.literal_eval(item.details)
                    except Exception:
                        pass
            elif isinstance(item.details, dict):
                item_details = item.details
                
            tickets.append({
                "type": booking.booking_type,
                "reference": booking.external_reference,
                "details": item_details
            })
            
        return {"success": True, "tickets": tickets}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": "INTERNAL_ERROR", "message": str(e)})
