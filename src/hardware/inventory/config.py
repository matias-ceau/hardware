from __future__ import annotations

from pathlib import Path
import tomllib


def _load_toml(path: Path) -> dict:
    if path.exists():
        return tomllib.loads(path.read_text())
    return {}


def resolve_db_paths(db_sqlite: str | None = None, db_json: str | None = None,
                     cwd: Path | None = None, home: Path | None = None) -> tuple[str | None, str | None]:
    """Return (sqlite_path, json_path) with precedence:
    CLI flags > cwd files > config files.
    """
    cwd = Path(cwd or Path.cwd())
    home = Path(home or Path.home())

    # CLI flags override everything
    if db_sqlite or db_json:
        return db_sqlite, db_json

    # Check for files in cwd
    sqlite_file = cwd / "metadata.db"
    json_file = cwd / "components.jsonld"
    if sqlite_file.exists() or json_file.exists():
        return str(sqlite_file) if sqlite_file.exists() else None, \
            str(json_file) if json_file.exists() else None

    # Load configs
    config = {}
    # load global config first then override with cwd config
    for path in (home / ".component_loader.toml", cwd / "cfg.toml"):
        config.update(_load_toml(path))

    db_cfg = config.get("database", {})
    return db_cfg.get("sqlite_path"), db_cfg.get("jsonld_path")
