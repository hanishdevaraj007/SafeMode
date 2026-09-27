from app.models.events import Signal, Decision, CampaignState
from app.correlation.buffer import TemporalEventBuffer
from typing import List, Dict, Any

class CorrelationEngine:
    def __init__(self, window_seconds: float):
        self.window_seconds = window_seconds

    def evaluate(self, signals: List[Signal], buffer: TemporalEventBuffer, process_context: Dict[str, Any], detection_mode: str = "SHORT_WINDOW_BASELINE", state: CampaignState = None) -> Decision:
        decision = Decision(window_seconds=self.window_seconds)
        decision.signals = signals
        decision.process_context = process_context
        decision.detection_mode = detection_mode
        
        all_event_ids = set()
        for s in signals:
            all_event_ids.update(s.event_ids)
        decision.affected_file_count = len(all_event_ids)
        
        if detection_mode == "SHORT_WINDOW_BASELINE":
            names = [s.name for s in signals]
            if "DECOY_INTERACTION" in names and "MULTI_FILE_TRANSFORMATION" in names:
                decision.risk_level = "HIGH"
                decision.score = 90.0
                decision.explanation = "Decoy interaction combined with multiple file transformations."
            elif "DECOY_INTERACTION" in names and "RENAME_BURST" in names:
                decision.risk_level = "HIGH"
                decision.score = 85.0
                decision.explanation = "Decoy interaction combined with rapid renames."
            elif "MULTI_FILE_TRANSFORMATION" in names and "RENAME_BURST" in names:
                decision.risk_level = "MEDIUM"
                decision.score = 75.0
                decision.explanation = "Multiple files transformed and renamed in a burst."
            elif "MIXED_TRANSFORMATION_ACTIVITY" in names and "RAPID_MODIFICATION_BURST" in names:
                decision.risk_level = "MEDIUM"
                decision.score = 70.0
                decision.explanation = "Mixed transformation activity with rapid modification burst."
            elif "DECOY_INTERACTION" in names:
                decision.risk_level = "MEDIUM"
                decision.score = 50.0
                decision.explanation = "Isolated decoy interaction."
            elif "RENAME_BURST" in names:
                decision.risk_level = "LOW"
                decision.score = 25.0
                decision.explanation = "Isolated suspicious rename burst."
            elif "ORGANIZATIONAL_RENAME_BURST" in names:
                decision.risk_level = "LOW"
                decision.score = 10.0
                decision.explanation = "Isolated organizational rename burst (benign)."
            elif "RAPID_MODIFICATION_BURST" in names:

                decision.risk_level = "LOW"
                decision.score = 20.0
                decision.explanation = "Isolated rapid modification burst (potentially benign)."
            else:
                decision.risk_level = "LOW"
                decision.score = 0.0
                
        elif detection_mode == "STATEFUL_MULTI_TIMESCALE":
            if not state:
                return decision
                
            decision.score = round(min(100.0, max(0.0, state.accumulated_score)), 2)
            decision.affected_file_count = len(state.affected_files)
            
            # Strict invariant mapping: score >= 80 <=> HIGH risk
            if state.status in ["HIGH_CONFIDENCE", "CONTAINMENT_PENDING", "CONTAINED"] or decision.score >= 80.0:
                decision.risk_level = "HIGH"
            elif state.status == "SUSPICIOUS" or decision.score >= 40.0:
                decision.risk_level = "MEDIUM"
            else:
                decision.risk_level = "LOW"
                
            duration = max(0.1, state.last_event_time - state.first_event_time)
            
            explanations = []
            if state.status != "IDLE":
                explanations.append(f"Suspicious activity accumulated across behavioral bursts over {duration:.1f} seconds.")
                explanations.append(f"The campaign modified {len(state.affected_files)} unique files.")
                
                if state.renames > 0:
                    explanations.append(f"Produced rename activity ({state.renames} renames).")
                    
                if state.decoy_interactions > 0:
                    explanations.append(f"Observed {state.decoy_interactions} decoy interactions.")
                else:
                    explanations.append("No decoy interaction was observed.")
                    
                decision.explanation = " ".join(explanations)
                
        return decision
