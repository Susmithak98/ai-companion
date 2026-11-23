import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def temp_data_dir(tmp_path, monkeypatch):
    """Give every test its own empty memory and mood files."""
    import config
    import agents
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(agents, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(agents, "MEMORY_FILE", str(tmp_path / "aira_memory.json"))
    monkeypatch.setattr(agents, "MOOD_FILE", str(tmp_path / "aira_moods.csv"))
    yield
