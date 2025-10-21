# Hardware Management System

A comprehensive Python-based system for managing electronics hardware projects, components, and documentation with AI-powered multimodal capabilities.

## 🚀 Features

### 🔧 Component Inventory
- **OCR-based extraction** from images and PDFs using multiple AI vision services (Mistral, OpenAI, OpenRouter)
- **Full CRUD operations** with SQLite and JSON-LD storage backends  
- **Natural language queries** with integrated LLM chat interface
- **Auto-discovery databases** with XDG compliance (`.hardware-inventory.db`)
- **Interactive API testing** for all OCR services
- **Shell completion** for bash/zsh/fish

### 🤖 MCP Server (Model Context Protocol)
- **Multimodal MCP server** for Claude integration with 9 tools:
  - **Inventory tools**: search, list, stats, component details
  - **OCR processing**: extract components from images/PDFs  
  - **Web search**: find datasheets and specs (Tavily API)
  - **Text embeddings**: semantic search (Jina AI + local fallback)
  - **Document conversion**: format conversion (Pandoc)
- **Async-first design** with typed parameters and error handling
- **Environment-based configuration** with graceful fallbacks

### 📋 Project Management (Framework Ready)
- Project creation and tracking infrastructure
- Bill of Materials (BOM) management foundation
- Component allocation system

### 📚 Resource Library (Framework Ready)  
- Datasheet and documentation management structure
- Search and reference system foundation
- Semantic search with embeddings
- Physics and electronics knowledge base
- Circuit reference collection

### AI Integration
- MCP Server for seamless LLM integration
- Chat interface for natural language inventory queries
- Multi-model support for OCR and text processing

## Quick Start

### Installation

```bash
git clone <repository-url>
cd hardware
uv sync  # Install dependencies
```

### Basic Usage

```bash
# Process component images
uv run hardware inventory add photos/ --service mistral

# List components
uv run hardware inventory list --limit 10

# Natural language queries
uv run hardware inventory ask "Do I have any 10k resistors?"

# Interactive chat
uv run hardware inventory chat

# System health check
uv run hardware inventory info
```

### Shell Completion

Enable autocompletion for faster CLI usage:

```bash
# Setup completion for your shell
hardware completion bash    # Instructions for Bash
hardware completion zsh     # Instructions for Zsh  
hardware completion fish    # Instructions for Fish

# After setup, get autocompletion for:
# - Commands: inventory, projects, resources
# - Subcommands: add, list, search, etc.
# - Options: --help, --service, --limit
# - File paths and arguments
```

## Documentation

### Core Commands

| Command | Description |
|---------|-------------|
| hardware inventory | Component inventory management |
| hardware projects | Project and BOM management |
| hardware resources | Documentation and reference management |
| hardware-mcp-server | MCP server for LLM integration |

## 📁 Database Location & Discovery

**IMPORTANT:** The system automatically discovers your database in this order:

### 🔍 Discovery Priority
1. **`.hardware-inventory.db`** in current directory (primary)
2. **`$XDG_DATA_HOME/hardware/inventory-main.db`** (default: `~/.local/share/hardware/inventory-main.db`)
3. **Legacy files**: `metadata.db`, `components.jsonld` in current directory
4. **Config files**: Custom paths in `~/.component_loader.toml` or `./cfg.toml`

### 🗂️ Find Your Database Location
```bash
# Check which database is being used
uv run hardware inventory info

# List components (shows database path)
uv run hardware inventory list --limit 1
```

### 📍 Common Database Locations
- **Project-specific**: `./hardware-inventory.db` (recommended for projects)
- **User-wide**: `~/.local/share/hardware/inventory-main.db` (default)
- **Custom**: Set in config files or use `--db-sqlite path/to/db.sqlite`

**💡 Tip**: Use project-specific databases by creating `.hardware-inventory.db` in your project folder

### OCR Services

| Service | Model | API Key Required | Description |
|---------|-------|------------------|-------------|
| mistral | pixtral-large-2411 | MISTRAL_API_KEY | Mistral's latest vision model (Nov 2024) |
| openai | gpt-4o-2024-11-20 | OPENAI_API_KEY | OpenAI's latest GPT-4o vision (Nov 2024) |
| gemini | gemini-2.0-flash-exp | GOOGLE_API_KEY | Google's newest multimodal model (Dec 2024) |
| anthropic | claude-3-5-sonnet-20241022 | ANTHROPIC_API_KEY | Best-in-class vision model (Oct 2024) |
| openrouter | claude-3.5-sonnet | OPENROUTER_API_KEY | Access to Claude via OpenRouter |
| local | - | None | Local Ollama instance |
| ocr.space | - | OCR_SPACE_API_KEY | OCR.Space cloud service |

