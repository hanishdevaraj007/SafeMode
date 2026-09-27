import platform
import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from pathlib import Path

@dataclass
class ExperimentManifest:
    """
    Formal machine-readable manifest recording complete metadata and parameters
    for a reproducible SafeMode experiment run.
    """
    run_id: str
    scenario: str
    scenario_type: str  # "ATTACK_SIMULATION" | "BENIGN"
    detector_mode: str  # "SHORT_WINDOW_BASELINE" | "STATEFUL_MULTI_TIMESCALE"
    detector_version: str
    configuration_version: str = "v1.0"
    random_seed: int = 42
    workload_parameters: Dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    target_directory: str = ""
    number_of_files_intended: int = 0
    number_of_files_affected: int = 0
    workload_pid: Optional[int] = None
    process_executable: str = ""
    containment_policy: str = "DRY_RUN"
    host_info: Dict[str, str] = field(default_factory=lambda: {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python_version": platform.python_version()
    })
    result_file_paths: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, file_path: Path):
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, file_path: Path) -> 'ExperimentManifest':
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls(**data)
