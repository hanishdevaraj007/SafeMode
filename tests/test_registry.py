import pytest
import os
import psutil
from app.telemetry.process_registry import ProcessRegistry
from app.response.actions import ResponseManager
from app.config import Config
from app.storage.logger import EventLogger

def test_registry_registration():
    registry = ProcessRegistry()
    registry.register(1234, "run_id", "/path/to/exe", "test.exe")
    
    assert registry.is_registered_lab_process(1234)
    assert not registry.is_registered_lab_process(9999)
    
    registry.mark_terminated(1234)
    assert not registry.is_registered_lab_process(1234)

def test_containment_safety(tmp_path):
    config = Config()
    config.lab_mode = True
    logger = EventLogger(tmp_path / "logs")
    registry = ProcessRegistry()
    response = ResponseManager(config, logger, registry)
    
    # 1. Unregistered PID
    audit = response.execute_containment(9999, "DRY_RUN")
    assert audit["action_result"] in ["FAILED", "REFUSED"]
    assert "not registered" in audit["reason"] or "Check 2 Failed" in audit["reason"]
    
    # 2. Registered PID
    pid = os.getpid()
    proc = psutil.Process(pid)
    registry.register_subprocess(
        run_id="test_run",
        pid=pid,
        parent_pid=os.getppid(),
        exe_path=proc.exe(),
        create_time=proc.create_time(),
        scenario="FAST_TRANSFORMATION",
        experiment_dir=str(config.lab_dir)
    )
    registry.update_status(pid, "RUNNING")
    
    audit = response.execute_containment(pid, "DRY_RUN")
    assert audit["action_result"] == "SUCCESS"
    assert audit["target_verified"] == True
    
    # Verify refusal when LAB_MODE=False
    config.lab_mode = False
    audit2 = response.execute_containment(pid, "TERMINATE")
    assert audit2["action_result"] in ["FAILED", "REFUSED"]

