from pathlib import Path

import pytest

from hardware.inventory.utils import ocr_extract, parse_fields, text_hash


class DummyResp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_ocr_extract_and_parse(monkeypatch, tmp_path):
    img = tmp_path / "image.png"
    img.write_bytes(b"x")

    def fake_post(url, files):
        return DummyResp({"ParsedResults": [{"ParsedText": "100uF 5 pcs $1.50"}]})

    monkeypatch.setattr("requests.post", fake_post)
    text = ocr_extract(img, "http://example.com")
    assert "100uF" in text

    data = parse_fields(text)
    assert data["value"] == "100uF"
    assert data["qty"] == "5"
    assert data["price"] == "$1.50"

    h = text_hash(text)
    assert len(h) == 40
