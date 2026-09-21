from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    travelers = relationship("Traveler", back_populates="user")
    booking_sessions = relationship("BookingSession", back_populates="user")
    consent_records = relationship("ConsentRecord", back_populates="user")

class Traveler(Base):
    __tablename__ = "travelers"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    age = Column(Integer)
    gender = Column(String, nullable=True)
    government_id_reference = Column(String, nullable=True)

    user = relationship("User", back_populates="travelers")

class BookingSession(Base):
    __tablename__ = "booking_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    itinerary_id = Column(String, nullable=True)
    origin = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    departure_date = Column(String, nullable=True)
    return_date = Column(String, nullable=True)
    travelers = Column(Integer, default=1)
    status = Column(String, default="PLANNING") # e.g. PLANNING, OPTIONS_FOUND, AWAITING_PAYMENT_CONSENT, PAYMENT_AUTHORIZED, BOOKED
    total_amount = Column(Float, default=0.0)
    currency = Column(String, default="INR")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="booking_sessions")
    booking_items = relationship("BookingItem", back_populates="session")
    consent_records = relationship("ConsentRecord", back_populates="session")
    payments = relationship("Payment", back_populates="session")
    bookings = relationship("Booking", back_populates="session")

class BookingItem(Base):
    __tablename__ = "booking_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    booking_session_id = Column(String, ForeignKey("booking_sessions.id"))
    type = Column(String) # 'flight', 'train', 'bus', 'hotel'
    provider = Column(String)
    option_id = Column(String)
    details = Column(Text) # JSON string of item details
    price = Column(Float)
    status = Column(String, default="PREPARED")

    session = relationship("BookingSession", back_populates="booking_items")

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String, primary_key=True, default=generate_uuid)
    booking_session_id = Column(String, ForeignKey("booking_sessions.id"))
    user_id = Column(String, ForeignKey("users.id"))
    amount = Column(Float)
    currency = Column(String, default="INR")
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED, EXPIRED
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    session = relationship("BookingSession", back_populates="consent_records")
    user = relationship("User", back_populates="consent_records")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    booking_session_id = Column(String, ForeignKey("booking_sessions.id"))
    amount = Column(Float)
    currency = Column(String, default="INR")
    status = Column(String, default="PENDING") # PENDING, SUCCESS, FAILED
    provider_reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("BookingSession", back_populates="payments")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=generate_uuid)
    booking_session_id = Column(String, ForeignKey("booking_sessions.id"))
    booking_type = Column(String) # 'flight', 'train', 'bus', 'hotel'
    provider = Column(String)
    external_reference = Column(String) # e.g. PNR
    from_location = Column(String, nullable=True)
    to_location = Column(String, nullable=True)
    departure = Column(String, nullable=True)
    arrival = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    status = Column(String, default="CONFIRMED") # CONFIRMED, CANCELLED
    confirmation_data = Column(Text) # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("BookingSession", back_populates="bookings")
