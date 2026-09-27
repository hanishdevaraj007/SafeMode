import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.models.events import FileEvent
from app.correlation.pipeline import EventPipeline

class LabEventHandler(FileSystemEventHandler):
    def __init__(self, pipeline: EventPipeline, decoy_paths: set):
        self.pipeline = pipeline
        self.decoy_paths = set(p.lower() for p in decoy_paths)

    def _process_event(self, event, event_type):
        if event.is_directory:
            return
            
        src_lower = event.src_path.lower()
        is_decoy = src_lower in self.decoy_paths
        
        file_event = FileEvent(
            event_type=event_type,
            file_path=event.src_path,
            is_decoy=is_decoy
        )
        self.pipeline.process(file_event)

    def on_created(self, event):
        self._process_event(event, "created")

    def on_modified(self, event):
        self._process_event(event, "modified")

    def on_deleted(self, event):
        self._process_event(event, "deleted")

    def on_moved(self, event):
        if not event.is_directory:
            src_lower = event.src_path.lower()
            dest_lower = event.dest_path.lower()
            is_decoy = (src_lower in self.decoy_paths) or (dest_lower in self.decoy_paths)
            file_event = FileEvent(
                event_type="renamed",
                file_path=f"{event.src_path} -> {event.dest_path}",
                is_decoy=is_decoy
            )
            self.pipeline.process(file_event)

class FileMonitor:
    def __init__(self, monitor_dir: str, pipeline: EventPipeline, decoy_paths: set):
        self.monitor_dir = monitor_dir
        self.observer = Observer()
        self.handler = LabEventHandler(pipeline, decoy_paths)
        
    def start(self):
        self.observer.schedule(self.handler, self.monitor_dir, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
