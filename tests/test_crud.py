"""Tests for CRUD operations in database backends."""

import json
from hardware.inventory.utils import JSONDB, SQLiteDB


def test_jsondb_crud_operations(tmp_path):
    """Test CRUD operations for JSON database backend."""
    db_path = tmp_path / "test.json"
    db = JSONDB(db_path)
    
    # Test adding components
    component1 = {"id": "comp1", "type": "resistor", "value": "100Ω", "description": "Test resistor"}
    component2 = {"id": "comp2", "type": "capacitor", "value": "100µF", "description": "Test capacitor"}
    
    assert db.add(component1, "file1.jpg", "hash1")
    assert db.add(component2, "file2.jpg", "hash2")
    
    # Test listing
    all_components = db.list_all()
    assert len(all_components) == 2
    
    # Test pagination
    paginated = db.list_all(limit=1, offset=0)
    assert len(paginated) == 1
    
    # Test search
    resistor_results = db.search("resistor")
    assert len(resistor_results) == 1
    assert resistor_results[0]["type"] == "resistor"
    
    field_search = db.search("100Ω", "value")
    assert len(field_search) == 1
    
    # Test get by ID
    component = db.get_by_id("comp1")
    assert component is not None
    assert component["type"] == "resistor"
    
    # Test update
    success = db.update("comp1", {"value": "200Ω", "qty": "5"})
    assert success
    updated = db.get_by_id("comp1")
    assert updated["value"] == "200Ω"
    assert updated["qty"] == "5"
    
    # Test update non-existent
    assert not db.update("nonexistent", {"value": "300Ω"})
    
    # Test count
    assert db.count() == 2
    
    # Test stats
    stats = db.get_stats()
    assert stats["total_components"] == 2
    assert "resistor" in stats["types"]
    assert "capacitor" in stats["types"]
    
    # Test delete
    success = db.delete("comp2")
    assert success
    assert db.count() == 1
    assert db.get_by_id("comp2") is None
    
    # Test delete non-existent
    assert not db.delete("nonexistent")


def test_sqlitedb_crud_operations(tmp_path):
    """Test CRUD operations for SQLite database backend."""
    db_path = tmp_path / "test.db"
    db = SQLiteDB(db_path)
    
    # Test adding components
    component1 = {"id": "comp1", "type": "resistor", "value": "100Ω", "description": "Test resistor"}
    component2 = {"id": "comp2", "type": "capacitor", "value": "100µF", "description": "Test capacitor"}
    
    assert db.add(component1, "file1.jpg", "hash1")
    assert db.add(component2, "file2.jpg", "hash2")
    
    # Test listing
    all_components = db.list_all()
    assert len(all_components) == 2
    
    # Test pagination
    paginated = db.list_all(limit=1, offset=0)
    assert len(paginated) == 1
    
    # Test search
    resistor_results = db.search("resistor")
    assert len(resistor_results) == 1
    assert resistor_results[0]["type"] == "resistor"
    
    field_search = db.search("100Ω", "value")
    assert len(field_search) == 1
    
    # Test get by ID
    component = db.get_by_id("comp1")
    assert component is not None
    assert component["type"] == "resistor"
    
    # Test update
    success = db.update("comp1", {"value": "200Ω", "qty": "5"})
    assert success
    updated = db.get_by_id("comp1")
    assert updated["value"] == "200Ω"
    assert updated["qty"] == "5"
    
    # Test update non-existent
    assert not db.update("nonexistent", {"value": "300Ω"})
    
    # Test count
    assert db.count() == 2
    
    # Test stats
    stats = db.get_stats()
    assert stats["total_components"] == 2
    assert "resistor" in stats["types"]
    assert "capacitor" in stats["types"]
    
    # Test delete
    success = db.delete("comp2")
    assert success
    assert db.count() == 1
    assert db.get_by_id("comp2") is None
    
    # Test delete non-existent
    assert not db.delete("nonexistent")


def test_database_stats_with_quantities(tmp_path):
    """Test statistics calculation with component quantities."""
    db = JSONDB(tmp_path / "test.json")
    
    components = [
        {"id": "1", "type": "resistor", "qty": "10 pcs", "description": "10K resistor"},
        {"id": "2", "type": "resistor", "qty": "5 pcs", "description": "1K resistor"},
        {"id": "3", "type": "capacitor", "qty": "20 pcs", "description": "100µF cap"},
        {"id": "4", "type": "transistor", "qty": "invalid", "description": "NPN transistor"},
    ]
    
    for i, comp in enumerate(components):
        db.add(comp, f"file{i}.jpg", f"hash{i}")
    
    stats = db.get_stats()
    
    assert stats["total_components"] == 4
    assert stats["total_quantity"] == 35  # 10 + 5 + 20 (invalid qty ignored)
    assert stats["types"]["resistor"] == 2
    assert stats["types"]["capacitor"] == 1
    assert stats["types"]["transistor"] == 1
    assert stats["most_common_type"] == "resistor"


def test_empty_database_operations(tmp_path):
    """Test operations on empty database."""
    db = JSONDB(tmp_path / "empty.json")
    
    # Test operations on empty database
    assert db.list_all() == []
    assert db.search("anything") == []
    assert db.get_by_id("nonexistent") is None
    assert not db.update("nonexistent", {"value": "test"})
    assert not db.delete("nonexistent")
    assert db.count() == 0
    
    stats = db.get_stats()
    assert stats["total_components"] == 0
    assert stats["total_quantity"] == 0
    assert stats["types"] == {}
    assert stats["most_common_type"] is None