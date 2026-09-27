import json
from app.storage.logger import EventLogger
from app.models.events import FileEvent

def test_json_logging(tmp_path):
    log_dir = tmp_path / "events"
    logger = EventLogger(log_dir)
    
    event = FileEvent(event_type="created", file_path="test.txt")
    logger.log_event(event.to_dict())
    
    with open(log_dir / "events.jsonl", "r") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["event_type"] == "created"
        assert data["file_path"] == "test.txt"
