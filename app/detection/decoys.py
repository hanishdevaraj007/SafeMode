import os
import random
import string
from pathlib import Path

class DecoyManager:
    def __init__(self, decoy_dir: Path, count: int = 10):
        self.decoy_dir = decoy_dir
        self.count = count
        self.decoy_paths = set()
        
    def _generate_random_name(self) -> str:
        name = ''.join(random.choices(string.ascii_lowercase, k=8))
        ext = random.choice(['.txt', '.docx', '.xlsx', '.pdf'])
        return name + ext

    def initialize(self):
        os.makedirs(self.decoy_dir, exist_ok=True)
        for _ in range(self.count):
            name = self._generate_random_name()
            path = self.decoy_dir / name
            with open(path, 'w') as f:
                f.write("CONFIDENTIAL DATA\n" * 10)
            self.decoy_paths.add(str(path.absolute()))
            
    def get_decoy_paths(self) -> set:
        return self.decoy_paths
