from typing import Dict, Any, Tuple
from satquery.backend.ai.schemas import QueryIntent
from satquery.backend.models.registry import ModelRegistry

class ModelRouter:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        
    def route(self, intent: QueryIntent, observation_modality: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Routes the intent to a specific pipeline and model.
        Returns: (pipeline_name, model_id, routing_trace)
        """
        modality = intent.modality or observation_modality
        task = intent.task
        
        trace = {
            "query": intent.raw_query,
            "intent": task,
            "input_modality": modality,
            "fallbacks_considered": []
        }
        
        pipeline = "optical_analysis"
        if task == "CHANGE_DETECTION":
            pipeline = "change_detection"
        elif task == "MULTIMODAL_COMPARISON":
            pipeline = "multimodal_analysis"
        elif modality == "sar":
            pipeline = "sar_analysis"
            
        trace["selected_pipeline"] = pipeline
        
        # Look for heavy models first
        available_models = self.registry.find_models(modality, task)
        active_models = [m for m in available_models if m.is_available()]
        
        if active_models:
            selected_model = active_models[0].get_id()
            trace["reason"] = f"Found available heavy model for {task} and {modality}"
        else:
            selected_model = "baseline_heuristic"
            trace["fallbacks_considered"] = [m.get_id() for m in available_models]
            trace["reason"] = "No heavy models available. Falling back to deterministic baseline heuristic."
            
        trace["selected_model"] = selected_model
        return pipeline, selected_model, trace
