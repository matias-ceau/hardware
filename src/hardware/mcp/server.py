"""FastMCP server for hardware management system.

Provides unified access to:
- Inventory: Component search and management with OCR
- Projects: Project and BOM management  
- Resources: Documentation and reference search

Follows MCP best practices:
- Async-first tool design
- Typed parameters and returns using Pydantic
- Proper error handling with context
- Structured output with schemas
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent, Tool
from mcp.server import Server
from mcp.server.stdio import stdio_server

from ..inventory import config as inventory_config
from ..inventory import utils as inventory_utils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastMCP instance with proper metadata
mcp = FastMCP(
    "Hardware Management System",
    description="Electronics component inventory, project management, and documentation tools with OCR capabilities",
    dependencies=["sqlite3", "requests", "rich", "pathlib"],
)

# Global database instances
inventory_db: inventory_utils.BaseDB | None = None


# Pydantic models for type-safe tool parameters and responses

class SearchParams(BaseModel):
    """Parameters for component search."""
    query: str = Field(description="Search query for components")
    field: str | None = Field(None, description="Specific field to search in")
    limit: int = Field(10, description="Maximum number of results", le=50)

class ComponentResult(BaseModel):
    """Single component result."""
    id: str = Field(description="Component ID")
    type: str = Field(description="Component type")
    value: str | None = Field(None, description="Component value")
    quantity: str | None = Field(None, description="Available quantity")
    description: str | None = Field(None, description="Component description")

class SearchResult(BaseModel):
    """Search results with metadata."""
    components: list[ComponentResult]
    total_found: int = Field(description="Total number of matching components")
    query: str = Field(description="Original search query")

class StatsResult(BaseModel):
    """Database statistics."""
    total_components: int
    total_quantity: int
    component_types: dict[str, int]
    most_common_type: str | None

class ListParams(BaseModel):
    """Parameters for listing components."""
    limit: int = Field(20, description="Maximum number of components", le=100)
    offset: int = Field(0, description="Number of components to skip", ge=0)

class ComponentListResult(BaseModel):
    """List of components with pagination."""
    components: list[ComponentResult]
    limit: int
    offset: int
    has_more: bool = Field(description="Whether there are more components available")

# Multimodal tool models

class OCRParams(BaseModel):
    """Parameters for OCR processing."""
    url: str | None = Field(None, description="Document URL")
    file_path: str | None = Field(None, description="Local file path")
    service: str = Field("mistral", description="OCR service to use")

class OCRResult(BaseModel):
    """OCR processing result."""
    text: str = Field(description="Extracted text")
    components_found: list[ComponentResult] = Field(default_factory=list, description="Parsed components")
    service_used: str = Field(description="OCR service that was used")

class WebSearchParams(BaseModel):
    """Parameters for web search."""
    query: str = Field(description="Search query")
    max_results: int = Field(3, description="Maximum number of results", le=10)

class WebSearchResult(BaseModel):
    """Web search result."""
    query: str
    results: list[dict[str, Any]]
    answer: str | None = Field(None, description="Direct answer if available")

class EmbeddingParams(BaseModel):
    """Parameters for text embedding."""
    texts: list[str] = Field(description="Texts to embed")

class EmbeddingResult(BaseModel):
    """Embedding result."""
    embeddings: list[list[float]] = Field(description="Text embeddings")
    model_used: str = Field(description="Embedding model used")

class ConvertParams(BaseModel):
    """Parameters for document conversion."""
    url: str | None = Field(None, description="Document URL")
    file_path: str | None = Field(None, description="Local file path")
    from_format: str | None = Field(None, description="Source format")
    to_format: str = Field("markdown", description="Target format")

class ConvertResult(BaseModel):
    """Document conversion result."""
    content: str = Field(description="Converted content")
    from_format: str = Field(description="Source format")
    to_format: str = Field(description="Target format")


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
    ),
    
    # Multimodal tools
    Tool(
        name="ocr_process",
        description="Extract text and components from images or PDFs using OCR",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to image or PDF document"
                },
                "file_path": {
                    "type": "string", 
                    "description": "Local file path to process"
                },
                "service": {
                    "type": "string",
                    "description": "OCR service to use (mistral, openai, openrouter, local, ocr.space)",
                    "default": "mistral"
                }
            }
        }
    ),
    Tool(
        name="web_search",
        description="Search the web for component datasheets, specifications, and suppliers",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for datasheets, components, or specifications"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="text_embedding",
        description="Generate embeddings for semantic component search",
        inputSchema={
            "type": "object",
            "properties": {
                "texts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of texts to embed"
                }
            },
            "required": ["texts"]
        }
    ),
    Tool(
        name="convert_document",
        description="Convert documents between formats (PDF, images, markdown, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to document"
                },
                "file_path": {
                    "type": "string",
                    "description": "Local file path"
                },
                "from_format": {
                    "type": "string",
                    "description": "Source format (auto-detected if not specified)"
                },
                "to_format": {
                    "type": "string",
                    "description": "Target format",
                    "default": "markdown"
                }
            }
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


# Multimodal tool handlers

async def handle_ocr_process(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle OCR processing requests."""
    try:
        url = arguments.get("url")
        file_path = arguments.get("file_path")
        service = arguments.get("service", "mistral")
        
        if not url and not file_path:
            return [TextContent(type="text", text="Either url or file_path is required")]
        
        # Use existing OCR infrastructure
        if file_path:
            path = Path(file_path)
        else:
            # Download file from URL
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(response.content)
                    path = Path(tmp.name)
        
        # Extract text using existing OCR system
        text = inventory_utils.ocr_extract(path, service)
        
        # Parse for components
        parsed_fields = inventory_utils.parse_fields(text)
        components_found = []
        if any(parsed_fields.get(field) for field in ["value", "qty", "type"]):
            component = ComponentResult(
                id="parsed",
                type=parsed_fields.get("type", "unknown"),
                value=parsed_fields.get("value"),
                quantity=parsed_fields.get("qty"),
                description=parsed_fields.get("description")
            )
            components_found.append(component)
        
        result_text = f"OCR Text (using {service}):\n{text}\n\n"
        if components_found:
            result_text += f"Components detected: {len(components_found)}\n"
            for comp in components_found:
                result_text += f"- {comp.type}: {comp.value} ({comp.quantity})\n"
        else:
            result_text += "No components detected in the text"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"OCR processing failed: {str(e)}")]


