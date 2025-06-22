"""Utility helpers for manipulating the inventory database."""

from __future__ import annotations

import sqlite3
import json
from collections.abc import Iterable
from typing import Any, Dict
import re
import hashlib
from pathlib import Path

FIELD_PATTERNS = {
    "value": r"([0-9\.]+\s*(?:[µu]F|nF|pF|kΩ|Ω|mH|uH|%)|10[0-9]{2})",
    "qty": r"([0-9]+)\s*(?:pcs?)",
    "price": r"([€$£]?\s*[0-9]+\.?[0-9]*)",
}


def parse_fields(text: str) -> Dict[str, str]:
    """Extract basic fields from OCR text."""
    data: Dict[str, str] = {}
    for field, pattern in FIELD_PATTERNS.items():
        m = re.search(pattern, text, re.I)
        if m:
            data[field] = m.group(1).strip()
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if lines:
        data["description"] = lines[0][:120]
    return data


# ----------------------- Utility helpers -----------------------


def text_hash(text: str) -> str:
    """Return a SHA-1 hash for ``text``."""
    return hashlib.sha1(text.encode()).hexdigest()


def trim_whitespace(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines())


def normalize_unicode(text: str) -> str:
    import unicodedata

    return unicodedata.normalize("NFKC", text)


def validate_schema(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder postprocess step."""
    return entry


def dedupe_entries(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder postprocess step."""
    return entry


# ----------------------- Database backends -----------------------


class BaseDB:
    def has_file(self, path: str) -> bool:
        """Check if the file path exists in the database."""
        raise NotImplementedError

    def has_hash(self, value: str) -> bool:
        """Check if the hash value exists in the database."""
        raise NotImplementedError

    def add(self, entry: Dict[str, Any], path: str, hsh: str) -> None:
        """Add an entry to the database with associated file path and hash."""
        raise NotImplementedError

    def import_db(self, path: Path) -> None:
        """Import database entries from the given path."""
        raise NotImplementedError

    def normalize_type(self, typ: str) -> str:
        return typ.strip().lower()


class JSONDB(BaseDB):
    def __init__(self, path: Path) -> None:
        self.path = path
        if path.exists():
            try:
                self.data = json.loads(path.read_text())
                if not isinstance(self.data, list):
                    self.data = []
            except Exception:
                self.data = []
        else:
            self.data = []
        self._index_files = {e.get("_file") for e in self.data if e.get("_file")}
        self._index_hashes = {e.get("_hash") for e in self.data if e.get("_hash")}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2))

    def has_file(self, path: str) -> bool:
        return path in self._index_files

    def has_hash(self, value: str) -> bool:
        return value in self._index_hashes

    def add(self, entry: Dict[str, Any], path: str, hsh: str) -> None:
        entry = dict(entry)
        entry["_file"] = path
        entry["_hash"] = hsh
        self.data.append(entry)
        self._index_files.add(path)
        self._index_hashes.add(hsh)
        self._save()

    def import_db(self, path: Path) -> None:
        if not path.exists():
            return
        data = json.loads(path.read_text())
        if not isinstance(data, Iterable):
            return
        for entry in data:
            h = entry.get("_hash")
            if h and h not in self._index_hashes:
                self.data.append(entry)
                self._index_files.add(entry.get("_file"))
                self._index_hashes.add(h)
        self._save()


class SQLiteDB(BaseDB):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(path)
        self._setup()

    def _setup(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS components (id TEXT PRIMARY KEY, data TEXT, file TEXT UNIQUE, hash TEXT UNIQUE)"
        )
        self.conn.commit()

    def has_file(self, path: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM components WHERE file=?", (path,))
        return cur.fetchone() is not None

    def has_hash(self, value: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM components WHERE hash=?", (value,))
        return cur.fetchone() is not None

    def add(self, entry: Dict[str, Any], path: str, hsh: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO components(id,data,file,hash) VALUES(?,?,?,?)",
            (entry["id"], json.dumps(entry), path, hsh),
        )
        self.conn.commit()

    def import_db(self, path: Path) -> None:
        if not path.exists():
            return
        src = sqlite3.connect(path)
        for row in src.execute("SELECT id,data,file,hash FROM components"):
            if not self.has_hash(row[3]):
                self.conn.execute(
                    "INSERT OR IGNORE INTO components(id,data,file,hash) VALUES(?,?,?,?)",
                    row,
                )
        self.conn.commit()
        src.close()
