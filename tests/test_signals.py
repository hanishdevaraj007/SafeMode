from app.correlation.buffer import TemporalEventBuffer
from app.models.events import FileEvent
from app.detection.signals import SignalExtractor

def test_signal_decoy_interaction():
    buffer = TemporalEventBuffer(window_seconds=5.0)
    buffer.add(FileEvent("modified", "decoy.txt", is_decoy=True))
    
    extractor = SignalExtractor({})
    signals = extractor.extract(buffer)
    
    names = [s.name for s in signals]
    assert "DECOY_INTERACTION" in names

def test_rapid_modification_burst():
    buffer = TemporalEventBuffer(window_seconds=5.0)
    for i in range(5):
        buffer.add(FileEvent("modified", f"file_{i}.txt"))
        
    extractor = SignalExtractor({"RAPID_MODIFICATION_BURST_COUNT": 5})
    signals = extractor.extract(buffer)
    
    names = [s.name for s in signals]
    assert "RAPID_MODIFICATION_BURST" in names
