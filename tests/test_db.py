from hardware.inventory.utils import JSONDB, SQLiteDB


def _run_backend_tests(db):
    e1 = {"name": "c1"}
    assert db.add(e1, "f1", "h1")
    assert db.has_file("f1")
    assert db.has_hash("h1")
    # duplicate file/hash
    assert not db.add(e1, "f1", "h1")
    assert not db.add(e1, "f2", "h1")
    # new entry
    assert db.add({"name": "c2"}, "f2", "h2")


def test_json_db(tmp_path):
    path = tmp_path / "db.json"
    db = JSONDB(path)
    _run_backend_tests(db)
    db2 = JSONDB(path)
    assert db2.has_file("f1")
    assert db2.has_hash("h2")


def test_sqlite_db(tmp_path):
    path = tmp_path / "db.sqlite"
    db = SQLiteDB(path)
    _run_backend_tests(db)
    db2 = SQLiteDB(path)
    assert db2.has_file("f1")
    assert db2.has_hash("h2")
