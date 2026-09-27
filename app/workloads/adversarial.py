import os
import time
from pathlib import Path
from app.workloads.base import BaseWorkload

class AdversarialWorkload(BaseWorkload):
    def _create_files(self, count: int) -> list:
        os.makedirs(self.workload_dir, exist_ok=True)
        files = []
        for i in range(count):
            path = self.workload_dir / f"victim_{self.name}_{i}.txt"
            self.check_safe_path(str(path))
            enc_path = path.with_suffix(".encrypted")
            locked_path = path.with_suffix(".locked")
            enc2_path = path.with_suffix(".enc")
            for p in [path, enc_path, locked_path, enc2_path]:
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass
            with open(path, "w") as f:
                f.write("original data")
            files.append(path)
        return files
        
    def _modify_file(self, path: Path):
        self.check_safe_path(str(path))
        with open(path, "w") as f:
            f.write("encrypted data")
            
    def _rename_file(self, old_path: Path, new_path: Path):
        self.check_safe_path(str(old_path))
        self.check_safe_path(str(new_path))
        if new_path.exists():
            try:
                new_path.unlink()
            except Exception:
                pass
        os.rename(str(old_path), str(new_path))

class FastTransformation(AdversarialWorkload):
    name = "FAST_TRANSFORMATION"
    scenario_type = "ATTACK_SIMULATION"
    file_count = 10
    
    def execute(self, **kwargs):
        files = self._create_files(self.file_count)
        for f in files:
            self._modify_file(f)
        for f in files:
            self._rename_file(f, f.with_suffix(".encrypted"))
        return {"file_count": self.file_count}

class SlowTransformation(AdversarialWorkload):
    name = "SLOW_TRANSFORMATION"
    scenario_type = "ATTACK_SIMULATION"
    burst_size = 2
    delay = 8.0
    bursts = 5
    
    def execute(self, **kwargs):
        files = self._create_files(self.bursts * self.burst_size)
        idx = 0
        for b in range(self.bursts):
            for i in range(self.burst_size):
                if idx < len(files):
                    f = files[idx]
                    self._modify_file(f)
                    self._rename_file(f, f.with_suffix(".encrypted"))
                    idx += 1
            if b < self.bursts - 1:
                time.sleep(self.delay)
        return {"file_count": len(files)}

class IntermittentTransformation(AdversarialWorkload):
    name = "INTERMITTENT_TRANSFORMATION"
    scenario_type = "ATTACK_SIMULATION"
    burst_size = 3
    delay = 6.0
    bursts = 4
    
    def execute(self, **kwargs):
        files = self._create_files(self.bursts * self.burst_size)
        idx = 0
        for b in range(self.bursts):
            for i in range(self.burst_size):
                if idx < len(files):
                    f = files[idx]
                    self._modify_file(f)
                    self._rename_file(f, f.with_suffix(".locked"))
                    idx += 1
            if b < self.bursts - 1:
                time.sleep(self.delay)
        return {"file_count": len(files)}

class RenameHeavy(AdversarialWorkload):
    name = "RENAME_HEAVY"
    scenario_type = "ATTACK_SIMULATION"
    file_count = 15
    
    def execute(self, **kwargs):
        files = self._create_files(self.file_count)
        for f in files:
            self._rename_file(f, f.with_suffix(".encrypted"))
        return {"file_count": self.file_count}
            
class DecoyAvoidance(AdversarialWorkload):
    name = "DECOY_AVOIDANCE"
    scenario_type = "ATTACK_SIMULATION"
    file_count = 5
    
    def execute(self, **kwargs):
        safe_dir = self.workload_dir / "protected"
        os.makedirs(safe_dir, exist_ok=True)
        files = [safe_dir / f"test_{i}.txt" for i in range(self.file_count)]
        for f in files:
            self.check_safe_path(str(f))
            with open(f, "w") as fp:
                fp.write("safe")
        for f in files:
            self._modify_file(f)
            self._rename_file(f, f.with_suffix(".encrypted"))
        return {"file_count": self.file_count}

class MixedBehavior(AdversarialWorkload):
    name = "MIXED_BEHAVIOR"
    scenario_type = "ATTACK_SIMULATION"
    file_count = 10
    
    def execute(self, **kwargs):
        files = self._create_files(self.file_count)
        for i, f in enumerate(files):
            if i % 3 == 0:
                self.check_safe_path(str(f))
                f.unlink()
            elif i % 3 == 1:
                self._modify_file(f)
            else:
                self._rename_file(f, f.with_suffix(".enc"))
        return {"file_count": self.file_count}
