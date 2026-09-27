from app.config import Config

def test_config_defaults():
    config = Config()
    assert config.response_mode == "CONTAIN"
    assert config.decoy_count == 10
    assert "lab" in str(config.lab_dir)
