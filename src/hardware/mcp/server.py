"""MCP server for hardware management system.

Provides unified access to:
- Inventory: Component search and management
- Projects: (Future) Project and BOM management  
- Resources: (Future) Documentation and reference search
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from ..inventory import config as inventory_config
from ..inventory import utils as inventory_utils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database instances
inventory_db: inventory_utils.BaseDB | None = None


def initialize_inventory_db() -> inventory_utils.BaseDB:
    """Initialize the inventory database."""
    sqlite_path, json_path = inventory_config.resolve_db_paths()
    
    if sqlite_path:
        return inventory_utils.SQLiteDB(Path(sqlite_path))
    elif json_path:
        return inventory_utils.JSONDB(Path(json_path))
    else:
        raise RuntimeError("Could not resolve inventory database path")


# Define MCP tools
TOOLS = [
    # Inventory tools
    Tool(
        name="inventory_search",
        description="Search for hardware components using natural language query",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for components (e.g., '10k resistor', 'capacitor 100uF')"
                },
                "field": {
                    "type": "string", 
                    "description": "Optional: specific field to search in (type, value, description, etc.)",
                    "required": False
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="inventory_get_component",
        description="Get detailed information about a specific component by ID",
        inputSchema={
            "type": "object",
            "properties": {
                "component_id": {
                    "type": "string",
                    "description": "The unique ID of the component"
                }
            },
            "required": ["component_id"]
        }
    ),
    Tool(
        name="inventory_list",
        description="List components with optional filters and pagination",
        inputSchema={
            "type": "object", 
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of components to return",
                    "default": 20
                },
                "offset": {
                    "type": "integer", 
                    "description": "Number of components to skip (for pagination)",
                    "default": 0
                },
                "component_type": {
                    "type": "string",
                    "description": "Filter by component type (resistor, capacitor, etc.)",
                    "required": False
                }
            }
        }
    ),
    Tool(
        name="inventory_stats",
        description="Get statistics about the component inventory",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    
    # Future tools for projects and resources
    Tool(
        name="system_info",
        description="Get information about available hardware management modules",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
]


# Tool handlers - Inventory
async def handle_inventory_search(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle component search requests."""
    global inventory_db
    if not inventory_db:
        inventory_db = initialize_inventory_db()
    
    query = arguments.get("query", "")
    field = arguments.get("field")
    limit = arguments.get("limit", 10)
    
    try:
        results = inventory_db.search(query, field)
        
        # Limit results
        if limit and len(results) > limit:
            results = results[:limit]
        
        if not results:
            return [TextContent(
                type="text",
                text=f"No components found matching '{query}'"
            )]
        
        # Format results
        response_text = f"Found {len(results)} component(s) matching '{query}':\n\n"
        
        for i, component in enumerate(results, 1):
            comp_id = component.get("id", "unknown")[:8]
            comp_type = component.get("type", "unknown")
            value = component.get("value", "N/A")
            qty = component.get("qty", "N/A")
            desc = component.get("description", "N/A")
            
            response_text += f"{i}. ID: {comp_id}\n"
            response_text += f"   Type: {comp_type}\n"
            response_text += f"   Value: {value}\n"
            response_text += f"   Quantity: {qty}\n"
            response_text += f"   Description: {desc[:100]}{'...' if len(desc) > 100 else ''}\n\n"
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        logger.error(f"Error searching components: {e}")
        return [TextContent(
            type="text", 
            text=f"Error searching components: {str(e)}"
        )]


