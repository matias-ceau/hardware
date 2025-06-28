from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any

import requests


def ocr_extract(path: Path, service_url: str) -> str:
    """Upload file to service_url and return extracted text."""
    with path.open("rb") as fh:
        resp = requests.post(service_url, files={"file": fh})
    resp.raise_for_status()
    data = resp.json()
    return data.get("text") or data.get("ParsedResults", [{}])[0].get("ParsedText", "")


def parse_fields(text: str) -> dict[str, Any]:
    field_patterns = {
        "value": r"([0-9\.]+\s*(?:[µu]F|nF|pF|kΩ|Ω|mH|uH|%))",
        "qty": r"([0-9]+)\s*(?:pcs?)",
        # price requires a currency symbol to avoid matching numeric values
        "price": r"([€$£]\s*[0-9]+\.?[0-9]*)",
    }
    data: dict[str, Any] = {}
    for key, pattern in field_patterns.items():
        m = re.search(pattern, text, re.I)
        if m:
            data[key] = m.group(1).strip()
    lines = text.splitlines()
    data["description"] = lines[0][:120] if lines else ""
    return data


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()


class JSONDB:
    def __init__(self, path: Path) -> None:
        self.path = path
        if path.exists():
            self.entries = json.loads(path.read_text())
        else:
            self.entries = []

    def has_file(self, f: str) -> bool:
        return any(e.get("file") == f for e in self.entries)

    def has_hash(self, h: str) -> bool:
        return any(e.get("hash") == h for e in self.entries)

    def add(self, entry: dict[str, Any], file: str, h: str) -> bool:
        if self.has_file(file) or self.has_hash(h):
            return False
        entry = entry.copy()
        entry["file"] = file
        entry["hash"] = h
        self.entries.append(entry)
        self.path.write_text(json.dumps(self.entries))
        return True


class SQLiteDB:
    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS components (file TEXT, hash TEXT, data TEXT)"
        )

    def has_file(self, f: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM components WHERE file = ? LIMIT 1", (f,)
        )
        return cur.fetchone() is not None

    def has_hash(self, h: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM components WHERE hash = ? LIMIT 1", (h,)
        )
        return cur.fetchone() is not None

    def add(self, entry: dict[str, Any], file: str, h: str) -> bool:
        if self.has_file(file) or self.has_hash(h):
            return False
        self.conn.execute(
            "INSERT INTO components (file, hash, data) VALUES (?,?,?)",
            (file, h, json.dumps(entry)),
        )
        self.conn.commit()
        return True