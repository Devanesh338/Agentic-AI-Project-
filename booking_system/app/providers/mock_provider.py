import uuid
from typing import Dict, Any, List
from app.providers.base_provider import TravelProvider
from datetime import datetime, timedelta

class MockFlightProvider(TravelProvider):
    def search(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{
            "option_id": "FL-10291",
            "provider": "DemoAir",
            "from": request.get("origin", "MAA"),
            "to": request.get("destination", "DEL"),
            "departure": "2026-10-10T06:30:00",
            "arrival": "2026-10-10T09:20:00",
            "duration_minutes": 170,
            "price": 5200,
            "currency": "INR",
            "available_seats": 4,
            "type": "flight"
        }]

    def get_details(self, option_id: str) -> Dict[str, Any]:
        return {"option_id": option_id, "price": 5200, "available_seats": 4}

    def prepare_booking(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {"booking_token": f"token_fl_{uuid.uuid4()}", "price": 5200}

    def confirm_booking(self, booking_token: str, idempotency_key: str) -> Dict[str, Any]:
        return {"pnr": f"PNR-{str(uuid.uuid4())[:6].upper()}", "status": "CONFIRMED"}

    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        return {"status": "CANCELLED", "refund_amount": 4700}

class MockTrainProvider(TravelProvider):
    def search(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{
            "option_id": "TR-8821",
            "provider": "DemoRail",
            "train_number": "12627",
            "train_name": "Karnataka Express",
            "from": request.get("origin", "Chennai"),
            "to": request.get("destination", "Delhi"),
            "departure": "2026-10-10T06:30:00",
            "arrival": "2026-10-11T09:20:00",
            "class": "3A",
            "price": 2450,
            "currency": "INR",
            "available_seats": 12,
            "type": "train"
        }]

    def get_details(self, option_id: str) -> Dict[str, Any]:
        return {"option_id": option_id, "price": 2450, "available_seats": 12}

    def prepare_booking(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {"booking_token": f"token_tr_{uuid.uuid4()}", "price": 2450}

    def confirm_booking(self, booking_token: str, idempotency_key: str) -> Dict[str, Any]:
        return {"pnr": f"PNR-{str(uuid.uuid4())[:8].upper()}", "status": "CONFIRMED"}

    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        return {"status": "CANCELLED", "refund_amount": 1950}

class MockHotelProvider(TravelProvider):
    def search(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{
            "option_id": "HT-991",
            "provider": "DemoHotel",
            "hotel_name": "Demo Hotel Delhi",
            "location": request.get("destination", "Delhi"),
            "room_type": "Deluxe",
            "nightly_price": 1200,
            "total_price": 3600,
            "currency": "INR",
            "available_rooms": 3,
            "type": "hotel"
        }]

    def get_details(self, option_id: str) -> Dict[str, Any]:
        return {"option_id": option_id, "total_price": 3600, "available_rooms": 3}

    def prepare_booking(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {"booking_token": f"token_ht_{uuid.uuid4()}", "price": 3600}

    def confirm_booking(self, booking_token: str, idempotency_key: str) -> Dict[str, Any]:
        return {"booking_id": f"HT-BK-{str(uuid.uuid4())[:6].upper()}", "status": "CONFIRMED"}

    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        return {"status": "CANCELLED", "refund_amount": 3000}

# Factory to get providers
def get_provider(type: str) -> TravelProvider:
    if type == "flight":
        return MockFlightProvider()
    elif type == "train":
        return MockTrainProvider()
    elif type == "hotel":
        return MockHotelProvider()
    else:
        raise ValueError(f"Unknown provider type: {type}")
