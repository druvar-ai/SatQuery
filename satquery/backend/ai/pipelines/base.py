from abc import ABC, abstractmethod
from typing import List, Dict, Any
from satquery.backend.ai.schemas import QueryIntent, SatQueryResponse
from satquery.backend.data.schemas import ObservationImage
from satquery.backend.models.registry import ModelRegistry

class BasePipeline(ABC):
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        
    @abstractmethod
    def execute(self, intent: QueryIntent, images: List[ObservationImage], trace: Dict[str, Any]) -> SatQueryResponse:
        pass
