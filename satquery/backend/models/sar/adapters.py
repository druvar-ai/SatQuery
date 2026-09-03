from typing import List, Dict, Any, Union
import numpy as np
from satquery.backend.models.base import RemoteSensingModel

class SARMAEAdapter(RemoteSensingModel):
    def get_id(self) -> str: return "sarmae-base"
    def get_name(self) -> str: return "SARMAE"
    def get_modality(self) -> str: return "sar"
    def get_capabilities(self) -> List[str]: return ["SCENE_DESCRIPTION", "FEATURE_EXTRACTION"]
    
    def get_status(self) -> str: return "NOT_INSTALLED"
    def get_device(self) -> str: return "none"
    def get_reason(self) -> str: return "Requires specific SAR model checkpoints and PyTorch."
    
    def is_available(self) -> bool: return False
    def is_loaded(self) -> bool: return False
    def load(self) -> None: pass
    def unload(self) -> None: pass
    
    def predict(self, input_data: Union[np.ndarray, Dict[str, Any]]) -> Dict[str, Any]:
        return {"error": "SARMAE model is NOT_INSTALLED."}

class SARHubAdapter(RemoteSensingModel):
    def get_id(self) -> str: return "sar-hub"
    def get_name(self) -> str: return "SAR-HUB"
    def get_modality(self) -> str: return "sar"
    def get_capabilities(self) -> List[str]: return ["SCENE_DESCRIPTION", "SEGMENTATION"]
    
    def get_status(self) -> str: return "NOT_INSTALLED"
    def get_device(self) -> str: return "none"
    def get_reason(self) -> str: return "Requires SAR-HUB dependencies."
    
    def is_available(self) -> bool: return False
    def is_loaded(self) -> bool: return False
    def load(self) -> None: pass
    def unload(self) -> None: pass
    
    def predict(self, input_data: Union[np.ndarray, Dict[str, Any]]) -> Dict[str, Any]:
        return {"error": "SAR-HUB model is NOT_INSTALLED."}
