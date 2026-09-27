import pytest
from app.experiment.metrics import ExperimentOutcome, compute_derived_metrics
from app.experiment.aggregator import ResultAggregator
from pathlib import Path

def test_metric_invariants_positive():
    # Valid high confidence detection
    outcome = ExperimentOutcome(
        run_id="run-1",
        scenario="FAST_TRANSFORMATION",
        scenario_type="ATTACK_SIMULATION",
        detector_mode="STATEFUL_MULTI_TIMESCALE",
        detector_version="SM-AY26-FINAL-v1",
        duration_seconds=2.5,
        outcome={
            "high_confidence_reached": True,
            "first_high_confidence_time_seconds": 1.8,
            "final_state": "HIGH_CONFIDENCE",
            "max_score": 85.0,
            "decoy_interaction": True
        }
    )
    
    metrics = compute_derived_metrics(outcome)
    assert metrics["high_confidence_reached"] is True
    assert metrics["detection_latency"] == 1.8
    assert metrics["detection_latency"] > 0
    assert metrics["true_positive"] == 1
    assert metrics["false_positive"] == 0
    assert metrics["synthetic_evasion_success"] is False

def test_metric_invariants_negative():
    # Benign run without detection
    outcome = ExperimentOutcome(
        run_id="run-2",
        scenario="BENIGN_BULK_COPY",
        scenario_type="BENIGN",
        detector_mode="STATEFUL_MULTI_TIMESCALE",
        detector_version="SM-AY26-FINAL-v1",
        duration_seconds=3.0,
        outcome={
            "high_confidence_reached": False,
            "first_high_confidence_time_seconds": None,
            "final_state": "OBSERVING",
            "max_score": 25.0,
            "decoy_interaction": False
        }
    )
    
    metrics = compute_derived_metrics(outcome)
    assert metrics["high_confidence_reached"] is False
    assert metrics["detection_latency"] is None
    assert metrics["true_positive"] == 0
    assert metrics["false_positive"] == 0
    assert metrics["true_negative"] == 1
    assert metrics["synthetic_evasion_success"] is False

def test_aggregator_validation_rejections(tmp_path):
    aggregator = ResultAggregator(tmp_path)
    
    # 1. Out of bounds score (> 100)
    invalid_score = {
        "run_id": "r1",
        "scenario": "FAST_TRANSFORMATION",
        "detector_mode": "STATEFUL_MULTI_TIMESCALE",
        "duration_seconds": 2.0,
        "outcome": {"max_score": 5000.0, "high_confidence_reached": True}
    }
    is_valid, msg = aggregator.validate_outcome(invalid_score)
    assert is_valid is False
    assert "Score out of bounds" in msg
    
    # 2. Invariant violation: detection is False but latency exists
    invalid_latency = {
        "run_id": "r2",
        "scenario": "BENIGN_BULK_COPY",
        "detector_mode": "STATEFUL_MULTI_TIMESCALE",
        "duration_seconds": 2.0,
        "outcome": {"max_score": 30.0, "high_confidence_reached": False, "first_high_confidence_time_seconds": 1.5}
    }
    is_valid, msg = aggregator.validate_outcome(invalid_latency)
    assert is_valid is False
    assert "Invariant violation" in msg
    
    # 3. Invariant violation: high confidence reached but score < 80
    invalid_high_conf = {
        "run_id": "r3",
        "scenario": "FAST_TRANSFORMATION",
        "detector_mode": "STATEFUL_MULTI_TIMESCALE",
        "duration_seconds": 2.0,
        "outcome": {"max_score": 50.0, "high_confidence_reached": True, "final_state": "OBSERVING"}
    }
    is_valid, msg = aggregator.validate_outcome(invalid_high_conf)
    assert is_valid is False
    assert "Invariant violation" in msg
