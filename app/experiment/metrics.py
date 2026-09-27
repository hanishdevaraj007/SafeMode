import json
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from pathlib import Path

@dataclass
class ExperimentOutcome:
    """
    Structured outcome representation for an individual SafeMode experiment run.
    """
    run_id: str
    scenario: str
    scenario_type: str
    detector_mode: str
    detector_version: str
    duration_seconds: float
    
    outcome: Dict[str, Any] = field(default_factory=lambda: {
        "high_confidence_reached": False,
        "first_high_confidence_time_seconds": None,
        "final_state": "IDLE",
        "max_score": 0.0,
        "decoy_interaction": False
    })
    
    files: Dict[str, int] = field(default_factory=lambda: {
        "intended": 0,
        "affected": 0
    })
    
    resource_usage: Dict[str, float] = field(default_factory=lambda: {
        "average_cpu_percent": 0.0,
        "max_cpu_percent": 0.0,
        "average_rss_mb": 0.0,
        "max_rss_mb": 0.0
    })
    
    containment: Dict[str, Any] = field(default_factory=lambda: {
        "requested": False,
        "action": None,
        "result": None
    })
    
    validity: str = "SUCCESS"  # "SUCCESS" | "FAILED" | "ABORTED" | "INVALID"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, file_path: Path):
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, file_path: Path) -> 'ExperimentOutcome':
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls(**data)


def compute_derived_metrics(outcome: ExperimentOutcome) -> Dict[str, Any]:
    """
    Derives standardized quantitative performance metrics from an experiment outcome.
    """
    scenario_type = outcome.scenario_type
    high_conf = outcome.outcome.get("high_confidence_reached", False)
    latency = outcome.outcome.get("first_high_confidence_time_seconds")
    
    # Controlled synthetic experiment labels
    is_test_positive = (scenario_type == "ATTACK_SIMULATION")
    is_test_negative = (scenario_type == "BENIGN")
    
    tp = 1 if (is_test_positive and high_conf) else 0
    fp = 1 if (is_test_negative and high_conf) else 0
    fn = 1 if (is_test_positive and not high_conf) else 0
    tn = 1 if (is_test_negative and not high_conf) else 0
    
    # Synthetic evasion workload success (avoided detection threshold during attack simulation)
    evasion_success = (is_test_positive and not high_conf)
    
    return {
        "run_id": outcome.run_id,
        "scenario": outcome.scenario,
        "scenario_type": scenario_type,
        "detector_mode": outcome.detector_mode,
        "duration_seconds": outcome.duration_seconds,
        "high_confidence_reached": high_conf,
        "detection_latency": latency if high_conf else None,
        "max_score": outcome.outcome.get("max_score", 0.0),
        "final_state": outcome.outcome.get("final_state", "IDLE"),
        "decoy_interaction": outcome.outcome.get("decoy_interaction", False),
        "files_intended": outcome.files.get("intended", 0),
        "files_affected": outcome.files.get("affected", 0),
        "synthetic_evasion_success": evasion_success,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "avg_cpu_percent": outcome.resource_usage.get("average_cpu_percent", 0.0),
        "max_cpu_percent": outcome.resource_usage.get("max_cpu_percent", 0.0),
        "avg_rss_mb": outcome.resource_usage.get("average_rss_mb", 0.0),
        "max_rss_mb": outcome.resource_usage.get("max_rss_mb", 0.0),
        "validity": outcome.validity
    }
