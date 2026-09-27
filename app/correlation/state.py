import time
from typing import List, Dict, Any, Set, Tuple
from app.models.events import CampaignState, Signal
from app.config import Config
from app.storage.logger import EventLogger

class CampaignMemory:
    """
    Multi-timescale campaign memory tracking cumulative behavioral evidence
    across temporal bursts with bounded risk scoring (0-100), exponential decay,
    evidence deduplication, and escalation/de-escalation hysteresis.
    """
    def __init__(self, config: Config, logger: EventLogger):
        self.config = config
        self.logger = logger
        self.state = CampaignState()
        # Evidence accounting: stores (signal_name, frozenset(event_ids))
        self.processed_evidence_keys: Set[Tuple[str, frozenset]] = set()
        
    def _decay_score(self, current_time: float):
        if self.state.status == "IDLE" or self.state.last_event_time == 0.0:
            return
            
        elapsed = current_time - self.state.last_event_time
        if elapsed > self.config.cooldown_period:
            self.logger.info(f"Campaign cooldown expired ({elapsed:.1f}s > {self.config.cooldown_period}s). Resetting state from {self.state.status} to IDLE.")
            self.reset()
            return
            
        decay_amount = elapsed * self.config.evidence_decay_rate
        new_score = max(0.0, self.state.accumulated_score - decay_amount)
        self.state.accumulated_score = round(new_score, 2)
        
    def update(self, signals: List[Signal], current_time: float) -> CampaignState:
        # 1. Apply decay since last event
        self._decay_score(current_time)
        
        if not signals:
            return self.state
            
        new_contributions = 0.0
        has_new_evidence = False
        
        # 2. Evidence accounting: only evaluate signals containing NEW evidence
        for s in signals:
            if not s.event_ids:
                continue
                
            evidence_key = (s.name, frozenset(s.event_ids))
            if evidence_key in self.processed_evidence_keys:
                continue # Skip already-accounted evidence
                
            self.processed_evidence_keys.add(evidence_key)
            has_new_evidence = True
            self.state.signals_history.append(s.name)
            self.state.event_ids.update(s.event_ids)
            
            # Bounded signal contributions (Scale: 0-100)
            if s.name == "DECOY_INTERACTION":
                new_contributions += 45.0
                self.state.decoy_interactions += s.evidence_count
            elif s.name == "MULTI_FILE_TRANSFORMATION":
                new_contributions += 30.0
                self.state.modifications += s.evidence_count
            elif s.name == "MIXED_TRANSFORMATION_ACTIVITY":
                new_contributions += 30.0
            elif s.name == "RENAME_BURST":
                new_contributions += 25.0
                self.state.renames += s.evidence_count
            elif s.name == "ORGANIZATIONAL_RENAME_BURST":
                new_contributions += 10.0
                self.state.renames += s.evidence_count
            elif s.name == "DELETE_BURST":
                new_contributions += 25.0
                self.state.deletions += s.evidence_count
            elif s.name in ["RAPID_MODIFICATION_BURST", "REPEATED_FILE_TRANSFORMATION"]:
                new_contributions += 15.0
                self.state.modifications += s.evidence_count


        if has_new_evidence:
            if self.state.status == "IDLE":
                self.state.status = "OBSERVING"
                self.state.first_event_time = current_time
                self.logger.log_state_transition(self.state.to_dict())
                
            self.state.last_event_time = current_time
            # Clamp strictly to [0.0, 100.0]
            raw_score = self.state.accumulated_score + new_contributions
            self.state.accumulated_score = round(min(100.0, max(0.0, raw_score)), 2)
            
        # 3. State transitions with hysteresis
        prev_status = self.state.status
        if self.state.accumulated_score >= self.config.escalation_threshold:
            if self.state.status not in ["CONTAINMENT_PENDING", "CONTAINED"]:
                self.state.status = "HIGH_CONFIDENCE"
        elif self.state.accumulated_score >= self.config.de_escalation_threshold:
            if self.state.status not in ["CONTAINMENT_PENDING", "CONTAINED", "HIGH_CONFIDENCE"]:
                self.state.status = "SUSPICIOUS"
        elif self.state.accumulated_score < self.config.de_escalation_threshold:
            if self.state.status == "SUSPICIOUS":
                self.state.status = "OBSERVING"
                
        if prev_status != self.state.status:
            self.logger.log_state_transition(self.state.to_dict())
            
        return self.state
        
    def set_containment_pending(self):
        self.state.status = "CONTAINMENT_PENDING"
        self.logger.log_state_transition(self.state.to_dict())
        
    def reset(self):
        old_id = self.state.state_id
        self.state = CampaignState()
        self.processed_evidence_keys.clear()
        self.logger.log_state_transition({"action": "RESET", "previous_state_id": old_id})

