import os
import shutil
import time
from app.workloads.base import BaseWorkload

class BenignBulkCopy(BaseWorkload):
    name = "BENIGN_BULK_COPY"
    scenario_type = "BENIGN"
    file_count = 10
    
    def execute(self, file_count=10, **kwargs):
        src_dir = self.workload_dir / "benign_src"
        dest_dir = self.workload_dir / "benign_dest"
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(dest_dir, exist_ok=True)
        
        for i in range(file_count):
            path = src_dir / f"doc_{i}.txt"
            self.check_safe_path(str(path))
            with open(path, "w") as f:
                f.write("doc data")
                
        for i in range(file_count):
            src = src_dir / f"doc_{i}.txt"
            dest = dest_dir / f"doc_{i}.txt"
            self.check_safe_path(str(dest))
            shutil.copy(str(src), str(dest))
            
        return {"file_count": file_count}

class BenignCompression(BaseWorkload):
    name = "BENIGN_COMPRESSION"
    scenario_type = "BENIGN"
    file_count = 5
    
    def execute(self, file_count=5, **kwargs):
        src_dir = self.workload_dir / "compress_src"
        os.makedirs(src_dir, exist_ok=True)
        
        for i in range(file_count):
            path = src_dir / f"doc_{i}.txt"
            self.check_safe_path(str(path))
            with open(path, "w") as f:
                f.write("doc data")
                
        archive_path = self.workload_dir / "archive.zip"
        if archive_path.exists():
            archive_path.unlink()
        self.check_safe_path(str(archive_path))
        shutil.make_archive(str(self.workload_dir / "archive"), 'zip', str(src_dir))
        return {"file_count": file_count}

class BenignDocumentEdit(BaseWorkload):
    name = "BENIGN_DOCUMENT_EDIT"
    scenario_type = "BENIGN"
    file_count = 1
    
    def execute(self, **kwargs):
        path = self.workload_dir / "editing_doc.txt"
        self.check_safe_path(str(path))
        
        with open(path, "w") as f:
            f.write("version 1")
        time.sleep(0.5)
        with open(path, "w") as f:
            f.write("version 2")
        time.sleep(0.5)
        with open(path, "w") as f:
            f.write("version 3")
            
        return {"file_count": 1}

class BenignRenameBatch(BaseWorkload):
    name = "BENIGN_RENAME_BATCH"
    scenario_type = "BENIGN"
    file_count = 10
    
    def execute(self, file_count=10, **kwargs):
        src_dir = self.workload_dir / f"rename_batch_{int(time.time()*1000)}"
        os.makedirs(src_dir, exist_ok=True)
        
        files = []
        for i in range(file_count):
            path = src_dir / f"pic_{i}.jpg"
            self.check_safe_path(str(path))
            with open(path, "w") as f:
                f.write("data")
            files.append(path)
            
        for i, path in enumerate(files):
            dest = src_dir / f"vacation_{i}.jpg"
            os.rename(str(path), str(dest))
            
        return {"file_count": file_count}

class BenignBackupStyle(BaseWorkload):
    name = "BENIGN_BACKUP_STYLE"
    scenario_type = "BENIGN"
    file_count = 10
    
    def execute(self, file_count=10, **kwargs):
        ts = int(time.time() * 1000)
        src_dir = self.workload_dir / f"backup_src_{ts}"
        dest_dir = self.workload_dir / f"backup_dest_{ts}"
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(dest_dir, exist_ok=True)
        
        for i in range(file_count):
            path = src_dir / f"doc_{i}.txt"
            self.check_safe_path(str(path))
            with open(path, "w") as f:
                f.write("data")
                
        time.sleep(0.2)
        for i in range(file_count):
            temp_dest = dest_dir / f"doc_{i}.txt.tmp"
            final_dest = dest_dir / f"doc_{i}.txt"
            self.check_safe_path(str(temp_dest))
            self.check_safe_path(str(final_dest))
            shutil.copy(str(src_dir / f"doc_{i}.txt"), str(temp_dest))
            os.rename(str(temp_dest), str(final_dest))
            
        return {"file_count": file_count}




