import argparse
import sys
import json
import time
from pathlib import Path

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
from app.workloads.runner import WorkloadRunner
from app.workloads import get_all_workloads
from app.correlation.state import CampaignMemory
from app.telemetry.process_registry import ProcessRegistry
from app.experiment.runner import ExperimentRunner
from app.experiment.aggregator import ResultAggregator
from app.experiment.analysis import ExperimentAnalysis

global_registry = ProcessRegistry()

def main():
    parser = argparse.ArgumentParser(description="SafeMode Research Prototype CLI")
    
    # Support positional command or subcommands
    parser.add_argument("command", nargs="*", help="Command to run: 'init-lab'/'lab init', 'status', 'workload', 'containment', 'monitor', 'experiment run', 'results aggregate', 'results report'")
    
    parser.add_argument("--list", action="store_true", help="List workloads or containment targets")
    parser.add_argument("--name", type=str, help="Name of workload to run")
    parser.add_argument("--internal-exec", action="store_true", help="Internal subprocess execution mode")
    parser.add_argument("--run-id", type=str, help="Run ID for experiment tracking")
    parser.add_argument("--params", type=str, help="JSON encoded parameters for workload")
    
    parser.add_argument("--scenarios", type=str, help="Comma-separated workload scenario names for experiment run")
    parser.add_argument("--modes", type=str, help="Comma-separated detector modes: SHORT_WINDOW_BASELINE,STATEFUL_MULTI_TIMESCALE")
    parser.add_argument("--repetitions", type=int, default=1, help="Number of repetitions per scenario/mode pair")
    
    parser.add_argument("--action", choices=["DRY_RUN", "SUSPEND", "RESUME", "TERMINATE"], help="Containment action")
    parser.add_argument("--pid", type=int, help="Target PID for containment")
    
    args = parser.parse_args()
    
    config = Config.load()
    logger = EventLogger(config.data_dir / "events")
    decoy_manager = DecoyManager(config.decoy_dir, count=config.decoy_count)
    
    cmd_tokens = [c.lower() for c in args.command] if args.command else ["status"]
    cmd_str = " ".join(cmd_tokens)
    
    if cmd_str in ["init-lab", "lab init", "lab"]:
        logger.info("Initializing lab environment...")
        decoy_manager.initialize()
        logger.info(f"Created {config.decoy_count} decoys in {config.decoy_dir}")
        
    elif cmd_str == "status":
        logger.info("SafeMode Status")
        logger.info(f"Lab Directory: {config.lab_dir}")
        logger.info(f"Response Mode: {config.response_mode}")
        logger.info(f"Detection Mode: {config.detection_mode}")
        logger.info(f"Telemetry Interval: {config.telemetry_interval}")
        logger.info(f"Detector Version: {config.detector_version}")
        
    elif cmd_str in ["workload", "workload run"]:
        runner = WorkloadRunner(config, logger)
        for wl_cls in get_all_workloads():
            runner.register(wl_cls)
            
        if args.internal_exec and args.name:
            # Invoked inside spawned child process
            params = json.loads(args.params) if args.params else {}
            res = runner.execute_internal(args.name, args.run_id or "internal", params)
            print("RESULT_JSON:" + json.dumps(res))
            sys.exit(0)
        elif args.list:
            logger.info("Available workloads:")
            for name in runner.list_workloads():
                logger.info(f" - {name}")
        elif args.name:
            res = runner.run(args.name, registry=global_registry)
            logger.info(f"Workload result: {res}")
        else:
            logger.warning("Please specify --list or --name")

    elif cmd_str in ["experiment", "experiment run"]:
        runner = ExperimentRunner(config)
        all_wl = WorkloadRunner(config, logger)
        for wl_cls in get_all_workloads():
            all_wl.register(wl_cls)
            
        scenarios = args.scenarios.split(",") if args.scenarios else all_wl.list_workloads()
        modes = args.modes.split(",") if args.modes else ["SHORT_WINDOW_BASELINE", "STATEFUL_MULTI_TIMESCALE"]
        
        logger.info(f"Starting Experiment Suite: Scenarios={scenarios}, Modes={modes}, Repetitions={args.repetitions}")
        
        for rep in range(args.repetitions):
            for sc in scenarios:
                for mode in modes:
                    logger.info(f"Running Experiment [Rep {rep+1}/{args.repetitions}]: Scenario={sc}, Mode={mode}")
                    outcome = runner.run_experiment(scenario=sc, detector_mode=mode, random_seed=42+rep)
                    logger.info(f"Outcome: MaxScore={outcome.outcome['max_score']}, HighConf={outcome.outcome['high_confidence_reached']}, Duration={outcome.duration_seconds}s")
                    time.sleep(1.0) # Cooldown between runs
                    
        logger.info("Experiment suite execution complete.")

    elif cmd_str in ["results aggregate", "aggregate"]:
        logger.info("Aggregating experiment results into CSV tables...")
        aggregator = ResultAggregator(config.data_dir)
        summary = aggregator.run_aggregation()
        logger.info(f"Aggregation Complete: Processed {summary['valid_outcomes']} valid runs. CSV outputs saved to {config.data_dir / 'results'}")

    elif cmd_str in ["results report", "report"]:
        logger.info("Generating experiment analysis report & research charts...")
        analysis = ExperimentAnalysis(config.data_dir)
        charts = analysis.generate_all_charts()
        analysis.print_summary_table()
        logger.info(f"Report Generation Complete: Generated {len(charts)} figures in {config.data_dir / 'figures'}")

    elif cmd_str == "containment":
        response_manager = ResponseManager(config, logger, global_registry)
        if args.list:
            logger.info("Registered Lab Processes:")
            for pid, info in global_registry.registered_processes.items():
                logger.info(f"PID: {pid} | Status: {info['status']} | Scenario: {info['scenario']}")
        elif args.action and (args.pid or args.name):
            target = args.pid or args.name
            logger.info(f"Executing {args.action} on target {target}...")
            audit = response_manager.execute_containment(target, args.action)
            logger.info(f"Containment Result: {audit['action_result']} - {audit['reason']}")
        else:
            logger.warning("Please specify --list or both --action and --pid")
            
    elif cmd_str == "monitor":
        logger.info("Starting SafeMode monitor daemon...")
        if config.decoy_dir.exists():
            for f in config.decoy_dir.iterdir():
                if f.is_file():
                    decoy_manager.decoy_paths.add(str(f.absolute()))
                    
        buffer = TemporalEventBuffer(window_seconds=config.correlation_window)
        extractor = SignalExtractor(config.signal_thresholds)
        engine = CorrelationEngine(window_seconds=config.correlation_window)
        process_snapshot = ProcessSnapshot()
        
        state_memory = CampaignMemory(config, logger)
        response_manager = ResponseManager(config, logger, global_registry)
        
        pipeline = EventPipeline(logger, buffer, extractor, engine, response_manager, process_snapshot, config, state_memory)
        
        monitor = FileMonitor(str(config.lab_dir), pipeline, decoy_manager.get_decoy_paths())
        monitor.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping monitor...")
            monitor.stop()
    else:
        logger.warning(f"Unknown command: '{cmd_str}'")

if __name__ == "__main__":
    main()

