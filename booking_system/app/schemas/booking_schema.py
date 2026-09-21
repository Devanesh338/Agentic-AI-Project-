from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import ast

class BookingItemSchema(BaseModel):
    id: Optional[str] = None
    type: str
    provider: str
    option_id: str
    details: Dict[str, Any]
    price: float
    status: str = "PREPARED"

    @field_validator('details', mode='before')
    @classmethod
    def parse_details(cls, v: Any) -> Dict[str, Any]:
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                try:
                    return ast.literal_eval(v)
                except Exception:
                    return {}
        return {}

class BookingSessionCreate(BaseModel):
    user_id: str
    itinerary_id: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    travelers: int = 1

class BookingSessionResponse(BaseModel):
    id: str
    user_id: str
    itinerary_id: Optional[str]
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    travelers: int = 1
    status: str
    total_amount: float
    currency: str
    created_at: datetime
    expires_at: Optional[datetime]
    booking_items: List[BookingItemSchema] = []

    class Config:
        from_attributes = True

class ConsentRequest(BaseModel):
    user_id: str
    amount: float
    currency: str = "INR"

class ConsentResponse(BaseModel):
    id: str
    booking_session_id: str
    status: str
    amount: float
    currency: str

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    user_id: str

class PaymentResponse(BaseModel):
    id: str
    status: str
    amount: float
    currency: str
    provider_reference: Optional[str]

    class Config:
        from_attributes = True

class BookingConfirmationResponse(BaseModel):
    booking_id: str
    booking_type: str
    external_reference: str
    status: str
    confirmation_data: Dict[str, Any]

    class Config:
        from_attributes = True
