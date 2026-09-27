import os
import time
import uuid
import psutil
from typing import Any, Optional, Dict
from app.config import Config
from app.storage.logger import EventLogger
from app.telemetry.process_registry import ProcessRegistry

class ResponseManager:
    """
    Response Manager responsible for enforcing safe containment policies
    against registered SafeMode subprocesses.
    """
    def __init__(self, config: Config, logger: EventLogger, registry: ProcessRegistry):
        self.config = config
        self.logger = logger
        self.registry = registry
        
    def handle(self, assessment: dict):
        if self.config.response_mode == "MONITOR":
            pass 
        elif self.config.response_mode == "ALERT":
            self.logger.warning(f"[ALERT] Risk level {assessment.get('risk_level')}: {assessment.get('explanation')}")
        elif self.config.response_mode == "CONTAIN":
            self.logger.warning(f"[CONTAIN] Action requested for risk level {assessment.get('risk_level')}")
            ctx = assessment.get("process_context", {})
            pid = ctx.get("experiment_pid")
            run_id = ctx.get("run_id")
            
            target_identity = pid or run_id
            if target_identity:
                self.execute_containment(target_identity, "DRY_RUN", decision_id=assessment.get("decision_id"), run_id=run_id)
            else:
                self.logger.warning("[CONTAIN] Refused: No exact experiment PID or Run ID available.")

    def execute_containment(
        self,
        target_identity: Any,
        action: str,
        decision_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a containment action after passing 10 mandatory security checks.
        Never falls back to PID-only unverified containment.
        """
        audit = {
            "response_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "requested_identity": str(target_identity),
            "requested_action": action,
            "run_id": run_id,
            "decision_id": decision_id,
            "checks": {},
            "target_verified": False,
            "lab_mode": self.config.lab_mode,
            "action_result": "REFUSED",
            "reason": ""
        }
        
        # Check 1: Verify LAB_MODE
        if not self.config.lab_mode:
            audit["checks"]["lab_mode"] = False
            audit["reason"] = "Check 1 Failed: LAB_MODE is False. Containment refused."
            self.logger.log_containment(audit)
            return audit
        audit["checks"]["lab_mode"] = True
        
        # Resolve PID & registry record from target_identity
        pid = None
        proc_record = None
        if isinstance(target_identity, int):
            pid = target_identity
            proc_record = self.registry.get(pid)
        elif isinstance(target_identity, str):
            proc_record = self.registry.get_by_run_id(target_identity)
            if proc_record:
                pid = proc_record["pid"]
            elif target_identity.isdigit():
                pid = int(target_identity)
                proc_record = self.registry.get(pid)
        elif isinstance(target_identity, dict):
            pid = target_identity.get("pid")
            run_id = target_identity.get("run_id") or run_id
            proc_record = self.registry.get(pid) if pid else (self.registry.get_by_run_id(run_id) if run_id else None)
            if proc_record and not pid:
                pid = proc_record["pid"]

        # Check 2: Retrieve registry record
        if not proc_record or not pid:
            audit["checks"]["registry_record"] = False
            audit["reason"] = f"Check 2 Failed: Target process identity '{target_identity}' is not registered in SafeMode process registry."
            self.logger.log_containment(audit)
            return audit
        audit["checks"]["registry_record"] = True
        audit["target_pid"] = pid
        audit["run_id"] = audit["run_id"] or proc_record.get("run_id")
        
        # Check 3: Confirm PID is still running
        if not psutil.pid_exists(pid):
            audit["checks"]["pid_running"] = False
            audit["reason"] = f"Check 3 Failed: Target PID {pid} is no longer running in OS."
            self.registry.update_status(pid, "TERMINATED")
            self.logger.log_containment(audit)
            return audit
        audit["checks"]["pid_running"] = True
        
        try:
            proc = psutil.Process(pid)
        except psutil.NoSuchProcess:
            audit["checks"]["pid_running"] = False
            audit["reason"] = f"Check 3 Failed: Target PID {pid} no longer exists."
            self.registry.update_status(pid, "TERMINATED")
            self.logger.log_containment(audit)
            return audit

        # Check 4: Verify executable identity
        reg_exe = os.path.normpath(proc_record.get("exe_path", "").lower())
        try:
            actual_exe = os.path.normpath(proc.exe().lower())
            if reg_exe and actual_exe != reg_exe:
                audit["checks"]["executable_identity"] = False
                audit["reason"] = f"Check 4 Failed: Executable identity mismatch. Expected {reg_exe}, got {actual_exe}."
                self.logger.log_containment(audit)
                return audit
        except Exception as e:
            audit["checks"]["executable_identity"] = False
            audit["reason"] = f"Check 4 Failed: Could not verify process executable path: {str(e)}"
            self.logger.log_containment(audit)
            return audit
        audit["checks"]["executable_identity"] = True
        
        # Check 5: Verify process start time where available
        reg_create_time = proc_record.get("create_time")
        if reg_create_time:
            try:
                actual_create_time = proc.create_time()
                if abs(actual_create_time - reg_create_time) > 2.0:
                    audit["checks"]["start_time"] = False
                    audit["reason"] = f"Check 5 Failed: Start time mismatch. Expected {reg_create_time}, got {actual_create_time}."
                    self.logger.log_containment(audit)
                    return audit
            except Exception:
                pass
        audit["checks"]["start_time"] = True

        # Check 6: Verify run is active
        current_status = proc_record.get("status", "")
        if current_status not in ["REGISTERED", "RUNNING", "SUSPENDED", "RESUMED"]:
            audit["checks"]["run_active"] = False
            audit["reason"] = f"Check 6 Failed: Experiment process state '{current_status}' is not active."
            self.logger.log_containment(audit)
            return audit
        audit["checks"]["run_active"] = True

        # Check 7: Verify process belongs to a known workload
        scenario = proc_record.get("scenario")
        if not scenario:
            audit["checks"]["known_workload"] = False
            audit["reason"] = "Check 7 Failed: Process does not belong to a registered scenario."
            self.logger.log_containment(audit)
            return audit
        audit["checks"]["known_workload"] = True

        # Check 8: Verify target directory is inside permitted lab workload directory
        exp_dir = proc_record.get("experiment_dir", str(self.config.lab_dir))
        abs_exp = os.path.abspath(exp_dir)
        abs_lab = os.path.abspath(str(self.config.lab_dir))
        if not abs_exp.startswith(abs_lab):
            audit["checks"]["permitted_directory"] = False
            audit["reason"] = f"Check 8 Failed: Experiment directory '{abs_exp}' outside lab directory '{abs_lab}'."
            self.logger.log_containment(audit)
            return audit
        audit["checks"]["permitted_directory"] = True

        # Check 9: Verify action is permitted for that experiment
        permitted_actions = proc_record.get("permitted_actions", ["DRY_RUN", "SUSPEND", "RESUME", "TERMINATE"])
        if action not in permitted_actions:
            audit["checks"]["action_permitted"] = False
            audit["reason"] = f"Check 9 Failed: Action '{action}' not permitted for experiment (permitted: {permitted_actions})."
            self.logger.log_containment(audit)
            return audit
        audit["checks"]["action_permitted"] = True

        # Check 10: Record all checks before action
        audit["checks"]["all_checks_passed"] = True
        audit["target_verified"] = True
        audit["target_process"] = scenario
        
        # Execute containment action
        try:
            if action == "DRY_RUN":
                audit["action_result"] = "SUCCESS"
                audit["reason"] = "Dry run containment check passed successfully."
            elif action == "SUSPEND":
                proc.suspend()
                self.registry.update_status(pid, "SUSPENDED")
                audit["action_result"] = "SUCCESS"
                audit["reason"] = f"Process {pid} suspended successfully."
            elif action == "RESUME":
                proc.resume()
                self.registry.update_status(pid, "RESUMED")
                audit["action_result"] = "SUCCESS"
                audit["reason"] = f"Process {pid} resumed successfully."
            elif action == "TERMINATE":
                proc.terminate()
                self.registry.update_status(pid, "TERMINATED")
                audit["action_result"] = "SUCCESS"
                audit["reason"] = f"Process {pid} terminated successfully."
            else:
                audit["action_result"] = "FAILED"
                audit["reason"] = f"Unknown action: {action}"
        except Exception as e:
            audit["action_result"] = "FAILED"
            audit["reason"] = f"Action execution exception: {str(e)}"
            
        self.logger.log_containment(audit)
        return audit

