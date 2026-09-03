from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from satquery.backend.data.schemas import ObservationImage

class SatelliteDataProvider(ABC):
    @abstractmethod
    def search(self, target_lat: float, target_lon: float, start_time: datetime, end_time: datetime, **kwargs) -> List[Dict[str, Any]]:
        """Search for available satellite imagery metadata."""
        pass
        
    @abstractmethod
    def acquire(self, product_metadata: Dict[str, Any], observation_id: str) -> Optional[ObservationImage]:
        """Download or link the imagery and return a structured ObservationImage."""
        pass
        
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is currently accessible (e.g., online, authenticated)."""
        pass
        
    @abstractmethod
    def get_source_name(self) -> str:
        pass
