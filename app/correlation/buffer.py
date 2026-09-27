from collections import deque
from app.models.events import FileEvent
from typing import List, Optional

class TemporalEventBuffer:
    def __init__(self, window_seconds: float = 5.0):
        self.window_seconds = window_seconds
        self.events: deque = deque()
        
    def add(self, event: FileEvent):
        self.events.append(event)
        self.expire_old_events(event.timestamp)
        
    def expire_old_events(self, current_time: float):
        while self.events and current_time - self.events[0].timestamp > self.window_seconds:
            self.events.popleft()
            
    def get_all(self) -> List[FileEvent]:
        return list(self.events)
        
    def query(self, 
              event_type: Optional[str] = None, 
              is_decoy: Optional[bool] = None,
              file_path: Optional[str] = None) -> List[FileEvent]:
        result = list(self.events)
        if event_type:
            result = [e for e in result if e.event_type == event_type]
        if is_decoy is not None:
            result = [e for e in result if e.is_decoy == is_decoy]
        if file_path:
            result = [e for e in result if e.file_path == file_path]
        return result
        
    def get_unique_files(self) -> set:
        return set(e.file_path for e in self.events)
