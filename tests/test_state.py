import pytest
import time
from app.correlation.state import CampaignMemory
from app.config import Config
from app.storage.logger import EventLogger
from app.models.events import Signal

def test_campaign_memory_accumulation(tmp_path):
    config = Config()
    logger = EventLogger(tmp_path / "logs")
    memory = CampaignMemory(config, logger)
    
    s1 = Signal("RAPID_MODIFICATION_BURST", 5, ["e1"])
    state = memory.update([s1], time.time())
    
    assert state.status == "OBSERVING"
    assert state.accumulated_score > 0
    
    s2 = Signal("DECOY_INTERACTION", 1, ["e2"])
    state = memory.update([s2], time.time())
    
    assert state.status == "SUSPICIOUS"
    # Ah, let's add one more
    s3 = Signal("RENAME_BURST", 3, ["e3"])
    state = memory.update([s3], time.time())
    assert state.accumulated_score >= config.escalation_threshold
    assert state.status == "HIGH_CONFIDENCE"

def test_campaign_memory_decay(tmp_path):
    config = Config()
    config.evidence_decay_rate = 10.0 # Fast decay
    logger = EventLogger(tmp_path / "logs")
    memory = CampaignMemory(config, logger)
    
    s1 = Signal("RAPID_MODIFICATION_BURST", 5, ["e1"])
    memory.update([s1], time.time())
    
    # 2 seconds later, no signals
    state = memory.update([], time.time() + 2.0)
    
    # Initial score was 25. 2 seconds * 10 = 20 decay. Remaining = 5.
    assert state.accumulated_score <= 5.0

def test_campaign_memory_reset(tmp_path):
    config = Config()
    config.cooldown_period = 2.0
    logger = EventLogger(tmp_path / "logs")
    memory = CampaignMemory(config, logger)
    
    s1 = Signal("RAPID_MODIFICATION_BURST", 5, ["e1"])
    memory.update([s1], time.time())
    
    # 3 seconds later, cooldown expires
    state = memory.update([], time.time() + 3.0)
    
    assert state.status == "IDLE"
    assert state.accumulated_score == 0.0
