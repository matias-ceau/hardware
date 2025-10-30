"""Pydantic models for hardware component validation and type safety.

Provides structured data models for:
- Component data validation
- OCR extraction results
- Search and query parameters
- Database operations

All models follow best practices:
- Type hints for all fields
- Field descriptions for clarity
- Default values where appropriate
- Validation logic for data integrity
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ComponentType(str, Enum):
    """Standard component types for classification."""
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    TRANSISTOR = "transistor"
    DIODE = "diode"
    IC = "ic"
    LED = "led"
    SWITCH = "switch"
    CONNECTOR = "connector"
    POTENTIOMETER = "potentiometer"
    CRYSTAL = "crystal"
    FUSE = "fuse"
    RELAY = "relay"
    TRANSFORMER = "transformer"
    SENSOR = "sensor"
    MODULE = "module"
    OTHER = "other"


class PackageType(str, Enum):
    """Standard package types for components."""
    THROUGH_HOLE = "through-hole"
    SMD = "smd"
    DIP = "dip"
    SOIC = "soic"
    QFP = "qfp"
    BGA = "bga"
    TO92 = "to-92"
    TO220 = "to-220"
    SOT23 = "sot-23"
    _0402 = "0402"
    _0603 = "0603"
    _0805 = "0805"
    _1206 = "1206"
    OTHER = "other"


class Component(BaseModel):
    """Hardware component data model with validation.
    
    Represents a single electronic component with all its properties.
    Validates data integrity and provides structured access.
    """
    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility
    
    # Core identification
    id: str = Field(description="Unique component identifier")
    type: str = Field(description="Component type (resistor, capacitor, etc.)")
    
    # Primary specifications
    value: str | None = Field(None, description="Component value (resistance, capacitance, part number)")
    qty: str | None = Field(None, description="Available quantity with unit (e.g., '10 pcs')")
    quantity: int | None = Field(None, description="Numeric quantity")
    
    # Descriptive information
    description: str | None = Field(None, description="Human-readable component description")
    partNumber: str | None = Field(None, description="Manufacturer part number")
    manufacturer: str | None = Field(None, description="Component manufacturer")
    
    # Physical characteristics
    package: str | None = Field(None, description="Package type (SMD, through-hole, DIP, etc.)")
    tolerance: str | None = Field(None, description="Component tolerance (e.g., ±5%)")
    
    # Electrical specifications
    voltage: str | None = Field(None, description="Voltage rating")
    voltageUnit: str | None = Field(None, description="Voltage unit (V, mV, kV)")
    power: str | None = Field(None, description="Power rating")
    powerUnit: str | None = Field(None, description="Power unit (W, mW)")
    
    # Additional properties
    color: str | None = Field(None, description="Component color or color code")
    usage: str | None = Field(None, description="Intended usage or application")
    notes: str | None = Field(None, description="Additional notes")
    
    # Metadata
    source: str | None = Field(None, description="Data source (OCR service, manual entry, import)")
    timestamp: str | None = Field(None, description="Creation/extraction timestamp")
    file: str | None = Field(None, description="Source file path")
    hash: str | None = Field(None, description="Content hash for deduplication")
    
    @field_validator("type")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        """Normalize component type to lowercase."""
        return v.lower().strip()
    
    @field_validator("quantity")
    @classmethod
    def extract_quantity_from_qty(cls, v: int | None, info) -> int | None:
        """Extract numeric quantity from qty string if quantity not set."""
        if v is not None:
            return v
        
        # Try to extract from qty field
        qty_str = info.data.get("qty", "")
        if qty_str:
            import re
            match = re.search(r"(\d+)", str(qty_str))
            if match:
                return int(match.group(1))
        return None


class OCRExtractionResult(BaseModel):
    """Result from OCR extraction operation.
    
    Contains the raw extracted text and parsed component data.
    """
    raw_text: str = Field(description="Raw text extracted from image")
    components: list[Component] = Field(default_factory=list, description="Parsed components")
    service: str = Field(description="OCR service used (mistral, openai, gemini, etc.)")
    model: str | None = Field(None, description="Specific model used")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @field_validator("raw_text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Ensure text is not empty."""
        if not v or not v.strip():
            raise ValueError("Extracted text cannot be empty")
        return v.strip()


class SearchQuery(BaseModel):
    """Search query parameters with validation."""
    query: str = Field(description="Search term or phrase")
    field: str | None = Field(None, description="Specific field to search (type, value, description)")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Ensure query is not empty."""
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()


class ComponentUpdate(BaseModel):
    """Update parameters for modifying component data."""
    value: str | None = None
    qty: str | None = None
    quantity: int | None = None
    description: str | None = None
    partNumber: str | None = None
    manufacturer: str | None = None
    package: str | None = None
    tolerance: str | None = None
    voltage: str | None = None
    power: str | None = None
    notes: str | None = None
    
    model_config = ConfigDict(extra="allow")  # Allow any field updates


class DatabaseStats(BaseModel):
    """Database statistics model."""
    total_components: int = Field(ge=0, description="Total number of components")
    total_quantity: int = Field(ge=0, description="Sum of all component quantities")
    types: dict[str, int] = Field(default_factory=dict, description="Count by component type")
    most_common_type: str | None = Field(None, description="Most frequently occurring type")
    database_path: str | None = Field(None, description="Path to database file")
    last_updated: str | None = Field(None, description="Last update timestamp")


class ComponentFilter(BaseModel):
    """Filter parameters for component queries."""
    type: str | None = None
    manufacturer: str | None = None
    package: str | None = None
    min_quantity: int | None = Field(None, ge=0)
    max_quantity: int | None = Field(None, ge=0)
    has_part_number: bool | None = None
    
    def matches(self, component: Component) -> bool:
        """Check if a component matches the filter criteria."""
        if self.type and component.type != self.type.lower():
            return False
        if self.manufacturer and component.manufacturer != self.manufacturer:
            return False
        if self.package and component.package != self.package:
            return False
        if self.min_quantity is not None and (component.quantity or 0) < self.min_quantity:
            return False
        if self.max_quantity is not None and (component.quantity or 0) > self.max_quantity:
            return False
        if self.has_part_number is not None:
            has_pn = bool(component.partNumber and component.partNumber.strip())
            if has_pn != self.has_part_number:
                return False
        return True
