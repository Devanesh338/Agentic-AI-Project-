import os
import sys
import uuid
import json
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from langchain_core.messages import AIMessage

# Add booking_system to path so absolute imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
sys.path.append(os.path.join(project_root, "booking_system"))

from app.database.database import SessionLocal, Base, engine
from app.services.booking_service import get_booking_session
from app.services.consent_service import request_consent, approve_consent
from app.schemas.booking_schema import ConsentRequest
from app.agents.booking_orchestrator import booking_app

app = FastAPI(title="Booking & Payment Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PaymentApprovalRequest(BaseModel):
    session_id: str
    thread_id: str
    amount: float
    currency: str

@app.get("/api/session/{session_id}")
def get_session(session_id: str, db = Depends(get_db)):
    session = get_booking_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    import ast
    items = []
    for item in session.booking_items:
        try:
            details = json.loads(item.details) if item.details else {}
        except json.JSONDecodeError:
            details = ast.literal_eval(item.details) if item.details else {}
            
        items.append({
            "id": item.id,
            "type": item.type,
            "provider": item.provider,
            "price": item.price,
            "details": details,
            "status": item.status
        })
        
    return {
        "id": session.id,
        "status": session.status,
        "total_amount": session.total_amount,
        "currency": session.currency,
        "items": items
    }

@app.post("/api/payment/approve")
async def approve_payment(req: PaymentApprovalRequest, db = Depends(get_db)):
    try:
        # 1. Register consent
        c_req = ConsentRequest(user_id=req.thread_id, amount=req.amount, currency=req.currency)
        c_rec = request_consent(db, req.session_id, c_req)
        approve_consent(db, req.session_id, c_rec.id)
        
        # 2. Resume LangGraph orchestrator
        booking_config = {"configurable": {"thread_id": req.thread_id}}
        final_res = await booking_app.ainvoke(None, config=booking_config)
        
        booking_details = final_res.get("booking_details")
        if not booking_details:
             raise Exception(final_res.get("messages", [AIMessage(content="Unknown error")])[-1].content)
             
        return {"success": True, "tickets": json.loads(booking_details)}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount static files at root
static_dir = os.path.join(project_root, "booking_system", "app", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
