import os
import time
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.config import Config
from app.storage.logger import EventLogger
from app.detection.decoys import DecoyManager
from app.response.actions import ResponseManager
from app.correlation.pipeline import EventPipeline
from app.telemetry.monitor import FileMonitor
from app.correlation.buffer import TemporalEventBuffer
from app.detection.signals import SignalExtractor
from app.detection.correlation import CorrelationEngine
from app.telemetry.process_context import ProcessSnapshot
from app.telemetry.process_registry import ProcessRegistry
from app.telemetry.resource_monitor import ResourceMonitor
from app.workloads.runner import WorkloadRunner
from app.workloads import get_all_workloads
from app.correlation.state import CampaignMemory
from app.experiment.manifest import ExperimentManifest
from app.experiment.metrics import ExperimentOutcome

class ExperimentRunner:
    """
    Orchestrates reproducible evaluation runs comparing SHORT_WINDOW_BASELINE
    and STATEFUL_MULTI_TIMESCALE detection modes against synthetic workloads.
    """
    def __init__(self, base_config: Optional[Config] = None):
        self.base_config = base_config or Config.load()
        
    def run_experiment(
        self,
        scenario: str,
        detector_mode: str = "STATEFUL_MULTI_TIMESCALE",
        random_seed: int = 42,
        workload_params: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
        containment_action: str = "DRY_RUN"
    ) -> ExperimentOutcome:
        run_id = run_id or str(uuid.uuid4())
        workload_params = workload_params or {}
        
        # Clone configuration and set mode
        cfg = Config.load()
        cfg.detection_mode = detector_mode
        cfg.lab_mode = True
        
        # Data directory layout
        exp_dir = cfg.data_dir / "experiments"
        events_dir = cfg.data_dir / "events"
        decisions_dir = cfg.data_dir / "decisions"
        resources_dir = cfg.data_dir / "resources"
        
        for d in [exp_dir, events_dir, decisions_dir, resources_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        logger = EventLogger(events_dir, run_id=run_id)
        registry = ProcessRegistry()
        
        decoy_manager = DecoyManager(cfg.decoy_dir, count=cfg.decoy_count)
        decoy_manager.initialize()
        
        # Setup telemetry & correlation components
        buffer = TemporalEventBuffer(window_seconds=cfg.correlation_window)
        extractor = SignalExtractor(cfg.signal_thresholds)
        engine = CorrelationEngine(window_seconds=cfg.correlation_window)
        process_snapshot = ProcessSnapshot()
        
        state_memory = CampaignMemory(cfg, logger) if detector_mode == "STATEFUL_MULTI_TIMESCALE" else None
        response_manager = ResponseManager(cfg, logger, registry)
        
        pipeline = EventPipeline(
            logger=logger,
            buffer=buffer,
            extractor=extractor,
            engine=engine,
            response=response_manager,
            process_snapshot=process_snapshot,
            config=cfg,
            state_memory=state_memory
        )
        
        # Monitor filesystem events in lab directory
        monitor = FileMonitor(str(cfg.lab_dir), pipeline, decoy_manager.get_decoy_paths())
        monitor.start()
        
        # Start Resource Monitor tracking detector process
        res_log_path = resources_dir / f"{run_id}_resources.jsonl"
        res_monitor = ResourceMonitor(target_pid=os.getpid(), interval=0.2, log_path=res_log_path)
        res_monitor.start()
        
        # Setup workload runner
        wl_runner = WorkloadRunner(cfg, logger)
        for wl_cls in get_all_workloads():
            wl_runner.register(wl_cls)
            
        wl_class = wl_runner.get_workload_class(scenario)
        if not wl_class:
            monitor.stop()
            res_monitor.stop()
            raise ValueError(f"Unknown scenario: {scenario}")
            
        scenario_type = getattr(wl_class, "scenario_type", "UNKNOWN")
        
        start_time = time.time()
        
        # Launch workload as child subprocess
        sub_info = wl_runner.run_subprocess(
            name=scenario,
            registry=registry,
            run_id=run_id,
            params=workload_params
        )
        
        if "error" in sub_info:
            monitor.stop()
            res_monitor.stop()
            return ExperimentOutcome(
                run_id=run_id,
                scenario=scenario,
                scenario_type=scenario_type,
                detector_mode=detector_mode,
                detector_version=cfg.detector_version,
                duration_seconds=0.0,
                validity="FAILED",
                error_message=sub_info["error"]
            )

        proc = sub_info["popen"]
        pid = sub_info["pid"]
        
        # Track decision outcomes during execution
        first_high_conf_time = None
        max_score = 0.0
        decoy_hit = False
        decisions_collected = []
        
        # Monitor workload subprocess until exit
        while proc.poll() is None:
            time.sleep(0.1)
            pipeline.evaluate(time.time())
            
        # Give watchdog buffer a brief moment to process final events
        time.sleep(0.5)
        pipeline.evaluate(time.time())
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Stop telemetry monitoring
        monitor.stop()
        res_monitor.stop()
        
        # Finalize process registry status
        if proc.returncode == 0:
            registry.update_status(pid, "COMPLETED")
        else:
            registry.update_status(pid, "FAILED")
            
        res_summary = res_monitor.get_summary()
        
        # Inspect logged decisions for this run
        run_dec_path = events_dir / f"{run_id}_decisions.jsonl"
        if run_dec_path.exists():
            with open(run_dec_path, "r") as f:
                for line in f:
                    if line.strip():
                        dec = json.loads(line.strip())
                        decisions_collected.append(dec)
                        score = float(dec.get("score", 0.0))
                        if score > max_score:
                            max_score = score
                        if dec.get("risk_level") == "HIGH" or score >= cfg.escalation_threshold:
                            if first_high_conf_time is None:
                                first_high_conf_time = round(dec.get("timestamp", end_time) - start_time, 2)
                        for sig in dec.get("signals", []):
                            if sig.get("name") == "DECOY_INTERACTION":
                                decoy_hit = True

        final_state_str = "IDLE"
        if state_memory:
            final_state_str = state_memory.state.status
            if state_memory.state.accumulated_score > max_score:
                max_score = state_memory.state.accumulated_score
            if state_memory.state.decoy_interactions > 0:
                decoy_hit = True
            if state_memory.state.status in ["HIGH_CONFIDENCE", "CONTAINMENT_PENDING", "CONTAINED"]:
                if first_high_conf_time is None:
                    first_high_conf_time = round(state_memory.state.last_event_time - start_time, 2)

        # Enforce strict bounded score: 0.0 <= max_score <= 100.0
        max_score = round(min(100.0, max(0.0, max_score)), 1)
        
        # Strict invariant: high_confidence_reached requires max_score >= 80 or HIGH state
        high_conf_reached = (max_score >= cfg.escalation_threshold) or (final_state_str in ["HIGH_CONFIDENCE", "CONTAINMENT_PENDING", "CONTAINED"])
        if not high_conf_reached:
            first_high_conf_time = None
        elif first_high_conf_time is None:
            first_high_conf_time = round(duration, 2)

        # Calculate affected file count accurately from raw events
        unique_affected_files = set()
        run_ev_path = events_dir / f"{run_id}_events.jsonl"
        if run_ev_path.exists():
            with open(run_ev_path, "r") as f:
                for line in f:
                    if line.strip():
                        ev = json.loads(line.strip())
                        p = ev.get("file_path")
                        if p:
                            unique_affected_files.add(p)
                            
        affected_count = len(unique_affected_files)
        if affected_count == 0 and state_memory:
            affected_count = len(state_memory.state.affected_files)
        intended_count = getattr(wl_class, "file_count", 10)
        if hasattr(wl_class, "bursts") and hasattr(wl_class, "burst_size"):
            intended_count = wl_class.bursts * wl_class.burst_size

        # Create Manifest
        manifest = ExperimentManifest(
            run_id=run_id,
            scenario=scenario,
            scenario_type=scenario_type,
            detector_mode=detector_mode,
            detector_version=cfg.detector_version,
            random_seed=random_seed,
            workload_parameters=workload_params,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            target_directory=str(cfg.lab_dir),
            number_of_files_intended=intended_count,
            number_of_files_affected=affected_count,
            workload_pid=pid,
            process_executable=sub_info["exe_path"],
            containment_policy=containment_action,
            result_file_paths={
                "events_log": str(events_dir / f"{run_id}_events.jsonl"),
                "decisions_log": str(events_dir / f"{run_id}_decisions.jsonl"),
                "resources_log": str(res_log_path),
                "manifest": str(exp_dir / f"{run_id}_manifest.json"),
                "outcome": str(exp_dir / f"{run_id}_outcome.json")
            }
        )
        manifest.save(exp_dir / f"{run_id}_manifest.json")
        
        # Create Outcome
        outcome = ExperimentOutcome(
            run_id=run_id,
            scenario=scenario,
            scenario_type=scenario_type,
            detector_mode=detector_mode,
            detector_version=cfg.detector_version,
            duration_seconds=round(duration, 2),
            outcome={
                "high_confidence_reached": high_conf_reached,
                "first_high_confidence_time_seconds": first_high_conf_time,
                "final_state": final_state_str,
                "max_score": round(max_score, 1),
                "decoy_interaction": decoy_hit
            },
            files={
                "intended": intended_count,
                "affected": affected_count
            },
            resource_usage=res_summary,
            containment={
                "requested": (containment_action != "NONE"),
                "action": containment_action,
                "result": "SUCCESS" if proc.returncode == 0 else "FAILED"
            },
            validity="SUCCESS" if proc.returncode == 0 else "FAILED"
        )
        outcome.save(exp_dir / f"{run_id}_outcome.json")
        
        return outcome
