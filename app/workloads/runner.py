import sys
import os
import json
import time
import uuid
import subprocess
import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import Config
from app.storage.logger import EventLogger
from app.telemetry.process_registry import ProcessRegistry

class WorkloadRunner:
    """
    Workload Runner capable of spawning deterministic synthetic workloads
    as genuine child subprocesses managed by SafeMode.
    """
    def __init__(self, config: Config, logger: EventLogger):
        self.config = config
        self.logger = logger
        self.workloads: Dict[str, Any] = {}
        
    def register(self, workload_class):
        name = getattr(workload_class, "name", workload_class.__name__)
        self.workloads[name] = workload_class
        self.workloads[workload_class.__name__] = workload_class
        
    def list_workloads(self):
        names = set()
        for k, v in self.workloads.items():
            names.add(getattr(v, "name", k))
        return sorted(list(names))
        
    def get_workload_class(self, name: str):
        if name in self.workloads:
            return self.workloads[name]
        for k, v in self.workloads.items():
            if getattr(v, "name", None) == name:
                return v
        return None

    def run_subprocess(
        self,
        name: str,
        registry: Optional[ProcessRegistry] = None,
        run_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        wl_class = self.get_workload_class(name)
        if not wl_class:
            self.logger.warning(f"Workload '{name}' rejected: unknown workload name.")
            return {"error": f"Unknown workload: {name}", "status": "REJECTED"}

        run_id = run_id or str(uuid.uuid4())
        params = params or {}
        
        # Security Gate: Validate lab path safety for any path parameter passed
        for k, v in params.items():
            if isinstance(v, str) and (":" in v or "/" in v or "\\" in v):
                abs_v = os.path.abspath(v)
                abs_lab = os.path.abspath(str(self.config.lab_dir))
                if not abs_v.startswith(abs_lab):
                    self.logger.warning(f"Workload parameter path violation: {v}")
                    return {"error": f"Path violation: {v}", "status": "REJECTED"}

        cmd = [
            sys.executable,
            "-m", "app", "workload",
            "--internal-exec",
            "--name", name,
            "--run-id", run_id,
            "--params", json.dumps(params)
        ]
        
        env = os.environ.copy()
        project_root = str(Path(__file__).parent.parent.parent.resolve())
        if "PYTHONPATH" in env and env["PYTHONPATH"]:
            env["PYTHONPATH"] = project_root + os.pathsep + env["PYTHONPATH"]
        else:
            env["PYTHONPATH"] = project_root
            
        start_time = time.time()
        self.logger.info(f"Spawning workload subprocess for {name} [Run ID: {run_id}]")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_root,
            env=env
        )
        
        pid = proc.pid
        parent_pid = os.getpid()
        exe_path = sys.executable
        
        try:
            ps_proc = psutil.Process(pid)
            create_time = ps_proc.create_time()
        except Exception:
            create_time = start_time
            
        scenario_type = getattr(wl_class, "scenario_type", "UNKNOWN")
        permitted_actions = ["DRY_RUN", "SUSPEND", "RESUME", "TERMINATE"]
        
        if registry:
            registry.register_subprocess(
                run_id=run_id,
                pid=pid,
                parent_pid=parent_pid,
                exe_path=exe_path,
                create_time=create_time,
                scenario=name,
                scenario_type=scenario_type,
                permitted_actions=permitted_actions,
                experiment_dir=str(self.config.lab_dir)
            )
            registry.update_status(pid, "RUNNING")
            
        return {
            "popen": proc,
            "pid": pid,
            "run_id": run_id,
            "name": name,
            "scenario_type": scenario_type,
            "start_time": start_time,
            "exe_path": exe_path,
            "create_time": create_time
        }

    def run(self, name: str, registry=None, **kwargs) -> Dict[str, Any]:
        """
        Synchronous wrapper around subprocess execution that waits for completion,
        logs results, and finalizes process registry status.
        """
        sub_info = self.run_subprocess(name=name, registry=registry, params=kwargs)
        if "error" in sub_info:
            return sub_info
            
        proc = sub_info["popen"]
        pid = sub_info["pid"]
        run_id = sub_info["run_id"]
        start_time = sub_info["start_time"]
        
        stdout, stderr = proc.communicate()
        duration = time.time() - start_time
        
        if proc.returncode == 0:
            if registry:
                registry.update_status(pid, "COMPLETED")
            self.logger.info(f"Completed workload {name} [PID: {pid}]. Duration: {duration:.2f}s")
            
            # Parse output JSON if returned from internal-exec
            res_data = {"file_count": 0}
            try:
                if stdout and "RESULT_JSON:" in stdout:
                    json_str = stdout.split("RESULT_JSON:")[1].strip()
                    res_data = json.loads(json_str)
            except Exception:
                pass

            experiment_data = {
                "run_id": run_id,
                "timestamp": start_time,
                "scenario": name,
                "scenario_type": sub_info["scenario_type"],
                "configuration": kwargs,
                "target_directory": str(self.config.lab_dir),
                "duration": duration,
                "detector_version": self.config.detector_version,
                "detection_mode": self.config.detection_mode,
                "attribution_mode": "EXPERIMENT_EXACT" if registry else "TEMPORAL_CONTEXT",
                "experiment_pid": pid,
                "exit_code": proc.returncode
            }
            self.logger.log_experiment(experiment_data)
            return {"run_id": run_id, "duration": duration, "file_count": res_data.get("file_count", 0), "pid": pid, "status": "COMPLETED"}
        else:
            if registry:
                registry.update_status(pid, "FAILED")
            self.logger.warning(f"Workload {name} failed [PID: {pid}, Exit Code: {proc.returncode}]: {stderr.strip()}")
            return {"error": stderr.strip() or f"Subprocess exited with code {proc.returncode}", "run_id": run_id, "pid": pid, "status": "FAILED"}

    def execute_internal(self, name: str, run_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoked inside the spawned child process to execute the workload code safely.
        """
        wl_class = self.get_workload_class(name)
        if not wl_class:
            raise ValueError(f"Unknown workload: {name}")
            
        wl = wl_class(self.config, run_id=run_id)
        for k, v in params.items():
            setattr(wl, k, v)

            
        res = wl.execute(**params)
        return res or {}

