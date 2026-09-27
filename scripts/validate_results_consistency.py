"""
Programmatic Result Consistency Validator for SafeMode Research Prototype.
Verifies exact alignment across:
RAW DECISIONS JSONL <-> OUTCOME JSON <-> EXPERIMENTS CSV <-> METRICS CSV <-> SCENARIO SUMMARY CSV
"""
import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any, List

def validate_consistency(base_dir: Path = Path("D:/Innovation_lab")) -> bool:
    data_dir = base_dir / "data"
    exp_dir = data_dir / "experiments"
    events_dir = data_dir / "events"
    results_dir = data_dir / "results"

    exp_csv = results_dir / "experiments.csv"
    metrics_csv = results_dir / "metrics.csv"
    summary_csv = results_dir / "scenario_summary.csv"

    if not exp_csv.exists() or not metrics_csv.exists() or not summary_csv.exists():
        print("ERROR: Result CSV files do not exist.")
        return False

    # Read experiments.csv
    exp_rows: Dict[str, Dict[str, str]] = {}
    with open(exp_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            exp_rows[r["run_id"]] = r

    # Read metrics.csv
    metrics_rows: Dict[str, Dict[str, str]] = {}
    with open(metrics_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            metrics_rows[r["run_id"]] = r

    # Read summary_csv
    summary_rows: Dict[tuple, Dict[str, str]] = {}
    with open(summary_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            summary_rows[(r["scenario"], r["detector_mode"])] = r

    outcome_files = list(exp_dir.glob("*_outcome.json"))
    if not outcome_files:
        print("ERROR: No outcome files found.")
        return False

    print(f"Validating consistency across {len(outcome_files)} experiment outcome files...")

    errors: List[str] = []

    for out_file in outcome_files:
        with open(out_file, "r", encoding="utf-8") as f:
            outcome = json.load(f)

        run_id = outcome["run_id"]
        scenario = outcome["scenario"]
        scen_type = outcome["scenario_type"]
        det_mode = outcome["detector_mode"]
        out_sec = outcome.get("outcome", {})
        high_conf = out_sec.get("high_confidence_reached", False)
        max_score = out_sec.get("max_score", 0.0)
        final_state = out_sec.get("final_state", "IDLE")
        lat = out_sec.get("first_high_confidence_time_seconds")

        # 1. Verify against raw decisions JSONL if available
        dec_file = events_dir / f"{run_id}_decisions.jsonl"
        if dec_file.exists():
            dec_scores = []
            dec_high_confs = []
            with open(dec_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        dec = json.loads(line)
                        s = float(dec.get("score", 0.0))
                        r = dec.get("risk_level")
                        dec_scores.append(s)
                        dec_high_confs.append(r == "HIGH" or s >= 80.0)

            if dec_scores:
                raw_max = max(dec_scores)
                if abs(raw_max - max_score) > 0.1:
                    errors.append(f"[{run_id}] max_score mismatch: outcome={max_score}, raw_decisions={raw_max}")
            if dec_high_confs:
                raw_high_conf = any(dec_high_confs)
                if raw_high_conf != high_conf:
                    errors.append(f"[{run_id}] high_confidence mismatch: outcome={high_conf}, raw_decisions={raw_high_conf}")


        # 2. Invariants on outcome itself
        if max_score < 0.0 or max_score > 100.0:
            errors.append(f"[{run_id}] Score out of bounded range [0, 100]: {max_score}")
        if not high_conf and lat is not None:
            errors.append(f"[{run_id}] HighConf is False but latency is defined: {lat}")
        if scen_type == "BENIGN" and high_conf:
            errors.append(f"[{run_id}] BENIGN run triggered HIGH_CONFIDENCE: max_score={max_score}")

        # 3. Verify against experiments.csv
        exp_row = exp_rows.get(run_id)
        if not exp_row:
            errors.append(f"[{run_id}] Missing from experiments.csv")
        else:
            if exp_row["high_confidence_reached"].lower() != str(high_conf).lower():
                errors.append(f"[{run_id}] experiments.csv high_confidence mismatch: {exp_row['high_confidence_reached']} vs {high_conf}")
            if abs(float(exp_row["max_score"]) - max_score) > 0.01:
                errors.append(f"[{run_id}] experiments.csv max_score mismatch: {exp_row['max_score']} vs {max_score}")
            if exp_row["final_state"] != final_state:
                errors.append(f"[{run_id}] experiments.csv final_state mismatch: {exp_row['final_state']} vs {final_state}")

        # 4. Verify against metrics.csv
        met_row = metrics_rows.get(run_id)
        if not met_row:
            errors.append(f"[{run_id}] Missing from metrics.csv")
        else:
            parse_int = lambda v: 1 if str(v).strip().lower() in ["1", "true"] else 0
            tp = parse_int(met_row["true_positive"])
            fp = parse_int(met_row["false_positive"])
            fn = parse_int(met_row["false_negative"])
            tn = parse_int(met_row["true_negative"])
            evasion = parse_int(met_row["synthetic_evasion_success"])


            if scen_type == "ATTACK_SIMULATION":
                if high_conf:
                    if tp != 1 or fn != 0 or evasion != 0 or fp != 0 or tn != 0:
                        errors.append(f"[{run_id}] metrics.csv attack detected error: tp={tp}, fn={fn}, ev={evasion}")
                else:
                    if tp != 0 or fn != 1 or evasion != 1 or fp != 0 or tn != 0:
                        errors.append(f"[{run_id}] metrics.csv attack evaded error: tp={tp}, fn={fn}, ev={evasion}")
            elif scen_type == "BENIGN":
                if high_conf:
                    if fp != 1 or tn != 0 or tp != 0 or fn != 0:
                        errors.append(f"[{run_id}] metrics.csv benign false positive error: fp={fp}, tn={tn}")
                else:
                    if fp != 0 or tn != 1 or tp != 0 or fn != 0:
                        errors.append(f"[{run_id}] metrics.csv benign clean error: fp={fp}, tn={tn}")

    # 5. Verify scenario_summary.csv aggregates
    for (scen, mode), sum_row in summary_rows.items():
        matching_mets = [m for m in metrics_rows.values() if m["scenario"] == scen and m["detector_mode"] == mode and m["validity"] == "SUCCESS"]
        if not matching_mets:
            continue
        tot = len(matching_mets)
        if int(sum_row["total_runs"]) != tot:
            errors.append(f"Summary [{scen}, {mode}] total_runs mismatch: {sum_row['total_runs']} vs {tot}")
        
        scen_type = matching_mets[0]["scenario_type"]
        if scen_type == "ATTACK_SIMULATION":
            exp_det = sum(int(m["true_positive"]) for m in matching_mets) / tot
            if abs(float(sum_row["detection_rate"]) - exp_det) > 0.001:
                errors.append(f"Summary [{scen}, {mode}] det_rate mismatch: {sum_row['detection_rate']} vs {exp_det}")
        elif scen_type == "BENIGN":
            exp_fp = sum(int(m["false_positive"]) for m in matching_mets) / tot
            if abs(float(sum_row["false_positive_rate"]) - exp_fp) > 0.001:
                errors.append(f"Summary [{scen}, {mode}] fp_rate mismatch: {sum_row['false_positive_rate']} vs {exp_fp}")

    if errors:
        print(f"FAILED: Found {len(errors)} consistency errors:")
        for e in errors:
            print(f"  - {e}")
        return False

    print(f"PASSED: Perfect mathematical and empirical consistency verified across all {len(outcome_files)} runs!")
    return True

if __name__ == "__main__":
    ok = validate_consistency()
    sys.exit(0 if ok else 1)
