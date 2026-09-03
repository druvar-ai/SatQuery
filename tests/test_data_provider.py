import os
import datetime
import numpy as np
from satquery.backend.data.providers.local import LocalSampleProvider
from satquery.backend.data.providers.sentinel import Sentinel1Provider, Sentinel2Provider
from satquery.backend.data.preprocessing import OpticalPreprocessor, SARPreprocessor

def test_local_provider():
    provider = LocalSampleProvider(data_dir="data/test_samples")
    assert provider.is_available() == True
    
    now = datetime.datetime.now(datetime.timezone.utc)
    results = provider.search(0.0, 0.0, now, now, modality="optical")
    
    assert len(results) == 1
    assert results[0]["modality"] == "optical"
    
    img = provider.acquire(results[0], "obs-123")
    assert img.modality == "optical"
    assert img.simulated == True
    assert os.path.exists(img.image_reference)
    
def test_sentinel_providers():
    s1 = Sentinel1Provider()
    s2 = Sentinel2Provider()
    
    # MVP expects these to be gracefully unavailable
    assert s1.is_available() == False
    assert s2.is_available() == False
    assert len(s1.search(0.0, 0.0, datetime.datetime.now(), datetime.datetime.now())) == 0

def test_preprocessing():
    arr = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    
    opt = OpticalPreprocessor.process(arr)
    assert opt["processed_array"].dtype == np.float32
    assert opt["processed_array"].max() <= 1.0
    
    sar = SARPreprocessor.process(arr[:,:,0])
    assert sar["processed_array"].dtype == np.float32
