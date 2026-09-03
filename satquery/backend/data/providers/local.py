import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from satquery.backend.data.providers.base import SatelliteDataProvider
from satquery.backend.data.schemas import ObservationImage

class LocalSampleProvider(SatelliteDataProvider):
    def __init__(self, data_dir: str = "data/samples"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
    def is_available(self) -> bool:
        return True
        
    def get_source_name(self) -> str:
        return "local-sample"
        
    def _create_synthetic_image(self, modality: str, path: str):
        # Create a tiny synthetic array to simulate offline local data without heavy images
        shape = (64, 64, 3) if modality in ["optical", "multispectral"] else (64, 64, 1)
        arr = np.random.randint(0, 255, shape, dtype=np.uint8)
        np.save(path, arr)

    def search(self, target_lat: float, target_lon: float, start_time: datetime, end_time: datetime, **kwargs) -> List[Dict[str, Any]]:
        modality = kwargs.get("modality", "optical")
        # Return a fake matching product
        return [{
            "id": f"SAMPLE_{modality.upper()}_{uuid.uuid4().hex[:8]}",
            "modality": modality,
            "acquisition_time": start_time,
            "simulated": True,
            "cloud_cover": 0.0,
            "source": "SYNTHETIC TEST DATA"
        }]
        
    def acquire(self, product_metadata: Dict[str, Any], observation_id: str) -> Optional[ObservationImage]:
        modality = product_metadata.get("modality", "optical")
        file_path = os.path.join(self.data_dir, f"{product_metadata['id']}.npy")
        
        if not os.path.exists(file_path):
            self._create_synthetic_image(modality, file_path)
            
        bands = ["R", "G", "B"] if modality in ["optical", "multispectral"] else ["VV"]
        
        return ObservationImage(
            image_id=str(uuid.uuid4()),
            observation_id=observation_id,
            source_provider=self.get_source_name(),
            source_product_id=product_metadata["id"],
            modality=modality,
            bands=bands,
            image_reference=file_path,
            dimensions=[64, 64, len(bands)],
            acquisition_time=product_metadata["acquisition_time"],
            simulated=True,
            celestial_body_id="earth",
            geographic_metadata={"fake_lat": 0.0, "fake_lon": 0.0},
            preprocessing_metadata={"source": "SYNTHETIC TEST DATA"}
        )
