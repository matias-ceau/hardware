from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
import uuid

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from . import config
from . import utils


console = Console()


def _resolve_db_paths(args: argparse.Namespace) -> utils.BaseDB:
    cfg = config.CONFIG
    db_sqlite = args.db_sqlite or ("metadata.db" if Path("metadata.db").exists() else None)
    if not db_sqlite:
        db_sqlite = cfg.get("database", {}).get("sqlite_path")

    db_json = args.db_json or ("components.jsonld" if Path("components.jsonld").exists() else None)
    if not db_json:
        db_json = cfg.get("database", {}).get("jsonld_path")

    if not db_sqlite and not db_json:
        console.print("[bold red]Error:[/] Specify --db-sqlite or --db-json or configure in cfg.toml")
        sys.exit(1)

    if db_sqlite:
        return utils.SQLiteDB(Path(db_sqlite))
    return utils.JSONDB(Path(db_json))


def _review(candidate: dict, db: utils.BaseDB, service: str) -> dict | None:
    table = Table()
    table.add_column("Field")
    table.add_column("Value")
    for k, v in candidate.items():
        table.add_row(k, str(v))
    console.print(table)
    if not Confirm.ask("Accept entry?", default=True):
        return None
    for k in list(candidate):
        candidate[k] = Prompt.ask(k, default=str(candidate[k]))
    candidate.setdefault("id", str(uuid.uuid4()))
    candidate.setdefault("timestamp", datetime.utcnow().isoformat())
    candidate.setdefault("source", service)
    if "type" in candidate:
        candidate["type"] = db.normalize_type(candidate["type"])
    return candidate


def _process(path: Path, db: utils.BaseDB, args: argparse.Namespace, pre: list[str], post: list[str]) -> None:
    if args.resume and db.has_file(str(path)):
        return
    text = utils.ocr_extract(path, args.service)
    text_hash = utils.text_hash(text)
    if db.has_hash(text_hash):
        return
    for t in pre:
        fn = getattr(utils, t, lambda x: x)
        text = fn(text)
    candidate = utils.parse_fields(text)
    entry = _review(candidate, db, args.service)
    if entry:
        for t in post:
            fn = getattr(utils, t, lambda x: x)
            entry = fn(entry)
        db.add(entry, str(path), text_hash)


def main(argv: list[str] | None = None) -> None:
    cfg = config.CONFIG
    proc_tools = cfg.get("tools", {}).get("preprocess", [])
    post_tools = cfg.get("tools", {}).get("postprocess", [])
    service_default = cfg.get("main", {}).get("service", "mistral")

    parser = argparse.ArgumentParser(description=cfg.get("main", {}).get("description", "Component loader"))
    parser.add_argument("path")
    parser.add_argument("--db-sqlite")
    parser.add_argument("--db-json")
    parser.add_argument("--import-db")
    parser.add_argument("--service", default=service_default, choices=list(utils.DEFAULT_ENDPOINTS))
    parser.add_argument("--ext", default=",".join([".png", ".jpg", ".jpeg", ".pdf"]))
    parser.add_argument("--continue", dest="resume", action="store_true")

    args = parser.parse_args(argv)

    db = _resolve_db_paths(args)
    if args.import_db:
        db.import_db(Path(args.import_db))

    exts = {e if e.startswith('.') else f'.{e}' for e in args.ext.split(',')}
    target = Path(args.path)
    files: list[Path] = []
    if target.is_dir():
        files = [p for p in target.iterdir() if p.suffix.lower() in exts]
    elif target.is_file():
        files = [target]
    else:
        console.print(f"[red]Path not found: {target}")
        sys.exit(1)
    files.sort()

    for p in files:
        console.rule(p.name)
        _process(p, db, args, proc_tools, post_tools)

    console.print("[green]Done. Database updated.[/]")

