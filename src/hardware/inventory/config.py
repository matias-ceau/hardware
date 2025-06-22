"""Configuration helpers for the inventory subsystem."""

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True)
class InventoryConfig:
    """Simple configuration object.

    The path of the inventory database can be overridden via the
    ``HARDWARE_DB_PATH`` environment variable. By default ``inventory.json``
    in the current working directory is used.
    """

    path: Path = Path(os.getenv("HARDWARE_DB_PATH", "inventory.json"))
