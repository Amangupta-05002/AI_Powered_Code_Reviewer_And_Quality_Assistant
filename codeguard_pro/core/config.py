# codeguard_pro/core/config.py

import tomllib
from pathlib import Path

DEFAULT_CONFIG = {
    "coverage_threshold": 80,
    "docstring_style": "google",
    "severity": "medium",
    "auto_fix": True,
    "exclude_paths": ["venv", "__pycache__", ".git"]
}

def load_config():
    config_path = Path("pyproject.toml")

    if not config_path.exists():
        return DEFAULT_CONFIG

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    tool_config = data.get("tool", {}).get("codeguard_pro", {})

    return {**DEFAULT_CONFIG, **tool_config}