from app.models.events import Signal, FileEvent
from app.detection.correlation import CorrelationEngine
from app.correlation.buffer import TemporalEventBuffer

def test_correlation_engine_decoy_and_burst():
    engine = CorrelationEngine(window_seconds=5.0)
    
    signals = [
        Signal("DECOY_INTERACTION", 1, []),
        Signal("MULTI_FILE_TRANSFORMATION", 5, [])
    ]
    
    buffer = TemporalEventBuffer()
    buffer.add(FileEvent("modified", "decoy.txt"))
    
    decision = engine.evaluate(signals, buffer, {})
    assert decision.risk_level == "HIGH"
    assert decision.score >= 80

def test_benign_activity():
    engine = CorrelationEngine(window_seconds=5.0)
    
    signals = [
        Signal("RAPID_MODIFICATION_BURST", 5, [])
    ]
    
    buffer = TemporalEventBuffer()
    buffer.add(FileEvent("modified", "test.txt"))
    
    decision = engine.evaluate(signals, buffer, {})
    assert decision.risk_level in ["LOW", "MEDIUM"]
    assert decision.score < 80
