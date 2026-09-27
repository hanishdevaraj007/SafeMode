from pathlib import Path
from typing import List
from app.models.events import FileEvent, Signal
from app.correlation.buffer import TemporalEventBuffer

class SignalExtractor:
    def __init__(self, thresholds: dict):
        self.thresholds = thresholds
        
    def extract(self, buffer: TemporalEventBuffer) -> List[Signal]:
        signals = []
        events = buffer.get_all()
        if not events:
            return signals
            
        unique_files = buffer.get_unique_files()
        
        decoy_events = buffer.query(is_decoy=True)
        if decoy_events:
            signals.append(Signal(
                name="DECOY_INTERACTION",
                evidence_count=len(decoy_events),
                event_ids=[e.event_id for e in decoy_events]
            ))
            
        mod_events = buffer.query(event_type="modified")
        if len(mod_events) >= self.thresholds.get("RAPID_MODIFICATION_BURST_COUNT", 5):
            signals.append(Signal(
                name="RAPID_MODIFICATION_BURST",
                evidence_count=len(mod_events),
                event_ids=[e.event_id for e in mod_events]
            ))
            
        rename_events = buffer.query(event_type="renamed")
        suspicious_renames = []
        organizational_renames = []
        for e in rename_events:
            if " -> " in e.file_path:
                src, dest = e.file_path.split(" -> ", 1)
                src_ext = Path(src).suffix.lower()
                dest_ext = Path(dest).suffix.lower()
                # Extension change or append is characteristic of structural/ransomware renames
                if src_ext != dest_ext:
                    suspicious_renames.append(e)
                else:
                    organizational_renames.append(e)
            else:
                suspicious_renames.append(e)

        if len(suspicious_renames) >= self.thresholds.get("RENAME_BURST_COUNT", 3):
            signals.append(Signal(
                name="RENAME_BURST",
                evidence_count=len(suspicious_renames),
                event_ids=[e.event_id for e in suspicious_renames]
            ))
        elif len(organizational_renames) >= self.thresholds.get("RENAME_BURST_COUNT", 3):
            signals.append(Signal(
                name="ORGANIZATIONAL_RENAME_BURST",
                evidence_count=len(organizational_renames),
                event_ids=[e.event_id for e in organizational_renames]
            ))
            
        delete_events = buffer.query(event_type="deleted")
        if len(delete_events) >= self.thresholds.get("DELETE_BURST_COUNT", 3):
            signals.append(Signal(
                name="DELETE_BURST",
                evidence_count=len(delete_events),
                event_ids=[e.event_id for e in delete_events]
            ))
            
        if len(unique_files) >= self.thresholds.get("MULTI_FILE_TRANSFORMATION_COUNT", 3):
            # True multi-file transformation represents cross-file content modification combined with
            # structural operations (suspicious renames or deletions), distinguishing attacks from simple additive copying
            has_mod_and_rename = (len(mod_events) >= 3 and len(suspicious_renames) >= 2)
            has_mod_and_delete = (len(mod_events) >= 3 and len(delete_events) >= 2)
            has_rename_burst_with_mod = (len(suspicious_renames) >= 3 and len(mod_events) >= 1)
            has_heavy_suspicious_renames = (len(suspicious_renames) >= 5)
            
            if has_mod_and_rename or has_mod_and_delete or has_rename_burst_with_mod or has_heavy_suspicious_renames:
                ev_ids = [e.event_id for e in (mod_events + suspicious_renames + delete_events)]
                signals.append(Signal(
                    name="MULTI_FILE_TRANSFORMATION",
                    evidence_count=len(unique_files),
                    event_ids=ev_ids
                ))
            
        file_mod_counts = {}
        for e in mod_events:
            file_mod_counts[e.file_path] = file_mod_counts.get(e.file_path, 0) + 1
            
        repeated_events = [e for e in mod_events if file_mod_counts[e.file_path] >= self.thresholds.get("REPEATED_FILE_TRANSFORMATION_COUNT", 3)]
                
        if repeated_events:
            signals.append(Signal(
                name="REPEATED_FILE_TRANSFORMATION",
                evidence_count=len(repeated_events),
                event_ids=[e.event_id for e in repeated_events]
            ))
            
        if mod_events and (suspicious_renames or len(rename_events) >= 2) and delete_events:
            signals.append(Signal(
                name="MIXED_TRANSFORMATION_ACTIVITY",
                evidence_count=len(mod_events) + len(rename_events) + len(delete_events),
                event_ids=[e.event_id for e in (mod_events + rename_events + delete_events)]
            ))
            
        return signals
