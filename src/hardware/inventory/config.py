
from __future__ import annotations

from pathlib import Path
import tomllib


CFG_FILES = [Path.cwd() / "cfg.toml", Path.home() / ".component_loader.toml"]


def load_config() -> dict:
    """Load configuration from ``cfg.toml`` or the user's home directory."""
    for path in CFG_FILES:
        if path.exists():
            with path.open("rb") as f:
                return tomllib.load(f)
    return {}


CONFIG = load_config()
