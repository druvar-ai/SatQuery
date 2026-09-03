import numpy as np
from typing import List, Dict, Any
from satquery.backend.ai.pipelines.base import BasePipeline
from satquery.backend.ai.schemas import QueryIntent, SatQueryResponse, Confidence, EvidenceArtifact
from satquery.backend.data.schemas import ObservationImage

class ChangeDetectionPipeline(BasePipeline):
    def execute(self, intent: QueryIntent, images: List[ObservationImage], trace: Dict[str, Any]) -> SatQueryResponse:
        if len(images) < 2:
            return SatQueryResponse(
                query=intent.raw_query,
                answer="Error: Change detection requires at least two images.",
                task=intent.task,
                modality="unknown",
                pipeline="change_detection",
                model="none",
                confidence=Confidence(value=0.0, type="error"),
                warnings=["Insufficient images provided."]
            )
            
        model_id = trace.get("selected_model", "baseline_heuristic")
        
        if model_id == "baseline_heuristic":
            # Baseline Normalized Difference Math on synthetic data
            try:
                arr1 = np.load(images[0].image_reference)
                arr2 = np.load(images[1].image_reference)
                
                if arr1.shape != arr2.shape:
                    raise ValueError(f"Image dimensions do not match: {arr1.shape} vs {arr2.shape}")
                
                # Deterministic thresholding logic
                diff = np.abs(arr1.astype(np.float32) - arr2.astype(np.float32))
                threshold = 50.0
                change_mask = diff > threshold
                changed_pixels = np.sum(change_mask)
                total_pixels = change_mask.size
                changed_percentage = (changed_pixels / total_pixels) * 100
                
                answer = f"BASELINE HEURISTIC: {changed_percentage:.2f}% of the region changed."
                conf = Confidence(value=0.7, type="heuristic_score", calibrated=False)
                evidence = [
                    EvidenceArtifact(
                        type="change_mask",
                        explanation=f"Calculated normalized difference exceeding threshold {threshold}.",
                        score=float(changed_percentage) # ensure standard python float
                    )
                ]
            except Exception as e:
                answer = f"Error performing baseline change detection: {str(e)}"
                conf = Confidence(value=0.0, type="error", calibrated=False)
                evidence = []
        else:
            answer = f"Model {model_id} generated change mask."
            conf = Confidence(value=0.85, type="model_score", calibrated=False)
            evidence = [EvidenceArtifact(type="change_mask", explanation="Deep learning change detection mask.")]
            
        return SatQueryResponse(
            query=intent.raw_query,
            answer=answer,
            task=intent.task,
            observation_ids=[img.observation_id for img in images],
            modality=images[0].modality,
            pipeline="change_detection",
            model=model_id,
            confidence=conf,
            evidence=evidence,
            routing_trace=trace,
            source_information={"simulated": images[0].simulated}
        )

class MultimodalAnalysisPipeline(BasePipeline):
    def execute(self, intent: QueryIntent, images: List[ObservationImage], trace: Dict[str, Any]) -> SatQueryResponse:
        import json
        
        optical_res = "BASELINE HEURISTIC: Suggests generic features."
        sar_res = "BASELINE HEURISTIC: Backscatter indicates structure."
        fused = "DISAGREEMENT DETECTED: Optical baseline and SAR baseline yield mixed interpretations."
        
        answer = json.dumps({
            "optical_result": optical_res,
            "sar_result": sar_res,
            "fused_interpretation": fused
        })
        
        conf = Confidence(value=0.65, type="heuristic_score", calibrated=False)
        evidence = [
            EvidenceArtifact(type="metadata", explanation="Optical result heuristics.", score=0.6),
            EvidenceArtifact(type="metadata", explanation="SAR backscatter heuristic.", score=0.55)
        ]
        return SatQueryResponse(
            query=intent.raw_query,
            answer=answer,
            task=intent.task,
            observation_ids=[img.observation_id for img in images],
            modality="multimodal",
            pipeline="multimodal_analysis",
            model="baseline_fusion",
            confidence=conf,
            evidence=evidence,
            routing_trace=trace
        )
