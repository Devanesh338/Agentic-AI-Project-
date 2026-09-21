from abc import ABC, abstractmethod
from typing import Dict, Any, List

class TravelProvider(ABC):
    @abstractmethod
    def search(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_details(self, option_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def prepare_booking(self, request: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def confirm_booking(self, booking_token: str, idempotency_key: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        pass
