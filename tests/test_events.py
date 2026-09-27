from app.models.events import FileEvent

def test_file_event_creation():
    event = FileEvent(event_type="created", file_path="C:\\test.txt")
    assert event.file_extension == "txt"
    assert event.is_decoy is False
    assert "event_id" in event.to_dict()
