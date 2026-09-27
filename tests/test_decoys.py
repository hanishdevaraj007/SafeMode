from app.detection.decoys import DecoyManager

def test_decoy_initialization(tmp_path):
    decoy_dir = tmp_path / "decoys"
    manager = DecoyManager(decoy_dir, count=5)
    manager.initialize()
    
    files = list(decoy_dir.iterdir())
    assert len(files) == 5
    assert len(manager.get_decoy_paths()) == 5
