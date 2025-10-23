from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Protocol

import requests

# Default service endpoints
DEFAULT_ENDPOINTS = {
    "mistral": "https://api.mistral.ai/v1/chat/completions",
    "local": "http://localhost:11434/api/generate",  # Local Ollama instance
    "ocr.space": "https://api.ocr.space/parse/image",
    "openai": "https://api.openai.com/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}


class BaseDB(Protocol):
    """Base protocol for database implementations.
    
    Provides a unified interface for different database backends (JSON, SQLite)
    supporting full CRUD operations for hardware component inventory.
    """

    def has_file(self, f: str) -> bool:
        """Check if file already exists in database."""
        ...

    def has_hash(self, h: str) -> bool:
        """Check if hash already exists in database."""
        ...

    def add(self, entry: dict[str, Any], file: str, h: str) -> bool:
        """Add new entry to database."""
        ...

    def list_all(self, limit: int | None = None, offset: int = 0) -> list[dict[str, Any]]:
        """List all components with optional pagination.
        
        Args:
            limit: Maximum number of entries to return (None for all)
            offset: Number of entries to skip
            
        Returns:
            List of component dictionaries
        """
        ...

    def search(self, query: str, field: str | None = None) -> list[dict[str, Any]]:
        """Search components by text query.
        
        Args:
            query: Search term to match
            field: Specific field to search in (None for all fields)
            
        Returns:
            List of matching component dictionaries
        """
        ...

    def get_by_id(self, component_id: str) -> dict[str, Any] | None:
        """Get a specific component by ID.
        
        Args:
            component_id: Unique identifier for the component
            
        Returns:
            Component dictionary or None if not found
        """
        ...

    def update(self, component_id: str, updates: dict[str, Any]) -> bool:
        """Update an existing component.
        
        Args:
            component_id: Unique identifier for the component
            updates: Dictionary of fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        ...

    def delete(self, component_id: str) -> bool:
        """Delete a component from the database.
        
        Args:
            component_id: Unique identifier for the component
            
        Returns:
            True if deletion successful, False otherwise
        """
        ...

    def count(self) -> int:
        """Get total number of components in database."""
        ...

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with counts by type, total components, etc.
        """
        ...

    def normalize_type(self, type_str: str) -> str:
        """Normalize component type string."""
        return type_str.lower().strip()

    def import_db(self, path: Path) -> None:
        """Import data from another database file."""
        ...


def ocr_extract(path: Path, service: str) -> str:
    """Extract text from image using specified service."""
    match service:
        case "mistral":
            return _mistral_ocr_extract(path, service)
        case "openai":
            return _openai_ocr_extract(path, service)
        case "openrouter":
            return _openrouter_ocr_extract(path, service)
        case "local" | "ocr.space":
            # Legacy services that use direct file upload
            service_url = DEFAULT_ENDPOINTS[service]
            with path.open("rb") as fh:
                resp = requests.post(service_url, files={"file": fh})
            resp.raise_for_status()
            data = resp.json()
            return data.get("text") or data.get("ParsedResults", [{}])[0].get("ParsedText", "")
        case _:
            raise ValueError(f"Unknown OCR service: {service}")


def _encode_image_base64(image_path: Path) -> str:
    """Encode image as base64 string for API."""
    with image_path.open("rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def _get_image_mime_type(image_path: Path) -> str:
    """Get MIME type for image file."""
    suffix = image_path.suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg', 
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(suffix, 'image/jpeg')


def test_api_connectivity(service: str) -> bool:
    """Test API connectivity using free endpoints."""
    try:
        if service == "mistral":
            return _test_mistral_connectivity()
        elif service == "openai":
            return _test_openai_connectivity()
        elif service == "openrouter":
            return _test_openrouter_connectivity()
        else:
            return False
    except Exception:
        return False


def _test_mistral_connectivity() -> bool:
    """Test Mistral API connectivity using models endpoint."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return False
    
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.mistral.ai/v1/models", headers=headers, timeout=10)
    return response.status_code == 200


def _test_openai_connectivity() -> bool:
    """Test OpenAI API connectivity using models endpoint."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False
    
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
    return response.status_code == 200


def _test_openrouter_connectivity() -> bool:
    """Test OpenRouter API connectivity using models endpoint."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return False
    
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
    return response.status_code == 200


def _mistral_ocr_extract(path: Path, service: str) -> str:
    """Extract text using Mistral Vision API."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set")
    
    base64_image = _encode_image_base64(path)
    mime_type = _get_image_mime_type(path)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "pixtral-large-latest",  # Mistral's latest vision model (Oct 2025)
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Please extract all text from this image of electronics components. 
                        Focus on identifying component types, values, quantities, part numbers, and descriptions.
                        Return only the extracted text, no additional commentary."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    response = requests.post(DEFAULT_ENDPOINTS[service], headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _openai_ocr_extract(path: Path, service: str) -> str:
    """Extract text using OpenAI Vision API."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    base64_image = _encode_image_base64(path)
    mime_type = _get_image_mime_type(path)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o",  # GPT-4o with vision capabilities (latest as of Oct 2025)
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Please extract all text from this image of electronics components. 
                        Focus on identifying component types, values, quantities, part numbers, and descriptions.
                        Return only the extracted text, no additional commentary."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    response = requests.post(DEFAULT_ENDPOINTS[service], headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _openrouter_ocr_extract(path: Path, service: str) -> str:
    """Extract text using OpenRouter with vision-capable models."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    
    base64_image = _encode_image_base64(path)
    mime_type = _get_image_mime_type(path)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/matias-ceau/hardware",  # Optional
        "X-Title": "Hardware Inventory OCR"  # Optional
    }
    
    payload = {
        "model": "anthropic/claude-3-5-sonnet-20241022",  # Vision-capable model (Oct 2025)
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Please extract all text from this image of electronics components. 
                        Focus on identifying component types, values, quantities, part numbers, and descriptions.
                        Return only the extracted text, no additional commentary."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    response = requests.post(DEFAULT_ENDPOINTS[service], headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    return data["choices"][0]["message"]["content"]


def parse_fields(text: str) -> dict[str, Any]:
    field_patterns = {
        "value": r"([0-9\.]+\s*(?:[µu]F|nF|pF|kΩ|Ω|mH|uH|%))",
        "qty": r"([0-9]+)\s*(?:pcs?|pieces?)",
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
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def parse_jsonld_components(imported_data: dict | list, source_path: Path) -> list[dict[str, Any]]:
    """Parse components from JSON-LD or simple list format."""
    components_to_add = []
    
    # Handle simple list format (legacy)
    if isinstance(imported_data, list):
        return imported_data
    
    # Handle JSON-LD format with @graph structure
    elif isinstance(imported_data, dict) and "@graph" in imported_data:
        graph = imported_data["@graph"]
        if isinstance(graph, list):
            for item in graph:
                if item.get("@type") == "ComponentCollection":
                    # Extract components from different collections
                    for collection_key in ["resistors", "capacitors", "transistors", "ICs", "potentiometers", "passives", "components"]:
                        if collection_key in item:
                            collection = item[collection_key]
                            if isinstance(collection, list):
                                for component in collection:
                                    normalized = normalize_jsonld_component(component, collection_key, source_path)
                                    if normalized:
                                        components_to_add.append(normalized)
    
    return components_to_add


def normalize_jsonld_component(component: dict[str, Any], collection_type: str, source_path: Path) -> dict[str, Any] | None:
    """Normalize a component from JSON-LD format to our internal format."""
    if not isinstance(component, dict):
        return None
        
    normalized = {}
    
    # Generate ID if not present
    if "id" not in component:
        component_type = component.get("@type", collection_type.rstrip("s")).lower()
        # Create a unique ID based on component properties
        if component_type == "resistor":
            resistance = component.get("resistance", 0)
            unit = component.get("resistanceUnit", "ohms")
            normalized["id"] = f"r_{resistance}_{unit.replace('ohms', 'ohm')}"
        elif component_type == "capacitor":
            capacitance = component.get("capacitance", 0)
            unit = component.get("capacitanceUnit", "F")
            cap_type = component.get("capacitorType", "")
            normalized["id"] = f"c_{capacitance}_{unit}_{cap_type}".replace(".", "_")
        elif component_type == "transistor":
            part_num = component.get("partNumber", "")
            if part_num:
                normalized["id"] = f"t_{part_num}"
            else:
                normalized["id"] = f"t_{hash(str(component)) % 10000}"
        elif component_type == "ic":
            part_num = component.get("partNumber", "")
            ic_type = component.get("icType", "")
            if part_num:
                normalized["id"] = f"ic_{part_num}"
            elif ic_type:
                normalized["id"] = f"ic_{ic_type}_{hash(str(component)) % 10000}"
            else:
                normalized["id"] = f"ic_{hash(str(component)) % 10000}"
        else:
            normalized["id"] = f"{component_type}_{hash(str(component)) % 10000}"
    else:
        normalized["id"] = component["id"]
    
    # Map component type
    component_type = component.get("@type", collection_type.rstrip("s")).lower()
    normalized["type"] = component_type
    
    # Map common fields
    normalized["quantity"] = component.get("quantity", 0)
    normalized["qty"] = f"{normalized['quantity']} pcs" if normalized["quantity"] else ""
    
    # Map type-specific fields to create description and value
    if component_type == "resistor":
        resistance = component.get("resistance", 0)
        unit = component.get("resistanceUnit", "ohms")
        normalized["value"] = f"{resistance} {unit}"
        normalized["description"] = f"Resistor {resistance} {unit}"
        
    elif component_type == "capacitor":
        capacitance = component.get("capacitance", 0)
        unit = component.get("capacitanceUnit", "F")
        cap_type = component.get("capacitorType", "")
        voltage = component.get("voltage", "")
        voltage_unit = component.get("voltageUnit", "")
        
        # Convert capacitance to more readable format
        if unit == "F" and capacitance < 1:
            if capacitance >= 1e-6:
                capacitance_str = f"{capacitance * 1e6} µF"
            elif capacitance >= 1e-9:
                capacitance_str = f"{capacitance * 1e9} nF"
            elif capacitance >= 1e-12:
                capacitance_str = f"{capacitance * 1e12} pF"
            else:
                capacitance_str = f"{capacitance} {unit}"
        else:
            capacitance_str = f"{capacitance} {unit}"
            
        normalized["value"] = capacitance_str
        desc_parts = ["Capacitor", capacitance_str]
        if cap_type:
            desc_parts.append(f"({cap_type})")
        if voltage and voltage_unit:
            desc_parts.append(f"{voltage}{voltage_unit}")
        normalized["description"] = " ".join(desc_parts)
        
    elif component_type in ["transistor", "ic"]:
        part_num = component.get("partNumber", "")
        ic_type = component.get("icType", "")
        desc_parts = [component_type.upper()]
        if part_num:
            desc_parts.append(part_num)
            normalized["partNumber"] = part_num
        if ic_type:
            desc_parts.append(f"({ic_type})")
        normalized["description"] = " ".join(desc_parts)
        normalized["value"] = part_num or ic_type or ""
        
    else:
        # Generic component
        desc = component.get("description", f"{component_type} component")
        normalized["description"] = desc
        normalized["value"] = component.get("value", "")
    
    # Copy other relevant fields
    for field in ["partNumber", "package", "tolerance", "color", "usage", "voltage", "voltageUnit"]:
        if field in component:
            normalized[field] = component[field]
    
    # Add dummy file and hash for imported components
    normalized["file"] = f"imported_from_{source_path.name}_{normalized['id']}"
    normalized["hash"] = text_hash(json.dumps(normalized, sort_keys=True))
    
    return normalized


class JSONDB:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.db_path = str(path)  # For consistent interface
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

    def normalize_type(self, type_str: str) -> str:
        """Normalize component type string."""
        return type_str.lower().strip()

    def import_db(self, path: Path) -> None:
        """Import data from another database file."""
        if not path.exists():
            return
            
        imported_data = json.loads(path.read_text())
        components_to_add = parse_jsonld_components(imported_data, path)
        
        # Add all collected components
        if components_to_add:
            self.entries.extend(components_to_add)
            self.path.write_text(json.dumps(self.entries))

    def list_all(self, limit: int | None = None, offset: int = 0) -> list[dict[str, Any]]:
        """List all components with optional pagination."""
        start = offset
        end = offset + limit if limit else None
        return self.entries[start:end]

    def search(self, query: str, field: str | None = None) -> list[dict[str, Any]]:
        """Search components by text query."""
        query_lower = query.lower()
        results = []
        
        for entry in self.entries:
            if field:
                # Search in specific field
                field_value = str(entry.get(field, "")).lower()
                if query_lower in field_value:
                    results.append(entry)
            else:
                # Search in all text fields
                searchable_text = " ".join([
                    str(entry.get("description", "")),
                    str(entry.get("type", "")),
                    str(entry.get("value", "")),
                    str(entry.get("partNumber", "")),
                ]).lower()
                if query_lower in searchable_text:
                    results.append(entry)
        
        return results

    def get_by_id(self, component_id: str) -> dict[str, Any] | None:
        """Get a specific component by ID."""
        for entry in self.entries:
            if entry.get("id") == component_id:
                return entry
        return None

    def update(self, component_id: str, updates: dict[str, Any]) -> bool:
        """Update an existing component."""
        for i, entry in enumerate(self.entries):
            if entry.get("id") == component_id:
                self.entries[i].update(updates)
                self.path.write_text(json.dumps(self.entries))
                return True
        return False

    def delete(self, component_id: str) -> bool:
        """Delete a component from the database."""
        for i, entry in enumerate(self.entries):
            if entry.get("id") == component_id:
                del self.entries[i]
                self.path.write_text(json.dumps(self.entries))
                return True
        return False

    def count(self) -> int:
        """Get total number of components in database."""
        return len(self.entries)

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        total = len(self.entries)
        types = {}
        total_qty = 0
        
        for entry in self.entries:
            # Count by type
            component_type = entry.get("type", "unknown")
            types[component_type] = types.get(component_type, 0) + 1
            
            # Sum quantities if available
            qty_str = entry.get("qty", "0")
            try:
                qty = int(qty_str.replace(" pcs", "").replace(" pc", ""))
                total_qty += qty
            except (ValueError, AttributeError):
                pass
        
        return {
            "total_components": total,
            "total_quantity": total_qty,
            "types": types,
            "most_common_type": max(types.items(), key=lambda x: x[1])[0] if types else None
        }


class SQLiteDB:
    """SQLite database backend for hardware component inventory.
    
    Stores components in a relational database with JSON data column
    for flexibility while maintaining query performance.
    """
    
    def __init__(self, path: Path) -> None:
        self.db_path = str(path)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS components (id TEXT PRIMARY KEY, file TEXT, hash TEXT, data TEXT)"
        )
        self.conn.commit()

    def has_file(self, f: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM components WHERE file = ? LIMIT 1", (f,))
        return cur.fetchone() is not None

    def has_hash(self, h: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM components WHERE hash = ? LIMIT 1", (h,))
        return cur.fetchone() is not None

    def add(self, entry: dict[str, Any], file: str, h: str) -> bool:
        if self.has_file(file) or self.has_hash(h):
            return False
        
        # Generate ID if not provided
        component_id = entry.get("id")
        if not component_id:
            import uuid
            component_id = str(uuid.uuid4())[:8]
            entry = entry.copy()
            entry["id"] = component_id
        
        self.conn.execute(
            "INSERT INTO components (id, file, hash, data) VALUES (?,?,?,?)",
            (component_id, file, h, json.dumps(entry)),
        )
        self.conn.commit()
        return True

    def normalize_type(self, type_str: str) -> str:
        """Normalize component type string."""
        return type_str.lower().strip()

    def import_db(self, path: Path) -> None:
        """Import data from another database file."""
        if not path.exists():
            return
            
        imported_data = json.loads(path.read_text())
        components_to_add = parse_jsonld_components(imported_data, path)
        
        # Add all collected components
        for entry in components_to_add:
            # Extract file and hash for SQLite storage
            file_path = entry.pop("file", "")
            hash_val = entry.pop("hash", "")
            if file_path and hash_val:
                self.add(entry, file_path, hash_val)

    def list_all(self, limit: int | None = None, offset: int = 0) -> list[dict[str, Any]]:
        """List all components with optional pagination."""
        if limit:
            cur = self.conn.execute(
                "SELECT data FROM components LIMIT ? OFFSET ?", (limit, offset)
            )
        else:
            if offset > 0:
                cur = self.conn.execute("SELECT data FROM components LIMIT -1 OFFSET ?", (offset,))
            else:
                cur = self.conn.execute("SELECT data FROM components")
        
        results = []
        for (data_json,) in cur.fetchall():
            results.append(json.loads(data_json))
        return results

    def search(self, query: str, field: str | None = None) -> list[dict[str, Any]]:
        """Search components by text query."""
        # For SQLite, we search in the JSON data field
        # This is not as efficient as proper columns but maintains flexibility
        query_lower = query.lower()
        cur = self.conn.execute("SELECT data FROM components")
        results = []
        
        for (data_json,) in cur.fetchall():
            entry = json.loads(data_json)
            
            if field:
                # Search in specific field
                field_value = str(entry.get(field, "")).lower()
                if query_lower in field_value:
                    results.append(entry)
            else:
                # Search in all text fields
                searchable_text = " ".join([
                    str(entry.get("description", "")),
                    str(entry.get("type", "")),
                    str(entry.get("value", "")),
                    str(entry.get("partNumber", "")),
                ]).lower()
                if query_lower in searchable_text:
                    results.append(entry)
        
        return results

    def get_by_id(self, component_id: str) -> dict[str, Any] | None:
        """Get a specific component by ID."""
        cur = self.conn.execute("SELECT data FROM components WHERE id = ?", (component_id,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def update(self, component_id: str, updates: dict[str, Any]) -> bool:
        """Update an existing component."""
        cur = self.conn.execute("SELECT data FROM components WHERE id = ?", (component_id,))
        row = cur.fetchone()
        if not row:
            return False
        
        entry = json.loads(row[0])
        entry.update(updates)
        
        self.conn.execute(
            "UPDATE components SET data = ? WHERE id = ?",
            (json.dumps(entry), component_id)
        )
        self.conn.commit()
        return True

    def delete(self, component_id: str) -> bool:
        """Delete a component from the database."""
        cur = self.conn.execute("DELETE FROM components WHERE id = ?", (component_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def count(self) -> int:
        """Get total number of components in database."""
        cur = self.conn.execute("SELECT COUNT(*) FROM components")
        return cur.fetchone()[0]

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        cur = self.conn.execute("SELECT data FROM components")
        total = 0
        types = {}
        total_qty = 0
        
        for (data_json,) in cur.fetchall():
            total += 1
            entry = json.loads(data_json)
            
            # Count by type
            component_type = entry.get("type", "unknown")
            types[component_type] = types.get(component_type, 0) + 1
            
            # Sum quantities if available
            qty_str = entry.get("qty", "0")
            try:
                qty = int(qty_str.replace(" pcs", "").replace(" pc", ""))
                total_qty += qty
            except (ValueError, AttributeError):
                pass
        
        return {
            "total_components": total,
            "total_quantity": total_qty,
            "types": types,
            "most_common_type": max(types.items(), key=lambda x: x[1])[0] if types else None
        }