async def handle_web_search(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle web search requests."""
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 3)
    
    # Check for Tavily API key
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        return [TextContent(type="text", text="TAVILY_API_KEY environment variable not set")]
    
    try:
        payload = {
            "api_key": tavily_api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            
        data = response.json()
        
        result_lines = [f"Web search results for: {query}\n"]
        
        if answer := data.get("answer"):
            result_lines.append(f"Answer: {answer}\n")
        
        for i, result in enumerate(data.get("results", [])[:max_results], 1):
            title = result.get("title", "No title")
            content = result.get("content", "")[:150] + "..." if len(result.get("content", "")) > 150 else result.get("content", "")
            url = result.get("url", "")
            result_lines.append(f"{i}. {title}\n{content}\n{url}\n")
        
        return [TextContent(type="text", text="\n".join(result_lines))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Web search failed: {str(e)}")]


async def handle_text_embedding(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle text embedding requests."""
    texts = arguments.get("texts", [])
    
    if not texts:
        return [TextContent(type="text", text="No texts provided for embedding")]
    
    # Check for Jina API key first
    jina_api_key = os.getenv("JINA_API_KEY")
    
    try:
        if jina_api_key:
            # Use Jina AI embeddings
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.jina.ai/v1/embeddings",
                    headers={"Authorization": f"Bearer {jina_api_key}"},
                    json={"model": "jina-embeddings-v2-base-en", "input": texts}
                )
                response.raise_for_status()
                
            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]
            model_used = "jina-embeddings-v2-base-en"
            
        else:
            # Fallback to local embeddings
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer("all-MiniLM-L6-v2")
                embeddings = model.encode(texts).tolist()
                model_used = "all-MiniLM-L6-v2 (local)"
            except ImportError:
                return [TextContent(type="text", text="No JINA_API_KEY found and sentence-transformers not installed")]
        
        result_text = f"Generated embeddings for {len(texts)} texts using {model_used}\n"
        result_text += f"Embedding dimensions: {len(embeddings[0]) if embeddings else 0}\n"
        
        # Include first few values for verification
        if embeddings:
            result_text += f"First embedding preview: [{', '.join(f'{x:.4f}' for x in embeddings[0][:5])}...]\n"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Embedding generation failed: {str(e)}")]


async def handle_convert_document(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle document conversion requests."""
    url = arguments.get("url")
    file_path = arguments.get("file_path")
    from_format = arguments.get("from_format")
    to_format = arguments.get("to_format", "markdown")
    
    if not url and not file_path:
        return [TextContent(type="text", text="Either url or file_path is required")]
    
    try:
        # Get file content
        if file_path:
            content = Path(file_path).read_bytes()
        else:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.content
        
        # Use pandoc for conversion
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            
            try:
                import pypandoc
                converted = pypandoc.convert_file(
                    tmp.name,
                    to=to_format,
                    format=from_format
                )
                
                # Truncate to 4KB limit
                if len(converted) > 4000:
                    converted = converted[:4000] + "\n... (truncated)"
                
                result_text = f"Document converted to {to_format}:\n\n{converted}"
                
            except ImportError:
                result_text = "pypandoc not installed. Install with: pip install pypandoc"
            except Exception as e:
                result_text = f"Conversion failed: {str(e)}"
            finally:
                os.unlink(tmp.name)
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Document conversion failed: {str(e)}")]


# Tool dispatch map
TOOL_HANDLERS = {
    "inventory_search": handle_inventory_search,
    "inventory_get_component": handle_inventory_get_component,
    "inventory_list": handle_inventory_list,
    "inventory_stats": handle_inventory_stats,
    "system_info": handle_system_info,
    # Multimodal tools
    "ocr_process": handle_ocr_process,
    "web_search": handle_web_search,
    "text_embedding": handle_text_embedding,
    "convert_document": handle_convert_document,
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


def run_server():
    """Sync entry point for MCP server."""
    asyncio.run(main())


if __name__ == "__main__":
    run_server()