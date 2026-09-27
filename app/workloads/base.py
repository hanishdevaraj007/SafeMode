import os
import shutil
from abc import ABC, abstractmethod
from app.config import Config
from app.utils.paths import validate_safe_lab_path

class BaseWorkload(ABC):
    name = "BASE"
    scenario_type = "BENIGN"
    
    def __init__(self, config: Config, run_id: str = None):
        self.config = config
        self.run_id = run_id
        self.workload_dir = self.config.lab_dir / "workloads"
        validate_safe_lab_path(str(self.workload_dir), self.config.lab_dir)
        os.makedirs(self.workload_dir, exist_ok=True)



        
    def check_safe_path(self, path: str):
        validate_safe_lab_path(path, self.config.lab_dir)

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        pass

