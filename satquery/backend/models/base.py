from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
import numpy as np

class RemoteSensingModel(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass
        
    @abstractmethod
    def get_name(self) -> str:
        pass
        
    @abstractmethod
    def get_modality(self) -> str:
        """e.g., optical, multispectral, sar"""
        pass
        
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """e.g., ['SCENE_DESCRIPTION', 'CHANGE_DETECTION']"""
        pass
        
    @abstractmethod
    def get_status(self) -> str:
        """Returns one of: AVAILABLE, UNAVAILABLE, NOT_INSTALLED, WEIGHTS_MISSING, MOCK, BASELINE"""
        pass
        
    @abstractmethod
    def get_device(self) -> str:
        """e.g., 'cpu', 'cuda', 'none'"""
        pass
        
    @abstractmethod
    def get_reason(self) -> str:
        """Textual explanation for the status"""
        pass
        
    @abstractmethod
    def is_available(self) -> bool:
        """True only if AVAILABLE and ready to predict."""
        pass
        
    @abstractmethod
    def is_loaded(self) -> bool:
        pass
        
    def get_state_dict(self) -> Dict[str, Any]:
        """Return the complete state of the model adapter."""
        return {
            "model_id": self.get_id(),
            "name": self.get_name(),
            "modality": self.get_modality(),
            "capabilities": self.get_capabilities(),
            "status": self.get_status(),
            "device": self.get_device(),
            "reason": self.get_reason(),
            "is_loaded": self.is_loaded()
        }
        
    @abstractmethod
    def load(self) -> None:
        pass
        
    @abstractmethod
    def unload(self) -> None:
        pass
        
    @abstractmethod
    def predict(self, input_data: Union[np.ndarray, Dict[str, Any]]) -> Dict[str, Any]:
        pass
