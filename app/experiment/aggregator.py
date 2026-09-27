import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from app.experiment.metrics import ExperimentOutcome, compute_derived_metrics

class ResultAggregator:
    """
    Result Aggregator module that collects, validates, and synthesizes experiment
    data into machine-readable CSV outputs and summary tables.
    """
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.exp_dir = self.data_dir / "experiments"
        self.results_dir = self.data_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def validate_outcome(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validates an experiment outcome record for structural and logical consistency.
        """
        if not data.get("run_id"):
            return False, "Missing run_id"
        if not data.get("scenario"):
            return False, "Missing scenario name"
        if data.get("detector_mode") not in ["SHORT_WINDOW_BASELINE", "STATEFUL_MULTI_TIMESCALE"]:
            return False, f"Invalid detector_mode: {data.get('detector_mode')}"
            
        score = data.get("outcome", {}).get("max_score", 0.0)
        if score < 0.0 or score > 100.0:
            return False, f"Score out of bounds (must be 0-100): {score}"
            
        high_conf = data.get("outcome", {}).get("high_confidence_reached", False)
        lat = data.get("outcome", {}).get("first_high_confidence_time_seconds")
        if not high_conf and lat is not None:
            return False, f"Invariant violation: detection is False but latency is {lat}"
        if high_conf and score < 80.0 and data.get("outcome", {}).get("final_state") not in ["HIGH_CONFIDENCE", "CONTAINMENT_PENDING", "CONTAINED"]:
            return False, f"Invariant violation: high confidence reached but score {score} < 80"
            
        dur = data.get("duration_seconds", 0.0)
        if dur < 0:
            return False, f"Negative duration: {dur}"
            
        if lat is not None and lat < 0:
            return False, f"Negative detection latency: {lat}"
            
        res = data.get("resource_usage", {})
        if res.get("average_cpu_percent", 0.0) < 0 or res.get("average_rss_mb", 0.0) < 0:
            return False, "Invalid negative resource numbers"
            
        return True, "Valid"

    def aggregate(self) -> Dict[str, Any]:
        return self.run_aggregation()

    def run_aggregation(self) -> Dict[str, Any]:
        outcomes: List[Dict[str, Any]] = []
        valid_outcomes: List[Dict[str, Any]] = []
        invalid_outcomes: List[Dict[str, Any]] = []
        
        seen_run_ids = set()

        if self.exp_dir.exists():
            for p in self.exp_dir.glob("*_outcome.json"):
                try:
                    with open(p, "r") as f:
                        data = json.load(f)
                    run_id = data.get("run_id")
                    if run_id in seen_run_ids:
                        data["validity"] = "INVALID"
                        data["error_message"] = "Duplicate run_id detected"
                        invalid_outcomes.append(data)
                        continue
                        
                    is_valid, msg = self.validate_outcome(data)
                    if is_valid:
                        seen_run_ids.add(run_id)
                        valid_outcomes.append(data)
                    else:
                        data["validity"] = "INVALID"
                        data["error_message"] = msg
                        invalid_outcomes.append(data)
                    outcomes.append(data)
                except Exception as e:
                    print(f"Failed to read outcome file {p}: {e}")

        # 1. Write experiments.csv
        exp_csv_path = self.results_dir / "experiments.csv"
        exp_fields = [
            "run_id", "scenario", "scenario_type", "detector_mode", "detector_version",
            "duration_seconds", "high_confidence_reached", "first_high_confidence_time_seconds",
            "max_score", "final_state", "decoy_interaction", "files_intended", "files_affected",
            "avg_cpu_percent", "max_cpu_percent", "avg_rss_mb", "max_rss_mb", "validity"
        ]
        
        with open(exp_csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=exp_fields)
            writer.writeheader()
            for o in outcomes:
                out_sec = o.get("outcome", {})
                res_sec = o.get("resource_usage", {})
                file_sec = o.get("files", {})
                writer.writerow({
                    "run_id": o.get("run_id"),
                    "scenario": o.get("scenario"),
                    "scenario_type": o.get("scenario_type"),
                    "detector_mode": o.get("detector_mode"),
                    "detector_version": o.get("detector_version"),
                    "duration_seconds": o.get("duration_seconds"),
                    "high_confidence_reached": out_sec.get("high_confidence_reached"),
                    "first_high_confidence_time_seconds": out_sec.get("first_high_confidence_time_seconds"),
                    "max_score": out_sec.get("max_score"),
                    "final_state": out_sec.get("final_state"),
                    "decoy_interaction": out_sec.get("decoy_interaction"),
                    "files_intended": file_sec.get("intended"),
                    "files_affected": file_sec.get("affected"),
                    "avg_cpu_percent": res_sec.get("average_cpu_percent"),
                    "max_cpu_percent": res_sec.get("max_cpu_percent"),
                    "avg_rss_mb": res_sec.get("average_rss_mb"),
                    "max_rss_mb": res_sec.get("max_rss_mb"),
                    "validity": o.get("validity", "SUCCESS")
                })

        # 2. Write metrics.csv
        metrics_csv_path = self.results_dir / "metrics.csv"
        metrics_fields = [
            "run_id", "scenario", "scenario_type", "detector_mode", "duration_seconds",
            "high_confidence_reached", "detection_latency", "max_score", "final_state",
            "decoy_interaction", "files_intended", "files_affected", "synthetic_evasion_success",
            "true_positive", "false_positive", "false_negative", "true_negative",
            "avg_cpu_percent", "max_cpu_percent", "avg_rss_mb", "max_rss_mb", "validity"
        ]
        
        derived_list = []
        with open(metrics_csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=metrics_fields)
            writer.writeheader()
            for o in outcomes:
                try:
                    obj = ExperimentOutcome(**o)
                    m = compute_derived_metrics(obj)
                    derived_list.append(m)
                    writer.writerow(m)
                except Exception as e:
                    print(f"Failed to compute metrics for {o.get('run_id')}: {e}")

        # 3. Write scenario_summary.csv
        summary_csv_path = self.results_dir / "scenario_summary.csv"
        summary_fields = [
            "scenario", "scenario_type", "detector_mode", "total_runs", "successful_runs",
            "detection_rate", "false_positive_rate", "evasion_rate", "mean_latency_seconds",
            "mean_max_score", "avg_cpu_percent", "peak_cpu_percent", "avg_rss_mb", "peak_rss_mb"
        ]
        
        # Group by (scenario, detector_mode)
        groups: Dict[tuple, List[Dict[str, Any]]] = {}
        for m in derived_list:
            if m["validity"] == "SUCCESS":
                key = (m["scenario"], m["detector_mode"])
                groups.setdefault(key, []).append(m)

        summary_rows = []
        with open(summary_csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=summary_fields)
            writer.writeheader()
            
            for (scen, mode), items in sorted(groups.items()):
                scen_type = items[0]["scenario_type"]
                total = len(items)
                
                high_confs = sum(1 for x in items if x["high_confidence_reached"])
                evasions = sum(1 for x in items if x["synthetic_evasion_success"])
                
                det_rate = (high_confs / total) if scen_type == "ATTACK_SIMULATION" else "N/A"
                fp_rate = (high_confs / total) if scen_type == "BENIGN" else "N/A"
                ev_rate = (evasions / total) if scen_type == "ATTACK_SIMULATION" else "N/A"
                
                latencies = [x["detection_latency"] for x in items if x["detection_latency"] is not None]
                mean_lat = (sum(latencies) / len(latencies)) if latencies else None
                
                scores = [x["max_score"] for x in items]
                mean_score = sum(scores) / len(scores) if scores else 0.0
                
                cpus = [x["avg_cpu_percent"] for x in items]
                max_cpus = [x["max_cpu_percent"] for x in items]
                mems = [x["avg_rss_mb"] for x in items]
                max_mems = [x["max_rss_mb"] for x in items]
                
                row = {
                    "scenario": scen,
                    "scenario_type": scen_type,
                    "detector_mode": mode,
                    "total_runs": total,
                    "successful_runs": total,
                    "detection_rate": round(det_rate, 4) if isinstance(det_rate, float) else det_rate,
                    "false_positive_rate": round(fp_rate, 4) if isinstance(fp_rate, float) else fp_rate,
                    "evasion_rate": round(ev_rate, 4) if isinstance(ev_rate, float) else ev_rate,
                    "mean_latency_seconds": round(mean_lat, 2) if mean_lat is not None else "N/A",
                    "mean_max_score": round(mean_score, 1),
                    "avg_cpu_percent": round(sum(cpus) / len(cpus), 2) if cpus else 0.0,
                    "peak_cpu_percent": round(max(max_cpus), 2) if max_cpus else 0.0,
                    "avg_rss_mb": round(sum(mems) / len(mems), 2) if mems else 0.0,
                    "peak_rss_mb": round(max(max_mems), 2) if max_mems else 0.0
                }
                summary_rows.append(row)
                writer.writerow(row)

        return {
            "total_outcomes": len(outcomes),
            "valid_outcomes": len(valid_outcomes),
            "invalid_outcomes": len(invalid_outcomes),
            "csv_files": [
                str(exp_csv_path),
                str(metrics_csv_path),
                str(summary_csv_path)
            ]
        }
