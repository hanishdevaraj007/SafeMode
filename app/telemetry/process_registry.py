import time
import os
import psutil
from typing import Dict, Any, Optional, List

class ProcessRegistry:
    """
    Stateful registry tracking SafeMode laboratory subprocesses for attribution
    and safe containment gating.
    """
    def __init__(self):
        self.registered_processes: Dict[int, Dict[str, Any]] = {}
        
    def register_subprocess(
        self,
        run_id: str,
        pid: int,
        parent_pid: int,
        exe_path: str,
        create_time: float,
        scenario: str,
        scenario_type: str = "ATTACK_SIMULATION",
        permitted_actions: Optional[List[str]] = None,
        experiment_dir: Optional[str] = None
    ):
        if permitted_actions is None:
            permitted_actions = ["DRY_RUN", "SUSPEND", "RESUME", "TERMINATE"]
            
        self.registered_processes[pid] = {
            "run_id": run_id,
            "pid": pid,
            "parent_pid": parent_pid,
            "exe_path": os.path.abspath(exe_path),
            "create_time": create_time,
            "registration_time": time.time(),
            "scenario": scenario,
            "scenario_type": scenario_type,
            "permitted_actions": permitted_actions,
            "experiment_dir": os.path.abspath(experiment_dir) if experiment_dir else "",
            "status": "REGISTERED"
        }

    def register(self, pid: int, run_id: str, exe_path: str, name: str):
        """Backward compatibility register method."""
        try:
            create_time = psutil.Process(pid).create_time()
        except Exception:
            create_time = time.time()
            
        self.register_subprocess(
            run_id=run_id,
            pid=pid,
            parent_pid=os.getppid(),
            exe_path=exe_path,
            create_time=create_time,
            scenario=name
        )
        self.update_status(pid, "RUNNING")
        
    def update_status(self, pid: int, status: str):
        valid_statuses = {"REGISTERED", "RUNNING", "SUSPENDED", "RESUMED", "COMPLETED", "TERMINATED", "FAILED"}
        if status not in valid_statuses:
            raise ValueError(f"Invalid lifecycle status: {status}")
            
        if pid in self.registered_processes:
            self.registered_processes[pid]["status"] = status
            
    def mark_terminated(self, pid: int):
        self.update_status(pid, "TERMINATED")
            
    def get(self, pid: int) -> Optional[Dict[str, Any]]:
        return self.registered_processes.get(pid)
        
    def get_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        for record in self.registered_processes.values():
            if record["run_id"] == run_id:
                return record
        return None

    def validate_identity(
        self,
        pid: int,
        expected_exe: Optional[str] = None,
        expected_create_time: Optional[float] = None
    ) -> bool:
        record = self.get(pid)
        if not record:
            return False
            
        if not psutil.pid_exists(pid):
            return False
            
        try:
            proc = psutil.Process(pid)
            if expected_exe:
                actual_exe = os.path.normpath(proc.exe().lower())
                exp_exe = os.path.normpath(expected_exe.lower())
                if actual_exe != exp_exe:
                    return False
                    
            if expected_create_time is not None:
                actual_create = proc.create_time()
                if abs(actual_create - expected_create_time) > 2.0:
                    return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
            
        return True

    def is_registered_lab_process(self, pid: int) -> bool:
        if pid not in self.registered_processes:
            return False
        record = self.registered_processes[pid]
        return record["status"] in {"REGISTERED", "RUNNING", "SUSPENDED", "RESUMED"}

