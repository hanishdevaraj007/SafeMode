import psutil
import time
from typing import Dict, Any

class ProcessSnapshot:
    def __init__(self, update_interval: float = 2.0):
        self.update_interval = update_interval
        self.last_update = 0
        self.active_processes: Dict[int, Dict[str, Any]] = {}
        
    def refresh(self):
        now = time.time()
        if now - self.last_update < self.update_interval:
            return
            
        self.active_processes.clear()
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'ppid']):
            try:
                self.active_processes[proc.info['pid']] = {
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "exe": proc.info['exe'],
                    "ppid": proc.info['ppid'],
                    "snapshot_time": now
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self.last_update = now
        
    def get_context(self, pid: int = None) -> Dict[str, Any]:
        self.refresh()
        if pid and pid in self.active_processes:
            return {"exact_match": True, "process": self.active_processes[pid]}
        return {
            "exact_match": False, 
            "note": "Exact attribution unavailable without ETW.",
            "active_processes_count": len(self.active_processes),
            "timestamp": self.last_update
        }
