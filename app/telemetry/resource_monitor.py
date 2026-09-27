import os
import time
import json
import threading
import psutil
from typing import Optional, List, Dict, Any
from pathlib import Path

class ResourceMonitor:
    """
    Periodic resource monitor tracking SafeMode detector process CPU, RSS memory,
    thread count, and CPU time telemetry.
    """
    def __init__(self, target_pid: Optional[int] = None, interval: float = 0.5, log_path: Optional[Path] = None):
        self.target_pid = target_pid or os.getpid()
        self.interval = interval
        self.log_path = log_path
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.samples: List[Dict[str, Any]] = []
        self._start_time = time.time()

    def start(self):
        self._running = True
        self._start_time = time.time()
        self.samples.clear()
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _monitor_loop(self):
        try:
            proc = psutil.Process(self.target_pid)
            proc.cpu_percent(interval=None)
        except Exception:
            proc = None

        while self._running:
            now = time.time()
            if proc and psutil.pid_exists(self.target_pid):
                try:
                    cpu = proc.cpu_percent(interval=None)
                    mem_info = proc.memory_info()
                    cpu_times = proc.cpu_times()
                    num_threads = proc.num_threads()
                    create_time = proc.create_time()
                    uptime = max(0.0, now - create_time)
                    
                    sample = {
                        "timestamp": now,
                        "detector_pid": self.target_pid,
                        "cpu_percent": cpu,
                        "rss_bytes": mem_info.rss,
                        "rss_mb": round(mem_info.rss / (1024 * 1024), 2),
                        "vsz_mb": round(mem_info.vms / (1024 * 1024), 2),
                        "cpu_time_user": cpu_times.user,
                        "cpu_time_system": cpu_times.system,
                        "num_threads": num_threads,
                        "uptime_seconds": round(uptime, 2)
                    }
                    self.samples.append(sample)
                    
                    if self.log_path:
                        with open(self.log_path, "a") as f:
                            f.write(json.dumps(sample) + "\n")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
            time.sleep(self.interval)

    def get_summary(self) -> Dict[str, float]:
        if not self.samples:
            return {
                "average_cpu_percent": 0.0,
                "max_cpu_percent": 0.0,
                "average_rss_mb": 0.0,
                "max_rss_mb": 0.0
            }
            
        cpus = [s["cpu_percent"] for s in self.samples]
        mems = [s["rss_mb"] for s in self.samples]
        
        return {
            "average_cpu_percent": round(sum(cpus) / len(cpus), 2),
            "max_cpu_percent": round(max(cpus), 2),
            "average_rss_mb": round(sum(mems) / len(mems), 2),
            "max_rss_mb": round(max(mems), 2)
        }
