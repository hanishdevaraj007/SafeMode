import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

@dataclass
class FileEvent:
    event_type: str
    file_path: str
    timestamp: float = field(default_factory=time.time)
    process_id: Optional[int] = None
    process_name: Optional[str] = None
    process_path: Optional[str] = None
    parent_process_id: Optional[int] = None
    parent_process_name: Optional[str] = None
    file_extension: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "filesystem"
    is_decoy: bool = False

    def __post_init__(self):
        self.file_extension = ""
        if "." in self.file_path:
            self.file_extension = self.file_path.rsplit(".", 1)[-1]

    def to_dict(self):
        return asdict(self)

@dataclass
class Signal:
    name: str
    evidence_count: int
    event_ids: List[str]
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Decision:
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    risk_level: str = "LOW"
    score: float = 0.0
    window_seconds: float = 5.0
    affected_file_count: int = 0
    signals: List[Signal] = field(default_factory=list)
    process_context: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""
    detection_mode: str = "SHORT_WINDOW_BASELINE"
    
    def to_dict(self):
        d = asdict(self)
        d['signals'] = [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.signals]
        return d

@dataclass
class CampaignState:
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "IDLE"
    first_event_time: float = 0.0
    last_event_time: float = 0.0
    affected_files: set = field(default_factory=set)
    modifications: int = 0
    renames: int = 0
    deletions: int = 0
    decoy_interactions: int = 0
    signals_history: List[str] = field(default_factory=list)
    event_ids: set = field(default_factory=set)
    accumulated_score: float = 0.0
    
    def to_dict(self):
        d = asdict(self)
        d['affected_files'] = list(self.affected_files)
        d['event_ids'] = list(self.event_ids)
        return d
