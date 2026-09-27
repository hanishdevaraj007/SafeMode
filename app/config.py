import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any

@dataclass
class Config:
    base_dir: Path = Path(os.getcwd())
    lab_dir: Path = field(init=False)
    decoy_dir: Path = field(init=False)
    data_dir: Path = field(init=False)
    telemetry_interval: float = 1.0
    correlation_window: float = 5.0
    campaign_window: float = 60.0
    response_mode: str = "CONTAIN"
    decoy_count: int = 10
    detector_version: str = "SM-AY26-FINAL-v1"
    
    detection_mode: str = "STATEFUL_MULTI_TIMESCALE" # or SHORT_WINDOW_BASELINE
    lab_mode: bool = False # Fail-safe default: must be explicitly enabled for lab experiments
    
    # Hysteresis and Decay (Bounded 0-100 scale)
    escalation_threshold: int = 80
    de_escalation_threshold: int = 40
    cooldown_period: float = 30.0
    evidence_decay_rate: float = 1.0 # score points per second
    
    signal_thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "RAPID_MODIFICATION_BURST_COUNT": 5,
        "RENAME_BURST_COUNT": 3,
        "DELETE_BURST_COUNT": 3,
        "MULTI_FILE_TRANSFORMATION_COUNT": 3,
        "REPEATED_FILE_TRANSFORMATION_COUNT": 3
    })

    def __post_init__(self):
        self.lab_dir = self.base_dir / "lab"
        self.decoy_dir = self.lab_dir / "decoys"
        self.data_dir = self.base_dir / "data"

    @classmethod
    def load(cls, path: str = None) -> 'Config':
        config = cls()
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(config, k):
                    setattr(config, k, v)
        return config