## Architecture

```
hardware/
├── inventory/     # Component CRUD + OCR processing
├── projects/      # Project and BOM management  
├── resources/     # Documentation and knowledge base
├── mcp/          # Unified MCP server for LLM access
└── visualize/     # (Future) Data visualization UI
```

## Choosing the Right OCR Service

The system supports multiple cutting-edge vision models for component extraction:

| Service | Best For | Strengths | Cost |
|---------|----------|-----------|------|
| **Gemini 2.0** | General use | Fast, accurate, newest model (Dec 2024) | Low |
| **Claude 3.5 Sonnet** | Complex images | Best vision quality, detailed extraction | Medium |
| **GPT-4o (latest)** | Balanced | Great accuracy, reliable, well-tested | Medium |
| **Mistral Pixtral** | Cost-effective | Good quality, European provider | Low |
| **OpenRouter** | Flexibility | Access to multiple models via one API | Variable |

**Recommendation**: Start with **Gemini 2.0** for best speed/quality balance, or use **Claude 3.5 Sonnet** for the highest accuracy on complex component images.

## Configuration

### Environment Variables

```bash
# OCR API Keys - Use cutting-edge models for best results
export MISTRAL_API_KEY="your-mistral-key"          # Latest: pixtral-large-2411
export OPENAI_API_KEY="your-openai-key"            # Latest: gpt-4o-2024-11-20
export GOOGLE_API_KEY="your-google-key"            # Gemini 2.0 Flash (newest)
export ANTHROPIC_API_KEY="your-anthropic-key"      # Claude 3.5 Sonnet (best vision)
export OPENROUTER_API_KEY="your-openrouter-key"    # Multi-model access

# Optional: Custom data directory
export XDG_DATA_HOME="/path/to/data"
```

### Configuration Files

Create ~/.component_loader.toml or ./cfg.toml:

```toml
[main]
service = "mistral"
description = "My hardware inventory"

[database]
sqlite_path = "~/custom-inventory.db"

[tools]
preprocess = []
postprocess = []
```

## Development

### Testing

```bash
uv run pytest                    # Run all tests
uv run pytest tests/test_crud.py # Run specific tests
uv run pytest -v                # Verbose output
```

### Adding Dependencies

```bash
uv add package-name              # Add dependency
uv sync                         # Install and sync
```

## MCP Integration

The system provides an MCP server for seamless LLM integration:

```bash
# Start MCP server
uv run hardware-mcp-server

# Available MCP tools:
# - inventory_search: Search components
# - inventory_get_component: Get component details  
# - inventory_list: List components with filters
# - inventory_stats: Get inventory statistics
# - system_info: System information
```

## Examples

### Component Management

```bash
# Add components from photos using cutting-edge models
uv run hardware inventory add component-photos/ --service gemini    # Google's newest
uv run hardware inventory add component-photos/ --service anthropic # Best vision quality
uv run hardware inventory add component-photos/ --service openai    # Latest GPT-4o

# Search for specific components
uv run hardware inventory search "resistor 10k"

# Natural language queries
uv run hardware inventory ask "What capacitors do I have over 100uF?"

# Update component quantity
uv run hardware inventory update comp-123 --set qty="50 pcs"
```

### Project Workflow (Coming Soon)

```bash
# Create project
uv run hardware projects create "Arduino Weather Station"

# Add components to BOM
uv run hardware projects add-component proj-001 resistor "10k" 3

# Check component availability
uv run hardware projects bom proj-001
```

## Roadmap

- [x] Component inventory with OCR
- [x] Multiple database backends
- [x] Natural language queries
- [x] MCP server integration
- [ ] Project and BOM management
- [ ] Resource library with embeddings
- [ ] Data visualization interface
- [ ] Circuit simulation integration

## License

MIT License - see LICENSE file for details.

## AI-Powered

This system leverages multiple AI services for enhanced functionality:
- Vision AI for component recognition and OCR
- Language Models for natural queries and chat
- Embeddings for semantic search (coming soon)
- MCP Protocol for seamless LLM integration