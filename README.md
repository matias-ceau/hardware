# Hardware Management System

> A modern, AI-powered electronics component inventory and project management system

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Python-based system for managing electronics hardware projects, components, and documentation with **cutting-edge AI vision models** for multimodal data ingestion.

## 📑 Table of Contents

- [What Makes This Special](#-what-makes-this-special)
- [Features](#-features)
- [Quick Start](#quick-start)
- [Choosing the Right OCR Service](#choosing-the-right-ocr-service)
- [Examples](#examples)
- [Documentation](#documentation)
- [Database Location & Discovery](#-database-location--discovery)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [AI-Powered Models](#ai-powered)
- [Development](#development)

## ✨ What Makes This Special

- 🤖 **Latest AI Models**: Uses Google Gemini 2.0, Claude 3.5, GPT-4o (Nov 2024) for component recognition
- 🔍 **Smart OCR**: Extract component data from photos with state-of-the-art vision models
- 💬 **Natural Language**: Ask questions like "Do I have any 10k resistors?" and get answers
- 🗄️ **Flexible Storage**: SQLite for performance, JSON-LD for portability
- 🔌 **MCP Integration**: Seamless LLM integration via Model Context Protocol
- 📊 **Project Ready**: Framework for BOM management and project tracking

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
# Clone the repository
git clone https://github.com/matias-ceau/hardware
cd hardware

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

**🚀 [Complete Getting Started Guide →](docs/examples/getting-started.md)**

### Set Up API Keys

Choose one or more cutting-edge vision services:

```bash
# Google Gemini 2.0 Flash (newest, Dec 2024) - Recommended!
export GOOGLE_API_KEY="your-google-key"

# Anthropic Claude 3.5 Sonnet (best vision quality)
export ANTHROPIC_API_KEY="your-anthropic-key"

# OpenAI GPT-4o (latest, Nov 2024)
export OPENAI_API_KEY="your-openai-key"

# Mistral Pixtral Large (cost-effective)
export MISTRAL_API_KEY="your-mistral-key"
```

### First Steps

```bash
# Check system status and configuration
hardware inventory info

# Extract components from photos (using newest model)
hardware inventory add component-photos/ --service gemini

# List your components
hardware inventory list --limit 10

# Search for specific parts
hardware inventory search "resistor 10k"

# Ask natural language questions
hardware inventory ask "What capacitors do I have over 100uF?"

# Interactive chat mode
hardware inventory chat
```

**📚 [See Complete Usage Guide →](docs/examples/usage-guide.md)**

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

Create `~/.component_loader.toml` for global settings:

```toml
[main]
service = "gemini"  # Default OCR service
description = "My hardware inventory"

[database]
sqlite_path = "~/.local/share/hardware/inventory-main.db"

[tools]
preprocess = []
postprocess = []
```

Or `./cfg.toml` for project-specific settings (takes precedence).

**📖 [Configuration Guide →](docs/examples/usage-guide.md#configuration)**

## Troubleshooting

### Common Issues

**"API key not found" error:**
```bash
# Check which keys are detected
hardware inventory info

# Set the missing key
export GOOGLE_API_KEY="your-key-here"
```

**"Database not found" error:**
```bash
# Check database location
hardware inventory info

# The system auto-creates databases, but you can create manually:
mkdir -p ~/.local/share/hardware
```

**OCR extraction fails:**
```bash
# Try a different service
hardware inventory add photo.jpg --service anthropic

# Test API connectivity
hardware inventory test --api-keys
```

**No components found after extraction:**
- Check the image quality (clear, well-lit photos work best)
- Try Claude 3.5 for better accuracy: `--service anthropic`
- Review the OCR output manually to verify text extraction

### Getting Help

1. **Check system info**: `hardware inventory info`
2. **Run tests**: `hardware inventory test --all`
3. **Review logs**: Check console output for detailed error messages
4. **Read docs**: See [usage guide](docs/examples/usage-guide.md) for examples

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
hardware inventory add component-photos/ --service gemini    # Google's newest
hardware inventory add component-photos/ --service anthropic # Best vision quality
hardware inventory add component-photos/ --service openai    # Latest GPT-4o

# Search for specific components
hardware inventory search "resistor 10k"
hardware inventory search "capacitor" --field type

# Natural language queries
hardware inventory ask "What capacitors do I have over 100uF?"
hardware inventory ask "Do I have any SMD resistors?"

# Update component quantity
hardware inventory update comp-123 --set qty="50 pcs"
hardware inventory update r001 --set notes="Used in power supply"

# View statistics
hardware inventory stats
```

### Interactive Workflows

```bash
# Interactive chat for inventory queries
hardware inventory chat

# Example conversation:
# You> What resistors do I have?
# Assistant> You have 89 resistors in inventory, including...
#
# You> Show me capacitors above 100uF
# Assistant> Here are your capacitors above 100uF...
```

### Project-Specific Inventory

```bash
# Create a project directory with its own inventory
mkdir ~/projects/robot-arm
cd ~/projects/robot-arm
touch .hardware-inventory.db

# Now all commands use this project's database
hardware inventory add parts/ --service gemini
hardware inventory list
hardware inventory stats
```

**📚 [See Complete Examples →](docs/examples/usage-guide.md)**

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

## AI-Powered

This system leverages the **latest cutting-edge AI models** (as of Dec 2024) for enhanced functionality:

| Service | Model | Release | Best For |
|---------|-------|---------|----------|
| Google Gemini | 2.0 Flash Exp | Dec 2024 | Fastest, newest, great balance |
| Anthropic | Claude 3.5 Sonnet | Oct 2024 | Best vision quality, complex images |
| OpenAI | GPT-4o (Nov 2024) | Nov 2024 | Reliable, well-tested, consistent |
| Mistral | Pixtral Large | Nov 2024 | Cost-effective, European provider |

**Recommendation**: Start with **Gemini 2.0** for optimal speed and quality, switch to **Claude 3.5** for maximum accuracy on challenging images.

## License

MIT License - see LICENSE file for details.