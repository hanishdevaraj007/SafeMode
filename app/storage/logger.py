import json
import logging
import os
from pathlib import Path
from typing import Optional

class EventLogger:
    """
    Structured logger that writes JSONL event traces and decision audits
    both globally and to run-specific experiment files.
    """
    def __init__(self, log_dir: Path, run_id: Optional[str] = None):
        self.log_dir = Path(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        self.run_id = run_id
        
        self.events_file = self.log_dir / "events.jsonl"
        self.decisions_file = self.log_dir / "decisions.jsonl"
        self.experiments_file = self.log_dir / "experiments.jsonl"
        self.containment_file = self.log_dir / "containment.jsonl"
        self.state_file = self.log_dir / "state.jsonl"
        
        self.console = logging.getLogger("SafeMode")
        self.console.setLevel(logging.INFO)
        if not self.console.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.console.addHandler(handler)

    def set_run_id(self, run_id: str):
        self.run_id = run_id

    def log_event(self, event_dict: dict):
        if self.run_id and "run_id" not in event_dict:
            event_dict["run_id"] = self.run_id
            
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event_dict) + "\n")
            
        if self.run_id:
            run_events_path = self.log_dir / f"{self.run_id}_events.jsonl"
            with open(run_events_path, "a") as f:
                f.write(json.dumps(event_dict) + "\n")
            
    def log_decision(self, decision_dict: dict):
        if self.run_id and "run_id" not in decision_dict:
            decision_dict["run_id"] = self.run_id
            
        with open(self.decisions_file, "a") as f:
            f.write(json.dumps(decision_dict) + "\n")
            
        if self.run_id:
            run_dec_path = self.log_dir / f"{self.run_id}_decisions.jsonl"
            with open(run_dec_path, "a") as f:
                f.write(json.dumps(decision_dict) + "\n")
        
    def log_experiment(self, experiment_dict: dict):
        with open(self.experiments_file, "a") as f:
            f.write(json.dumps(experiment_dict) + "\n")

    def log_containment(self, containment_dict: dict):
        with open(self.containment_file, "a") as f:
            f.write(json.dumps(containment_dict) + "\n")

    def log_state_transition(self, state_dict: dict):
        if self.run_id and "run_id" not in state_dict:
            state_dict["run_id"] = self.run_id
        with open(self.state_file, "a") as f:
            f.write(json.dumps(state_dict) + "\n")

    def info(self, message: str):
        self.console.info(message)
        
    def warning(self, message: str):
        self.console.warning(message)

