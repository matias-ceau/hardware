# MCP Server Implementation Guide

This document describes the implementation of the Hardware Management System's Model Context Protocol (MCP) server, following the best practices outlined in the [architecture memo](memo.md).

## Architecture Overview

The hardware inventory system provides MCP integration through two server implementations:

1. **Legacy MCP Server** (`src/hardware/mcp/server.py`) - Original stdio-based server
2. **Modern FastMCP Server** (`src/hardware/mcp/fastmcp_server.py`) - Production-ready HTTP server

## FastMCP Implementation

### Key Features

✅ **Async-first design** - All tools use `async def` with proper Context usage  
✅ **Typed parameters** - Pydantic models for input validation and documentation  
✅ **Structured output** - Automatic schema generation from return type annotations  
✅ **Error handling** - Proper exception handling with context logging  
✅ **Progress reporting** - Uses `ctx.info()` for long operations  
✅ **Concise output** - Results under 4KB with proper pagination  

### Available Tools

#### 1. Search Components
- **Purpose**: Search inventory using natural language queries
- **Input**: `SearchParams` (query, optional field, limit)
- **Output**: `SearchResult` with typed component list
- **Example**: Search for "10k resistor" or "capacitor 100uF"

#### 2. Get Inventory Statistics  
- **Purpose**: Get comprehensive database statistics
- **Input**: None (Context only)
- **Output**: `StatsResult` with counts and breakdowns
- **Features**: Total components, quantities, type distribution

#### 3. List Components
- **Purpose**: Paginated component listing
- **Input**: `ListParams` (limit, offset) 
- **Output**: `ComponentListResult` with pagination metadata
- **Features**: Efficient pagination with `has_more` indicator

#### 4. Get Component Details
- **Purpose**: Detailed component information by ID
- **Input**: `ComponentDetailsParams` (component_id)
- **Output**: `ComponentDetails` with full metadata
- **Features**: Structured fields + flexible metadata dict

### Data Models

All tools use strongly-typed Pydantic models:

```python
class ComponentResult(BaseModel):
    id: str
    type: str  
    value: str | None
    quantity: str | None
    description: str | None

class SearchResult(BaseModel):
    components: list[ComponentResult]
    total_found: int
    query: str
```

### Database Integration

- **Auto-discovery**: Uses `inventory_config.resolve_db_paths()`
- **SQLite primary**: `.hardware-inventory.db` in current directory
- **XDG fallback**: `~/.local/share/hardware/inventory-main.db`
- **Multiple backends**: SQLite and JSON-LD support

## Deployment

### Development
```bash
# Run locally
uv run python -m hardware.mcp.fastmcp_server

# With custom port
PORT=8080 uv run python -m hardware.mcp.fastmcp_server
```

### Production
```bash
# Docker deployment
hardware-mcp-server  # Uses FastMCP HTTP transport

# Claude Desktop integration  
mcp install hardware.mcp.server  # Uses stdio transport
```

### Configuration

Environment variables:
- `PORT`: HTTP server port (default: 8080)
- `XDG_DATA_HOME`: Custom data directory path
- Add any OCR API keys for future multimodal tools

## Testing

### Unit Tests
```bash
# Test MCP tools
uv run pytest tests/test_mcp_tools.py -v

# Test with real database
uv run hardware-inventory test --database
```

### Manual Testing
```bash
# Test HTTP endpoints
curl -X POST http://localhost:8080/tools/search_components \
  -H "Content-Type: application/json" \
  -d '{"params":{"query":"resistor","limit":5}}'

# Test via MCP client
mcp connect http://localhost:8080
```

## Best Practices Applied

### 1. Async-First Design
- All tools are `async def` functions
- Proper `await` usage for database operations
- Non-blocking I/O with context reporting

### 2. Type Safety
- Pydantic models for all inputs/outputs
- Automatic JSON schema generation
- Runtime validation with helpful error messages

### 3. Error Handling
- Try/catch blocks with context logging
- User-friendly error messages
- Proper exception propagation

### 4. Progress & Observability
- `ctx.info()` for operation progress
- `ctx.error()` for error logging
- Structured logging for production monitoring

### 5. Output Size Management
- Pagination for large result sets
- 4KB output limit compliance
- `has_more` indicators for UX

## Future Enhancements

### Multimodal Tools
Following the starter kit pattern, add:
- **OCR Tools**: Image/PDF component extraction
- **STT Tools**: Audio component specifications
- **Search Tools**: Web search for datasheets
- **Convert Tools**: Format conversion (PDF, images)
- **Embed Tools**: Semantic component search

### Authentication
- API key validation for protected endpoints
- OAuth scopes for read/write operations
- Rate limiting for public deployments

### Monitoring
- Prometheus metrics export
- Tool latency tracking
- Success/error rate monitoring
- Custom dashboards for inventory insights

## Related Documentation

- [Architecture Memo](memo.md) - MCP best practices and guidelines
- [Starter Kit](../examples/starter-kit.md) - Multimodal MCP server template
- [Hardware CLI Guide](../../CLAUDE.md) - CLI integration and usage
- [Testing Guide](../testing.md) - Comprehensive testing strategies