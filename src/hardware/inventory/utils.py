"""Utility helpers for manipulating the inventory database."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List


def load_inventory(path: Path) -> List[Dict[str, Any]]:
    """Return the inventory list stored at *path*.

    Missing files yield an empty list.
    """
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return []


def save_inventory(path: Path, data: List[Dict[str, Any]]) -> None:
    """Write *data* to *path* in JSON format."""
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def generate_id() -> str:
    """Return a new unique identifier."""
    return uuid.uuid4().hex
