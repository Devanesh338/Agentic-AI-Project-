import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.database import Base
from app.services import booking_service, consent_service, payment_service
from app.schemas.booking_schema import BookingSessionCreate, BookingItemSchema, ConsentRequest

# Setup test DB
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_booking_workflow_success(db):
    # 1. Create Session
    session = booking_service.create_booking_session(db, BookingSessionCreate(user_id="test_user_1"))
    assert session.id is not None
    
    # 2. Add Item
    item = BookingItemSchema(
        type="flight",
        provider="DemoAir",
        option_id="FL-102",
        price=5200.0,
        details={"origin": "MAA"}
    )
    booking_service.add_booking_item(db, session.id, item)
    assert session.total_amount == 5200.0
    
    # 3. Propose
    session = booking_service.create_booking_proposal(db, session.id)
    assert session.status == "AWAITING_PAYMENT_CONSENT"
    
    # 4. Try confirm without consent (should fail)
    with pytest.raises(PermissionError):
        payment_service.confirm_bookings(db, session.id)
        
    # 5. Consent
    c_req = ConsentRequest(user_id="test_user_1", amount=5200.0, currency="INR")
    c_rec = consent_service.request_consent(db, session.id, c_req)
    consent_service.approve_consent(db, session.id, c_rec.id)
    
    assert session.status == "PAYMENT_AUTHORIZED"
    
    # 6. Payment & Confirm
    payment_service.process_payment(db, session.id)
    bookings = payment_service.confirm_bookings(db, session.id)
    
    assert len(bookings) == 1
    assert bookings[0].status == "CONFIRMED"
    
def test_price_change_invalidates_consent(db):
    session = booking_service.create_booking_session(db, BookingSessionCreate(user_id="test_user_2"))
    item = BookingItemSchema(type="train", provider="DemoRail", option_id="TR-1", price=1000.0, details={})
    booking_service.add_booking_item(db, session.id, item)
    booking_service.create_booking_proposal(db, session.id)
    
    c_req = ConsentRequest(user_id="test_user_2", amount=800.0, currency="INR") # Wrong amount!
    c_rec = consent_service.request_consent(db, session.id, c_req)
    
    with pytest.raises(ValueError, match="Price changed"):
        consent_service.approve_consent(db, session.id, c_rec.id)
