import argparse
import sys
import datetime
import uuid
import json

from satquery.backend.models.registry import registry
from satquery.backend.models.optical.adapters import SatMAEAdapter, SatlasPretrainAdapter
from satquery.backend.models.sar.adapters import SARMAEAdapter, SARHubAdapter
from satquery.backend.models.vlm.adapters import VLMAdapter
from satquery.backend.ai.interpreter.interpreter import QueryInterpreter
from satquery.backend.ai.router.router import ModelRouter
from satquery.backend.ai.pipelines.optical_sar import OpticalAnalysisPipeline, SARAnalysisPipeline
from satquery.backend.ai.pipelines.advanced import ChangeDetectionPipeline, MultimodalAnalysisPipeline
from satquery.backend.data.providers.local import LocalSampleProvider

# Register models (lazy init, offline by default)
registry.register(SatMAEAdapter())
registry.register(SatlasPretrainAdapter())
registry.register(SARMAEAdapter())
registry.register(SARHubAdapter())
registry.register(VLMAdapter())

def run_demo(mode: str):
    print(f"\n--- SATQUERY AI DEMO: {mode.upper()} ---")
    provider = LocalSampleProvider()
    
    # Fake observation
    fake_obs_id = str(uuid.uuid4())
    fake_obs_id_2 = str(uuid.uuid4())
    
    query = ""
    if mode == "optical":
        query = "What objects are visible in this optical image?"
        modality = "optical"
    elif mode == "sar":
        query = "Analyze this SAR image for structures."
        modality = "sar"
    elif mode == "change":
        query = "What changed between these two images?"
        modality = "optical"
    elif mode == "multimodal":
        query = "Compare the SAR and optical observations."
        modality = "optical"
    else:
        print("Unknown mode.")
        sys.exit(1)
        
    print(f"\nQUERY: '{query}'")
        
    # Acquire sample data
    now = datetime.datetime.now(datetime.timezone.utc)
    product_meta = {"id": "test", "modality": modality, "acquisition_time": now}
    image1 = provider.acquire(product_meta, fake_obs_id)
    image2 = provider.acquire(product_meta, fake_obs_id_2)
    images = [image1]
    if mode == "change":
        images.append(image2)
        
    # Interpret
    intent = QueryInterpreter.parse(query, fake_obs_id, fake_obs_id_2)
    print(f"\nINTENT: {intent.task} (Modality: {intent.modality})")
    
    # Route
    router = ModelRouter(registry)
    pipeline_name, model_id, trace = router.route(intent, modality)
    print(f"ROUTER TRACE: {json.dumps(trace, indent=2)}")
    
    # Execute Pipeline
    if pipeline_name == "optical_analysis":
        pipeline = OpticalAnalysisPipeline(registry)
    elif pipeline_name == "sar_analysis":
        pipeline = SARAnalysisPipeline(registry)
    elif pipeline_name == "change_detection":
        pipeline = ChangeDetectionPipeline(registry)
    else:
        pipeline = MultimodalAnalysisPipeline(registry)
        
    response = pipeline.execute(intent, images, trace)
    
    print("\n--- RESPONSE ---")
    print(f"Answer: {response.answer}")
    print(f"Model: {response.model}")
    print(f"Confidence: {response.confidence.value} ({response.confidence.type})")
    print(f"Evidence: {[e.type for e in response.evidence]}")

def main():
    parser = argparse.ArgumentParser(description="SatQuery AI CLI Demo")
    parser.add_argument("action", choices=["demo"], help="Action to perform")
    parser.add_argument("--mode", type=str, required=True, choices=["optical", "sar", "change", "multimodal"], help="Demo mode")
    
    args = parser.parse_args()
    
    if args.action == "demo":
        run_demo(args.mode)

if __name__ == "__main__":
    main()
