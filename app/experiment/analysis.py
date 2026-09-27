import os
import csv
import json
from pathlib import Path
from typing import Dict, Any, List
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

class ExperimentAnalysis:
    """
    Generates structured comparative tables and research publication figures
    based strictly on empirical experiment results.
    """
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.results_dir = self.data_dir / "results"
        self.figures_dir = self.data_dir / "figures"
        self.figures_dir.mkdir(parents=True, exist_ok=True)

    def load_metrics(self) -> List[Dict[str, Any]]:
        metrics_file = self.results_dir / "metrics.csv"
        if not metrics_file.exists():
            return []
        items = []
        with open(metrics_file, "r") as f:
            reader = csv.DictReader(f)
            for r in reader:
                items.append(r)
        return items

    def generate_all_charts(self) -> List[str]:
        metrics = self.load_metrics()
        if not metrics:
            print("No metrics available for chart generation.")
            return []

        generated = []
        g1 = self._plot_detection_outcomes(metrics)
        if g1: generated.append(g1)

        g2 = self._plot_detection_latency(metrics)
        if g2: generated.append(g2)

        g3 = self._plot_cpu_overhead(metrics)
        if g3: generated.append(g3)

        g4 = self._plot_memory_overhead(metrics)
        if g4: generated.append(g4)

        g5 = self._plot_score_progression()
        if g5: generated.append(g5)

        return generated

    def _plot_detection_outcomes(self, metrics: List[Dict[str, Any]]) -> str:
        scenarios = sorted(list(set(m["scenario"] for m in metrics)))
        if not scenarios:
            return ""

        modes = ["SHORT_WINDOW_BASELINE", "STATEFUL_MULTI_TIMESCALE"]
        scores_by_mode = {m: [] for m in modes}
        
        for sc in scenarios:
            for mode in modes:
                match = [m for m in metrics if m["scenario"] == sc and m["detector_mode"] == mode]
                if match:
                    val = 1.0 if match[0]["high_confidence_reached"].lower() == "true" else 0.0
                else:
                    val = 0.0
                scores_by_mode[mode].append(val)

        x = range(len(scenarios))
        width = 0.35

        plt.figure(figsize=(12, 6))
        plt.bar([i - width/2 for i in x], scores_by_mode["SHORT_WINDOW_BASELINE"], width, label="Baseline (Short-Window)", color="#e74c3c")
        plt.bar([i + width/2 for i in x], scores_by_mode["STATEFUL_MULTI_TIMESCALE"], width, label="Stateful (Multi-Timescale)", color="#2ecc71")

        plt.xlabel("Workload Scenario", fontsize=11, fontweight="bold")
        plt.ylabel("High-Confidence Decision Reached (1 = Yes, 0 = No)", fontsize=11, fontweight="bold")
        plt.title("Detection Outcome by Scenario and Detector Mode", fontsize=13, fontweight="bold")
        plt.xticks(x, scenarios, rotation=45, ha="right", fontsize=9)
        plt.yticks([0, 1], ["Avoided / Low Risk", "High Confidence"])
        plt.legend()
        plt.tight_layout()
        
        out_path = self.figures_dir / "detection_outcomes.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        return str(out_path)

    def _plot_detection_latency(self, metrics: List[Dict[str, Any]]) -> str:
        scenarios = sorted(list(set(m["scenario"] for m in metrics)))
        if not scenarios:
            return ""

        modes = ["SHORT_WINDOW_BASELINE", "STATEFUL_MULTI_TIMESCALE"]
        latency_by_mode = {m: [] for m in modes}

        for sc in scenarios:
            for mode in modes:
                match = [m for m in metrics if m["scenario"] == sc and m["detector_mode"] == mode]
                if match and match[0].get("detection_latency") and match[0]["detection_latency"] != "None":
                    val = float(match[0]["detection_latency"])
                else:
                    val = 0.0
                latency_by_mode[mode].append(val)

        x = range(len(scenarios))
        width = 0.35

        plt.figure(figsize=(12, 6))
        plt.bar([i - width/2 for i in x], latency_by_mode["SHORT_WINDOW_BASELINE"], width, label="Baseline (Short-Window)", color="#e74c3c")
        plt.bar([i + width/2 for i in x], latency_by_mode["STATEFUL_MULTI_TIMESCALE"], width, label="Stateful (Multi-Timescale)", color="#3498db")

        plt.xlabel("Workload Scenario", fontsize=11, fontweight="bold")
        plt.ylabel("Detection Latency (Seconds)", fontsize=11, fontweight="bold")
        plt.title("Detection Latency by Scenario and Detector Mode", fontsize=13, fontweight="bold")
        plt.xticks(x, scenarios, rotation=45, ha="right", fontsize=9)
        plt.legend()
        plt.tight_layout()

        out_path = self.figures_dir / "detection_latency.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        return str(out_path)

    def _plot_cpu_overhead(self, metrics: List[Dict[str, Any]]) -> str:
        scenarios = sorted(list(set(m["scenario"] for m in metrics)))
        if not scenarios:
            return ""

        modes = ["SHORT_WINDOW_BASELINE", "STATEFUL_MULTI_TIMESCALE"]
        cpu_by_mode = {m: [] for m in modes}

        for sc in scenarios:
            for mode in modes:
                match = [m for m in metrics if m["scenario"] == sc and m["detector_mode"] == mode]
                if match:
                    val = float(match[0].get("avg_cpu_percent", 0.0))
                else:
                    val = 0.0
                cpu_by_mode[mode].append(val)

        x = range(len(scenarios))
        width = 0.35

        plt.figure(figsize=(12, 6))
        plt.bar([i - width/2 for i in x], cpu_by_mode["SHORT_WINDOW_BASELINE"], width, label="Baseline CPU %", color="#9b59b6")
        plt.bar([i + width/2 for i in x], cpu_by_mode["STATEFUL_MULTI_TIMESCALE"], width, label="Stateful CPU %", color="#1abc9c")

        plt.xlabel("Workload Scenario", fontsize=11, fontweight="bold")
        plt.ylabel("Average Detector CPU (%)", fontsize=11, fontweight="bold")
        plt.title("SafeMode Detector CPU Overhead", fontsize=13, fontweight="bold")
        plt.xticks(x, scenarios, rotation=45, ha="right", fontsize=9)
        plt.legend()
        plt.tight_layout()

        out_path = self.figures_dir / "cpu_overhead.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        return str(out_path)

    def _plot_memory_overhead(self, metrics: List[Dict[str, Any]]) -> str:
        scenarios = sorted(list(set(m["scenario"] for m in metrics)))
        if not scenarios:
            return ""

        modes = ["SHORT_WINDOW_BASELINE", "STATEFUL_MULTI_TIMESCALE"]
        rss_by_mode = {m: [] for m in modes}

        for sc in scenarios:
            for mode in modes:
                match = [m for m in metrics if m["scenario"] == sc and m["detector_mode"] == mode]
                if match:
                    val = float(match[0].get("avg_rss_mb", 0.0))
                else:
                    val = 0.0
                rss_by_mode[mode].append(val)

        x = range(len(scenarios))
        width = 0.35

        plt.figure(figsize=(12, 6))
        plt.bar([i - width/2 for i in x], rss_by_mode["SHORT_WINDOW_BASELINE"], width, label="Baseline RSS (MB)", color="#e67e22")
        plt.bar([i + width/2 for i in x], rss_by_mode["STATEFUL_MULTI_TIMESCALE"], width, label="Stateful RSS (MB)", color="#34495e")

        plt.xlabel("Workload Scenario", fontsize=11, fontweight="bold")
        plt.ylabel("Average Detector RSS Memory (MB)", fontsize=11, fontweight="bold")
        plt.title("SafeMode Detector Memory RSS Overhead", fontsize=13, fontweight="bold")
        plt.xticks(x, scenarios, rotation=45, ha="right", fontsize=9)
        plt.legend()
        plt.tight_layout()

        out_path = self.figures_dir / "memory_overhead.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        return str(out_path)

    def _plot_score_progression(self) -> str:
        # Load decisions log for state progression plot
        dec_file = self.data_dir / "events" / "decisions.jsonl"
        if not dec_file.exists():
            return ""

        timestamps = []
        scores = []
        first_t = None

        with open(dec_file, "r") as f:
            for line in f:
                if line.strip():
                    d = json.loads(line.strip())
                    if d.get("detection_mode") == "STATEFUL_MULTI_TIMESCALE":
                        t = d.get("timestamp", 0.0)
                        if first_t is None:
                            first_t = t
                        rel_t = t - first_t
                        timestamps.append(rel_t)
                        scores.append(d.get("score", 0.0))

        if not timestamps:
            return ""

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, scores, marker="o", color="#e74c3c", linewidth=2, label="Accumulated Risk Score")
        plt.axhline(y=80, color="r", linestyle="--", label="High Confidence Escalation Threshold (80)")
        plt.axhline(y=40, color="y", linestyle=":", label="Suspicious Threshold (40)")

        plt.xlabel("Elapsed Time (Seconds)", fontsize=11, fontweight="bold")
        plt.ylabel("Stateful Risk Score", fontsize=11, fontweight="bold")
        plt.title("Multi-Timescale State Progression for Slow/Intermittent Workload", fontsize=13, fontweight="bold")
        plt.legend()
        plt.tight_layout()

        out_path = self.figures_dir / "score_progression.png"
        plt.savefig(out_path, dpi=300)
        plt.close()
        return str(out_path)

    def print_summary_table(self):
        summary_file = self.results_dir / "scenario_summary.csv"
        if not summary_file.exists():
            print("No scenario summary found.")
            return

        print("\n" + "="*125)
        print("SAFEMODE RESEARCH PROTOTYPE - EMPIRICAL EVALUATION RESULTS TABLE")
        print("="*125)
        header = f"{'Scenario':<28} | {'Type':<18} | {'Mode':<10} | {'Det Rate':<9} | {'FP Rate':<8} | {'Mean Lat':<9} | {'Max Score':<10} | {'Avg CPU %':<10} | {'Avg RSS MB':<11}"
        print(header)
        print("-" * len(header))

        with open(summary_file, "r") as f:
            reader = csv.DictReader(f)
            for r in reader:
                mode_str = "Baseline" if r["detector_mode"] == "SHORT_WINDOW_BASELINE" else "Stateful"
                det_str = str(r.get("detection_rate", "N/A"))
                fp_str = str(r.get("false_positive_rate", "N/A"))
                lat_str = str(r.get("mean_latency_seconds", "N/A"))
                print(f"{r['scenario']:<28} | {r['scenario_type']:<18} | {mode_str:<10} | {det_str:<9} | {fp_str:<8} | {lat_str:<9} | {r['mean_max_score']:<10} | {r['avg_cpu_percent']:<10} | {r['avg_rss_mb']:<11}")
        print("="*125 + "\n")
