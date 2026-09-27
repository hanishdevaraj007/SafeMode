import time
from app.storage.logger import EventLogger
from app.correlation.buffer import TemporalEventBuffer
from app.detection.signals import SignalExtractor
from app.detection.correlation import CorrelationEngine
from app.response.actions import ResponseManager
from app.telemetry.process_context import ProcessSnapshot
from app.correlation.state import CampaignMemory
from app.config import Config

class EventPipeline:
    def __init__(self, logger: EventLogger, buffer: TemporalEventBuffer, extractor: SignalExtractor, engine: CorrelationEngine, response: ResponseManager, process_snapshot: ProcessSnapshot, config: Config, state_memory: CampaignMemory = None):
        self.logger = logger
        self.buffer = buffer
        self.extractor = extractor
        self.engine = engine
        self.response = response
        self.process_snapshot = process_snapshot
        self.config = config
        self.state_memory = state_memory
        
        self.last_evaluation = 0.0
        self.evaluation_interval = 1.0

    def process(self, event):
        self.buffer.add(event)
        self.logger.log_event(event.to_dict())
        
        current_time = time.time()
        if current_time - self.last_evaluation >= self.evaluation_interval:
            self.last_evaluation = current_time
            self.evaluate(current_time)
            
    def evaluate(self, current_time: float):
        signals = self.extractor.extract(self.buffer)
        
        if self.config.detection_mode == "STATEFUL_MULTI_TIMESCALE" and self.state_memory:
            state = self.state_memory.update(signals, current_time)
        else:
            state = None
            
        if not signals and (not state or state.status == "IDLE"):
            return
            
        process_context = self.process_snapshot.get_context()
        
        decision = self.engine.evaluate(
            signals, 
            self.buffer, 
            process_context, 
            detection_mode=self.config.detection_mode,
            state=state
        )
        
        if decision.risk_level in ["MEDIUM", "HIGH"] or (state and state.status != "IDLE"):
            self.logger.log_decision(decision.to_dict())
            
            if decision.risk_level == "HIGH":
                if state and state.status == "HIGH_CONFIDENCE":
                    self.state_memory.set_containment_pending()
                self.response.handle(decision.to_dict())
