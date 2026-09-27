import psutil
from typing import Dict, Any, Optional

def get_process_info(pid: int) -> Dict[str, Any]:
    """Safely retrieves process information given a PID."""
    info = {
        "process_id": pid,
        "process_name": None,
        "process_path": None,
        "parent_process_id": None,
        "parent_process_name": None
    }
    if pid is None:
        return info

    try:
        proc = psutil.Process(pid)
        info["process_name"] = proc.name()
        info["process_path"] = proc.exe()
        
        parent = proc.parent()
        if parent:
            info["parent_process_id"] = parent.pid
            info["parent_process_name"] = parent.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
    return info
