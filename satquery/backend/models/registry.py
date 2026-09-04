from typing import Any, Dict, List, Optional
from satquery.backend.models.base import RemoteSensingModel
import logging

logger = logging.getLogger(__name__)

class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, RemoteSensingModel] = {}
        
    def register(self, model: RemoteSensingModel):
        self._models[model.get_id()] = model
        logger.info(f"Registered model: {model.get_id()} (Available: {model.is_available()})")
        
    def get_model(self, model_id: str) -> Optional[RemoteSensingModel]:
        return self._models.get(model_id)
        
    def find_models(self, modality: str, capability: str) -> List[RemoteSensingModel]:
        matched = []
        for model in self._models.values():
            if model.get_modality() == modality and capability in model.get_capabilities():
                matched.append(model)
        return matched
        
    def get_all_models(self) -> List[Dict[str, Any]]:
        return [
            m.get_state_dict()
            for m in self._models.values()
        ]

registry = ModelRegistry()
