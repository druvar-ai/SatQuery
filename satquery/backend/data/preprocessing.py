import numpy as np
from typing import Dict, Any

class OpticalPreprocessor:
    @staticmethod
    def process(image_array: np.ndarray) -> Dict[str, Any]:
        """Normalizes and prepares an optical/multispectral array for model input."""
        # Baseline MVP logic: clip to [0, 255] and scale to [0, 1]
        processed = np.clip(image_array, 0, 255).astype(np.float32) / 255.0
        return {
            "processed_array": processed,
            "metadata": {
                "normalization": "[0, 1]",
                "clipped": True,
                "original_shape": image_array.shape
            }
        }

class SARPreprocessor:
    @staticmethod
    def process(image_array: np.ndarray) -> Dict[str, Any]:
        """Processes SAR arrays, handling backscatter scaling."""
        # Baseline MVP logic: Convert to dB and normalize assuming typical C-band VV values
        # Since our synthetic is just [0, 255], we mock a transformation
        processed = np.clip(image_array, 1e-6, 255)
        processed_db = 10 * np.log10(processed)
        processed_norm = (processed_db + 20) / 20.0 # arbitrary mapping for MVP
        
        return {
            "processed_array": processed_norm.astype(np.float32),
            "metadata": {
                "normalization": "pseudo-dB-scaled",
                "clipped": True,
                "original_shape": image_array.shape
            }
        }
