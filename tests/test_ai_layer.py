import pytest
import datetime
import uuid
from satquery.backend.models.registry import ModelRegistry
from satquery.backend.models.optical.adapters import SatMAEAdapter
from satquery.backend.ai.interpreter.interpreter import QueryInterpreter
from satquery.backend.ai.router.router import ModelRouter
from satquery.backend.ai.pipelines.optical_sar import OpticalAnalysisPipeline
from satquery.backend.ai.pipelines.advanced import ChangeDetectionPipeline
from satquery.backend.data.schemas import ObservationImage

def test_query_interpreter():
    intent = QueryInterpreter.parse("What changed in the region?", "obs-1")
    assert intent.task == "CHANGE_DETECTION"
    assert intent.observation_id == "obs-1"
    
    intent2 = QueryInterpreter.parse("What is in this SAR image?")
    assert intent2.modality == "sar"
    assert intent2.task == "SCENE_DESCRIPTION"

def test_model_registry_and_router():
    registry = ModelRegistry()
    registry.register(SatMAEAdapter())
    
    router = ModelRouter(registry)
    
    # Route optical scene description
    intent = QueryInterpreter.parse("Analyze this optical image")
    pipeline, model, trace = router.route(intent, "optical")
    
    assert pipeline == "optical_analysis"
    assert "baseline_heuristic" in model # because SatMAE returns is_available() == False
    assert trace["selected_pipeline"] == pipeline

def test_pipelines():
    registry = ModelRegistry()
    opt_pipe = OpticalAnalysisPipeline(registry)
    
    intent = QueryInterpreter.parse("Analyze optical")
    trace = {"selected_model": "baseline_heuristic", "selected_pipeline": "optical"}
    
    img = ObservationImage(
        image_id="img-1",
        observation_id="obs-1",
        source_provider="local-sample",
        modality="optical",
        image_reference="fake.npy",
        dimensions=[64,64,3],
        acquisition_time=datetime.datetime.now(datetime.timezone.utc),
        celestial_body_id="earth",
        simulated=True
    )
    
    resp = opt_pipe.execute(intent, [img], trace)
    assert resp.task == "SCENE_DESCRIPTION"
    assert resp.modality == "optical"
    assert resp.confidence.type == "heuristic_score"
    assert len(resp.evidence) > 0

def test_change_detection_numerical():
    import numpy as np
    import os
    
    # Setup
    registry = ModelRegistry()
    pipe = ChangeDetectionPipeline(registry)
    intent = QueryInterpreter.parse("What changed?")
    trace = {"selected_model": "baseline_heuristic", "selected_pipeline": "change_detection"}
    
    # Create synthetic arrays
    os.makedirs("data/test_samples", exist_ok=True)
    arr1 = np.zeros((10, 10, 1), dtype=np.uint8)
    arr2_zero = np.zeros((10, 10, 1), dtype=np.uint8)
    arr3_changed = np.zeros((10, 10, 1), dtype=np.uint8)
    arr3_changed[0:5, 0:5, 0] = 255 # 25 out of 100 pixels changed > 50
    
    np.save("data/test_samples/c1.npy", arr1)
    np.save("data/test_samples/c2.npy", arr2_zero)
    np.save("data/test_samples/c3.npy", arr3_changed)
    
    img1 = ObservationImage(image_id="1", observation_id="o1", source_provider="local-sample", modality="optical", image_reference="data/test_samples/c1.npy", dimensions=[10,10,1], acquisition_time=datetime.datetime.now(datetime.timezone.utc), celestial_body_id="earth", simulated=True)
    img2_zero = ObservationImage(image_id="2", observation_id="o2", source_provider="local-sample", modality="optical", image_reference="data/test_samples/c2.npy", dimensions=[10,10,1], acquisition_time=datetime.datetime.now(datetime.timezone.utc), celestial_body_id="earth", simulated=True)
    img3_changed = ObservationImage(image_id="3", observation_id="o3", source_provider="local-sample", modality="optical", image_reference="data/test_samples/c3.npy", dimensions=[10,10,1], acquisition_time=datetime.datetime.now(datetime.timezone.utc), celestial_body_id="earth", simulated=True)
    
    # Test 0% change
    resp_zero = pipe.execute(intent, [img1, img2_zero], trace)
    assert resp_zero.evidence[0].score == 0.0
    
    # Test >0% change (should be exactly 25.0)
    resp_changed = pipe.execute(intent, [img1, img3_changed], trace)
    assert resp_changed.evidence[0].score == 25.0
