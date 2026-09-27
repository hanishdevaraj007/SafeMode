from app.models.events import FileEvent
from typing import List, Dict, Any

class RiskEngine:
    def __init__(self):
        self.recent_events: List[FileEvent] = []
        self.window_size = 5.0 # seconds
        
        self.weights = {
            "DECOY_INTERACTION": 50,
            "RAPID_MODIFICATION_BURST": 30,
            "RENAME_ACTIVITY": 20,
            "DELETION_BURST": 20
        }
        
    def analyze(self, event: FileEvent) -> Dict[str, Any]:
        self.recent_events.append(event)
        
        current_time = event.timestamp
        self.recent_events = [e for e in self.recent_events if current_time - e.timestamp <= self.window_size]
        
        score = 0
        signals = []
        event_ids = []
        
        if event.is_decoy:
            score += self.weights["DECOY_INTERACTION"]
            signals.append("DECOY_INTERACTION")
            event_ids.append(event.event_id)
            
        if event.event_type == "renamed":
            score += self.weights["RENAME_ACTIVITY"]
            signals.append("RENAME_ACTIVITY")
            event_ids.append(event.event_id)
            
        if event.event_type == "deleted":
            deletions = [e for e in self.recent_events if e.event_type == "deleted"]
            if len(deletions) >= 5:
                score += self.weights["DELETION_BURST"]
                if "DELETION_BURST" not in signals:
                    signals.append("DELETION_BURST")
                event_ids.extend([e.event_id for e in deletions])

        modifications = [e for e in self.recent_events if e.event_type == "modified"]
        if len(modifications) >= 5:
            score += self.weights["RAPID_MODIFICATION_BURST"]
            if "RAPID_MODIFICATION_BURST" not in signals:
                signals.append("RAPID_MODIFICATION_BURST")
            event_ids.extend([e.event_id for e in modifications])
            
        event_ids = list(set(event_ids))
        
        risk_level = "LOW"
        if score >= 70:
            risk_level = "HIGH"
        elif score >= 30:
            risk_level = "MEDIUM"
            
        return {
            "risk_level": risk_level,
            "score": score,
            "signals": signals,
            "evidence_event_ids": event_ids
        }
