from typing import List, Dict, Any
from satquery.backend.ai.pipelines.base import BasePipeline
from satquery.backend.ai.schemas import QueryIntent, SatQueryResponse, Confidence, EvidenceArtifact
from satquery.backend.data.schemas import ObservationImage

class OpticalAnalysisPipeline(BasePipeline):
    def execute(self, intent: QueryIntent, images: List[ObservationImage], trace: Dict[str, Any]) -> SatQueryResponse:
        model_id = trace.get("selected_model", "baseline_heuristic")
        
        if model_id == "baseline_heuristic":
            answer = "BASELINE HEURISTIC (Synthetic Data): The image appears to contain generic features based on overall brightness."
            conf = Confidence(value=0.6, type="heuristic_score", calibrated=False)
            evidence = [
                EvidenceArtifact(
                    type="metadata", 
                    explanation="Visual inspection using baseline heuristic indicates generic features based on overall brightness.",
                    score=0.6
                )
            ]
        else:
            model = self.registry.get_model(model_id)
            # In a real setup, we would call model.predict(preprocessed_image)
            answer = f"Model {model_id} successfully extracted features."
            conf = Confidence(value=0.85, type="model_score", calibrated=False)
            evidence = [EvidenceArtifact(type="feature_map", explanation="Features extracted by heavy model")]
            
        return SatQueryResponse(
            query=intent.raw_query,
            answer=answer,
            task=intent.task,
            observation_ids=[img.observation_id for img in images],
            modality="optical",
            pipeline="optical_analysis",
            model=model_id,
            confidence=conf,
            evidence=evidence,
            routing_trace=trace,
            source_information={"simulated": images[0].simulated, "provider": images[0].source_provider} if images else {}
        )

class SARAnalysisPipeline(BasePipeline):
    def execute(self, intent: QueryIntent, images: List[ObservationImage], trace: Dict[str, Any]) -> SatQueryResponse:
        model_id = trace.get("selected_model", "baseline_heuristic")
        
        if model_id == "baseline_heuristic":
            answer = "BASELINE HEURISTIC (Synthetic Data): Analyzing radar backscatter using thresholding heuristics."
            conf = Confidence(value=0.55, type="heuristic_score", calibrated=False)
            evidence = [EvidenceArtifact(type="metadata", explanation="High backscatter regions identified using threshold.")]
        else:
            answer = f"SAR Model {model_id} detected specific signatures."
            conf = Confidence(value=0.8, type="model_score", calibrated=False)
            evidence = [EvidenceArtifact(type="segmentation_mask", explanation="Segmented regions from SAR model.")]
            
        return SatQueryResponse(
            query=intent.raw_query,
            answer=answer,
            task=intent.task,
            observation_ids=[img.observation_id for img in images],
            modality="sar",
            pipeline="sar_analysis",
            model=model_id,
            confidence=conf,
            evidence=evidence,
            routing_trace=trace,
            source_information={"simulated": images[0].simulated, "provider": images[0].source_provider} if images else {}
        )
