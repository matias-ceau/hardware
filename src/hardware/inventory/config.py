from __future__ import annotations

import os
from pathlib import Path
import tomllib


def _load_toml(path: Path) -> dict:
    if path.exists():
        return tomllib.loads(path.read_text())
    return {}


# Load configuration from default locations
def _load_config() -> dict:
    """Load configuration from various locations with precedence."""
    config = {}
    cwd = Path.cwd()
    home = Path.home()

    # Load configs in order of precedence (later overrides earlier)
    for path in (home / ".component_loader.toml", cwd / "cfg.toml"):
        config.update(_load_toml(path))

    # Set defaults if not specified
    config.setdefault("main", {})
    config["main"].setdefault("service", "mistral")
    config["main"].setdefault("description", "Component loader")

    config.setdefault("database", {})
    config.setdefault("tools", {"preprocess": [], "postprocess": []})

    return config


# Global configuration instance
CONFIG = _load_config()


def _get_xdg_data_home() -> Path:
    """Get XDG_DATA_HOME directory, defaulting to ~/.local/share if not set."""
    xdg_data = os.getenv("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data)
    return Path.home() / ".local" / "share"


def resolve_db_paths(
    db_sqlite: str | None = None,
    db_json: str | None = None,
    cwd: Path | None = None,
    home: Path | None = None,
) -> tuple[str | None, str | None]:
    """Return (sqlite_path, json_path) with precedence:
    CLI flags > cwd files > config files > XDG defaults.
    
    New behavior:
    - Looks for .hardware-inventory.db in current directory first
    - Falls back to XDG_DATA_HOME/hardware/inventory-main.db
    - SQLite is primary, JSON-LD is optional secondary
    """
    cwd = Path(cwd or Path.cwd())
    home = Path(home or Path.home())

    # CLI flags override everything
    if db_sqlite or db_json:
        return db_sqlite, db_json

    # Check for .hardware-inventory.db in current directory (primary)
    local_sqlite = cwd / ".hardware-inventory.db"
    local_json = cwd / ".hardware-inventory.jsonld"
    
    if local_sqlite.exists():
        # If local SQLite exists, also check for optional JSON-LD
        json_path = str(local_json) if local_json.exists() else None
        return str(local_sqlite), json_path

    # Check for legacy files in cwd for backward compatibility
    legacy_sqlite = cwd / "metadata.db"
    legacy_json = cwd / "components.jsonld"
    if legacy_sqlite.exists() or legacy_json.exists():
        return (
            str(legacy_sqlite) if legacy_sqlite.exists() else None,
            str(legacy_json) if legacy_json.exists() else None
        )

    # Load configs for custom paths
    config = {}
    for path in (home / ".component_loader.toml", cwd / "cfg.toml"):
        config.update(_load_toml(path))

    db_cfg = config.get("database", {})
    config_sqlite = db_cfg.get("sqlite_path")
    config_json = db_cfg.get("jsonld_path")
    
    if config_sqlite or config_json:
        return config_sqlite, config_json

    # Default: XDG_DATA_HOME/hardware/inventory-main.db
    xdg_data = _get_xdg_data_home()
    default_dir = xdg_data / "hardware"
    default_dir.mkdir(parents=True, exist_ok=True)
    
    default_sqlite = default_dir / "inventory-main.db"
    default_json = default_dir / "inventory-main.jsonld"
    
    # Return defaults (JSON-LD only if it exists)
    return str(default_sqlite), str(default_json) if default_json.exists() else None
