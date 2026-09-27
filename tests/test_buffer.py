import time
from app.correlation.buffer import TemporalEventBuffer
from app.models.events import FileEvent

def test_buffer_add_and_expire():
    buffer = TemporalEventBuffer(window_seconds=1.0)
    
    e1 = FileEvent("created", "test1.txt")
    e1.timestamp = time.time() - 2.0  # old
    
    e2 = FileEvent("created", "test2.txt")
    e2.timestamp = time.time()
    
    buffer.add(e1)
    buffer.add(e2)
    
    events = buffer.get_all()
    assert len(events) == 1
    assert events[0].file_path == "test2.txt"

def test_buffer_query():
    buffer = TemporalEventBuffer(window_seconds=5.0)
    buffer.add(FileEvent("modified", "decoy.txt", is_decoy=True))
    buffer.add(FileEvent("created", "normal.txt", is_decoy=False))
    
    decoys = buffer.query(is_decoy=True)
    assert len(decoys) == 1
    assert decoys[0].file_path == "decoy.txt"
