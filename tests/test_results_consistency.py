from pathlib import Path
from scripts.validate_results_consistency import validate_consistency

def test_all_experiment_results_consistent():
    """
    Verifies that all 22 benchmark runs maintain strict invariant consistency:
    - Bounded scores [0.0, 100.0]
    - Decisions JSONL matches outcome JSON
    - Outcome JSON matches experiments.csv and metrics.csv
    - Metrics match scenario_summary.csv aggregates
    - Benign runs have zero false positives (FP Rate == 0.0)
    - Detection latency is only defined when High Confidence is reached
    """
    assert validate_consistency(Path("D:/Innovation_lab")) is True
