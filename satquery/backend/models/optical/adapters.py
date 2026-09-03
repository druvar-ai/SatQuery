from typing import List, Dict, Any, Union
import numpy as np
from satquery.backend.models.base import RemoteSensingModel

class SatMAEAdapter(RemoteSensingModel):
    def get_id(self) -> str: return "satmae-base"
    def get_name(self) -> str: return "SatMAE"
    def get_modality(self) -> str: return "multispectral"
    def get_capabilities(self) -> List[str]: return ["SCENE_DESCRIPTION", "FEATURE_EXTRACTION"]
    
    def get_status(self) -> str: return "NOT_INSTALLED"
    def get_device(self) -> str: return "none"
    def get_reason(self) -> str: return "Requires torch, torchvision, and a >300MB checkpoint download."
    
    def is_available(self) -> bool: return False
    def is_loaded(self) -> bool: return False
    def load(self) -> None: pass
    def unload(self) -> None: pass
    
    def predict(self, input_data: Union[np.ndarray, Dict[str, Any]]) -> Dict[str, Any]:
        return {"error": "SatMAE model is NOT_INSTALLED."}

class SatlasPretrainAdapter(RemoteSensingModel):
    def get_id(self) -> str: return "satlas-pretrain"
    def get_name(self) -> str: return "SatlasPretrain"
    def get_modality(self) -> str: return "optical"
    def get_capabilities(self) -> List[str]: return ["SCENE_DESCRIPTION", "FEATURE_EXTRACTION", "OBJECT_DETECTION"]
    
    def get_status(self) -> str: return "NOT_INSTALLED"
    def get_device(self) -> str: return "none"
    def get_reason(self) -> str: return "Requires HuggingFace transformers and pre-trained weights."
    
    def is_available(self) -> bool: return False
    def is_loaded(self) -> bool: return False
    def load(self) -> None: pass
    def unload(self) -> None: pass
    
    def predict(self, input_data: Union[np.ndarray, Dict[str, Any]]) -> Dict[str, Any]:
        return {"error": "SatlasPretrain model is NOT_INSTALLED."}