async def handle_inventory_get_component(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle get component by ID requests."""
    global inventory_db
    if not inventory_db:
        inventory_db = initialize_inventory_db()
    
    component_id = arguments.get("component_id", "")
    
    try:
        component = inventory_db.get_by_id(component_id)
        
        if not component:
            return [TextContent(
                type="text",
                text=f"Component with ID '{component_id}' not found"
            )]
        
        # Format component details
        response_text = f"Component Details (ID: {component_id}):\n\n"
        
        for key, value in component.items():
            if key not in ["file", "hash"]:  # Hide internal fields
                response_text += f"{key.capitalize()}: {value}\n"
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        logger.error(f"Error getting component: {e}")
        return [TextContent(
            type="text",
            text=f"Error getting component: {str(e)}"
        )]


async def handle_inventory_list(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle list components requests."""
    global inventory_db
    if not inventory_db:
        inventory_db = initialize_inventory_db()
    
    limit = arguments.get("limit", 20)
    offset = arguments.get("offset", 0)
    component_type = arguments.get("component_type")
    
    try:
        # Get all components first
        all_components = inventory_db.list_all(limit=None, offset=0)
        
        # Filter by type if specified
        if component_type:
            all_components = [
                c for c in all_components 
                if c.get("type", "").lower() == component_type.lower()
            ]
        
        # Apply pagination
        total = len(all_components)
        components = all_components[offset:offset + limit] if limit else all_components[offset:]
        
        if not components:
            return [TextContent(
                type="text",
                text="No components found in inventory"
            )]
        
        # Format results
        filter_text = f" (filtered by type: {component_type})" if component_type else ""
        response_text = f"Components in inventory{filter_text}:\n"
        response_text += f"Showing {len(components)} of {total} total components\n\n"
        
        for i, component in enumerate(components, offset + 1):
            comp_id = component.get("id", "unknown")[:8]
            comp_type = component.get("type", "unknown")
            value = component.get("value", "N/A")
            qty = component.get("qty", "N/A")
            
            response_text += f"{i}. {comp_id} - {comp_type} {value} ({qty})\n"
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        logger.error(f"Error listing components: {e}")
        return [TextContent(
            type="text",
            text=f"Error listing components: {str(e)}"
        )]


async def handle_inventory_stats(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle inventory statistics requests."""
    global inventory_db
    if not inventory_db:
        inventory_db = initialize_inventory_db()
    
    try:
        stats = inventory_db.get_stats()
        
        response_text = "Inventory Statistics:\n\n"
        response_text += f"Total components: {stats['total_components']}\n"
        response_text += f"Total quantity: {stats['total_quantity']}\n"
        
        if stats.get('most_common_type'):
            response_text += f"Most common type: {stats['most_common_type']}\n"
        
        if stats.get('types'):
            response_text += "\nComponents by type:\n"
            for comp_type, count in sorted(stats['types'].items(), key=lambda x: x[1], reverse=True):
                response_text += f"  {comp_type}: {count}\n"
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return [TextContent(
            type="text",
            text=f"Error getting inventory stats: {str(e)}"
        )]


async def handle_system_info(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle system information requests."""
    response_text = """Hardware Management System Information:

Available Modules:
• inventory - Component management with OCR extraction and CRUD operations
• projects - (Coming soon) Project and BOM management  
• resources - (Coming soon) Documentation and reference material search
• visualize - (Coming soon) Data visualization and circuit simulation UI

Current Capabilities:
• Search components by natural language query
• Get detailed component information
• List components with filtering and pagination
• View inventory statistics
• OCR-based component extraction from images
• Multiple database backends (SQLite, JSON-LD)
• Multiple OCR services (Mistral, OpenAI, OpenRouter, etc.)

Database Location:
• Auto-discovery: .hardware-inventory.db in current directory
• Fallback: $XDG_DATA_HOME/hardware/inventory-main.db

Use the inventory_* tools to interact with the component database.
"""
    
    return [TextContent(type="text", text=response_text)]


# Tool dispatch map
TOOL_HANDLERS = {
    "inventory_search": handle_inventory_search,
    "inventory_get_component": handle_inventory_get_component,
    "inventory_list": handle_inventory_list,
    "inventory_stats": handle_inventory_stats,
    "system_info": handle_system_info,
}


async def main():
    """Main MCP server entry point."""
    server = Server("hardware-management")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return TOOLS
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        if name not in TOOL_HANDLERS:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}. Available tools: {', '.join(TOOL_HANDLERS.keys())}"
            )]
        
        return await TOOL_HANDLERS[name](arguments)
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())