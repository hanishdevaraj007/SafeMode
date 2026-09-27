import pytest
from app.config import Config
from app.workloads.adversarial import FastTransformation
from app.workloads.benign import BenignBulkCopy
from app.workloads.runner import WorkloadRunner
from app.storage.logger import EventLogger

def test_workload_safe_path(tmp_path):
    config = Config()
    config.base_dir = tmp_path
    config.lab_dir = tmp_path / "lab"
    
    logger = EventLogger(tmp_path / "logs")
    runner = WorkloadRunner(config, logger)
    runner.register(FastTransformation)
    
    result = runner.run("FastTransformation", file_count=2)
    assert "error" not in result
    assert result["file_count"] == 2

def test_workload_benign(tmp_path):
    config = Config()
    config.base_dir = tmp_path
    config.lab_dir = tmp_path / "lab"
    
    logger = EventLogger(tmp_path / "logs")
    runner = WorkloadRunner(config, logger)
    runner.register(BenignBulkCopy)
    
    result = runner.run("BenignBulkCopy", file_count=2)
    assert "error" not in result
    assert result["file_count"] == 2
