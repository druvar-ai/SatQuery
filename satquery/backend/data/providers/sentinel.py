import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from satquery.backend.data.providers.base import SatelliteDataProvider
from satquery.backend.data.schemas import ObservationImage
import logging

logger = logging.getLogger(__name__)

class Sentinel2Provider(SatelliteDataProvider):
    """Optical/Multispectral Earth Observation Provider"""
    
    def _has_credentials(self) -> bool:
        return bool(os.getenv("COPERNICUS_API_KEY"))
    
    def is_available(self) -> bool:
        return self._has_credentials()
        
    def get_source_name(self) -> str:
        return "sentinel-2"
        
    def search(self, target_lat: float, target_lon: float, start_time: datetime, end_time: datetime, **kwargs) -> List[Dict[str, Any]]:
        if not self._has_credentials():
            logger.warning("EXTERNAL_PROVIDER_UNAVAILABLE: Missing COPERNICUS_API_KEY.")
            return []
        # Real API logic would go here if key exists
        return []
        
    def acquire(self, product_metadata: Dict[str, Any], observation_id: str) -> Optional[ObservationImage]:
        if not self._has_credentials():
            logger.error("EXTERNAL_PROVIDER_UNAVAILABLE: Cannot acquire without credentials.")
            return None
        return None

class Sentinel1Provider(SatelliteDataProvider):
    """SAR Earth Observation Provider"""
    
    def _has_credentials(self) -> bool:
        return bool(os.getenv("COPERNICUS_API_KEY"))
    
    def is_available(self) -> bool:
        return self._has_credentials()
        
    def get_source_name(self) -> str:
        return "sentinel-1"
        
    def search(self, target_lat: float, target_lon: float, start_time: datetime, end_time: datetime, **kwargs) -> List[Dict[str, Any]]:
        if not self._has_credentials():
            logger.warning("EXTERNAL_PROVIDER_UNAVAILABLE: Missing COPERNICUS_API_KEY.")
            return []
        # Real API logic would go here
        return []
        
    def acquire(self, product_metadata: Dict[str, Any], observation_id: str) -> Optional[ObservationImage]:
        if not self._has_credentials():
            logger.error("EXTERNAL_PROVIDER_UNAVAILABLE: Cannot acquire without credentials.")
            return None
        return None
