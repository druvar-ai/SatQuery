from typing import List, Dict, Any, Union
import numpy as np
from satquery.backend.models.base import RemoteSensingModel

class VLMAdapter(RemoteSensingModel):
    def get_id(self) -> str: return "vlm-base"
    def get_name(self) -> str: return "Vision Language Model (Base)"
    def get_modality(self) -> str: return "multimodal"
    def get_capabilities(self) -> List[str]: return ["VISUAL_QUESTION_ANSWERING", "CAPTIONING"]
    
    def get_status(self) -> str: return "NOT_INSTALLED"
    def get_device(self) -> str: return "none"
    def get_reason(self) -> str: return "Requires an LLM inference engine or API key (e.g., LLaVA, GPT-4V)."
    
    def is_available(self) -> bool: return False
    def is_loaded(self) -> bool: return False
    def load(self) -> None: pass
    def unload(self) -> None: pass
    
    def predict(self, input_data: Union[np.ndarray, Dict[str, Any]]) -> Dict[str, Any]:
        return {"error": "VLM is NOT_INSTALLED."}
