# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a comprehensive Python hardware management system using modern Python tooling with multiple specialized submodules:

- **Package Manager**: UV (uv) for dependency management and virtual environments
- **Project Structure**: Standard Python package layout with `src/hardware/` containing specialized submodules
- **Architecture**: Modular design with unified MCP server access

### Submodules

1. **inventory/** - Component management with OCR extraction and CRUD operations
2. **projects/** - Project and BOM (Bill of Materials) management  
3. **resources/** - Documentation, datasheets, and reference search with embeddings
4. **mcp/** - Unified MCP server providing LLM access to all submodules
5. **visualize/** - (Future) Data visualization and circuit simulation UI

### Entry Points

CLI commands defined in pyproject.toml:
- `hardware` - Main CLI dispatcher routing to submodules
- `hardware-inventory` - Component inventory management
- `hardware-projects` - Project and BOM management
- `hardware-resources` - Documentation and reference management  
- `hardware-mcp-server` - MCP server for LLM integration

## Core Architecture

### Main Components

1. **CLI Layer** (`src/hardware/inventory/cli.py`): Command-line interface for processing images/PDFs and extracting component data using OCR services
2. **Configuration** (`src/hardware/inventory/config.py`): Loads settings from `~/.component_loader.toml` or `cfg.toml` in project directory
3. **Database Abstraction** (`src/hardware/inventory/utils.py`): Protocol-based design supporting both SQLite and JSON-LD storage backends
4. **Data Processing**: OCR text extraction and component field parsing with preprocessing/postprocessing hooks

### Database Backends

The system supports two storage formats through a Protocol interface with full CRUD operations:

- **SQLiteDB**: Structured relational storage with JSON data column for flexibility
- **JSONDB**: JSON-LD format storage (initial database in `data/electronics_updated_1.jsonld` can be imported for testing)

Both backends support:
- **Create**: Add new components with OCR or manual entry
- **Read**: List, search, and retrieve components with pagination
- **Update**: Modify component fields (value, quantity, description, etc.)
- **Delete**: Remove components with confirmation
- **Analytics**: Statistics, counts by type, quantity totals

### OCR Integration

Supports multiple OCR services via configurable endpoints:
- `mistral`: Mistral AI vision API (`https://api.mistral.ai/v1/chat/completions`) - requires MISTRAL_API_KEY
- `openai`: OpenAI GPT-4o vision (`https://api.openai.com/v1/chat/completions`) - requires OPENAI_API_KEY  
- `openrouter`: OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`) - requires OPENROUTER_API_KEY
- `local`: Local Ollama instance (`http://localhost:11434/api/generate`)
- `ocr.space`: OCR.Space cloud service (`https://api.ocr.space/parse/image`) - requires API key

## Development Commands

### Testing
```bash
uv run pytest                    # Run all tests
uv run pytest tests/test_config.py   # Run specific test file
uv run pytest -v                # Verbose output
uv run pytest -k "test_name"    # Run tests matching pattern
```

### Running the Application

#### Main CLI Commands
```bash
# Process images/PDFs for component extraction (via main hardware CLI)
uv run hardware inventory add <path> [options]
# note that the next 2 should be equibvalent to the first one (and uv run is not necessary for application in case they are built/installed.
hardware inventory add <path> [options]
hardware-inventory add <path> [options]

# Direct inventory CLI access with full CRUD operations
uv run hardware-inventory <command> [options]
```

#### Inventory Management Commands
```bash
# Add components from OCR processing
uv run hardware-inventory add <path> [options]
  --service mistral|openai|openrouter|local|ocr.space    # Choose OCR service
  --continue                           # Resume processing, skip already processed files
  --import-db path/to/existing.db      # Import from existing database
  --ext .png,.jpg,.jpeg,.pdf           # File extensions to process
  --comment "<comment>"                  # Optionnal natural language ressource corresponding to the data in <path>

# List components in database
uv run hardware-inventory list [options]
  --limit N                            # Maximum number of components to show
  --offset N                           # Number of components to skip (pagination)

# Search components
uv run hardware-inventory search <query> [options]
  --field <field_name>                 # Search in specific field only

# Natural language queries
uv run hardware-inventory ask "Do I have any 10k resistors?"
uv run hardware-inventory chat          # Interactive chat mode

# Show detailed component information
uv run hardware-inventory show <component_id>

# Update component information
uv run hardware-inventory update <component_id> --set field=value [--set field2=value2]

# Delete component (with confirmation)
uv run hardware-inventory delete <component_id> [--force]

# Show database statistics
uv run hardware-inventory stats

# Configuration management
uv run hardware-inventory config show   # Show current config
uv run hardware-inventory config help   # Configuration format help
uv run hardware-inventory config paths  # Show config file locations

# System information
uv run hardware-inventory info          # Health check and system info

# Database backend options (for all commands):
# --db-sqlite path/to/db.sqlite       # Use SQLite backend

# Export database to other format (not implemented) with full compatibility
uv run hardware-inventory dump [<ext>|-o <path>.ext>]
# Default dump JSON/JSON-LD, CSV, XML, parquet, RDF, turtle, markdown

# Export database or reports in a specified format (no equivalence in terms of information)
uv run hardware-inventory export [--interactive/-i] [ <choice> [<path>.ext | --type <ext>]]
```

#### Projects Management Commands
```bash
# Create and manage projects
uv run hardware-projects create "Arduino LED Matrix"
uv run hardware-projects list
uv run hardware-projects show project-001

# BOM management
uv run hardware-projects bom project-001
uv run hardware-projects add-component project-001 resistor "10k" 5
```

#### Resources Management Commands  
```bash
# Add and search documentation
uv run hardware-resources add datasheet.pdf --component "LM358"
uv run hardware-resources search "operational amplifier"
uv run hardware-resources list --type datasheet
uv run hardware-resources extract datasheet.pdf
```

#### MCP Server
```bash
# Start MCP server for LLM integration
uv run hardware-mcp-server
```

#### Shell Completion
```bash
# Setup autocompletion for your shell
uv run hardware completion bash     # Bash setup instructions
uv run hardware completion zsh      # Zsh setup instructions  
uv run hardware completion fish     # Fish setup instructions
```

#### Usage Examples
```bash
# Add components from images in a directory
uv run hardware-inventory add photos/ --service mistral --db-json components.json

# List first 10 components
uv run hardware-inventory list --limit 10 --db-json components.json

# Search for resistors
uv run hardware-inventory search resistor --db-json components.json

# Update a component's quantity
uv run hardware-inventory update r001 --set qty="25 pcs" --db-json components.json

# Show database statistics
uv run hardware-inventory stats --db-json components.json
```

### Development Setup
```bash
uv sync                          # Install dependencies and sync virtual environment
uv add <package>                 # Add new dependency
uv remove <package>              # Remove dependency
```

## Configuration

### Database Auto-Discovery

The system automatically discovers databases with this precedence:
1. **Local discovery**: `.hardware-inventory.db` in current directory
2. **XDG fallback**: `$XDG_DATA_HOME/hardware/inventory-main.db` (default: `~/.local/share/hardware/inventory-main.db`)
3. **Legacy support**: `metadata.db` and `components.jsonld` in current directory
4. **Config override**: Paths specified in configuration files

### Configuration Files

The system loads configuration from TOML files:
1. `~/.component_loader.toml` (global)
2. `./cfg.toml` (project-specific, takes precedence)

Key configuration sections:
- `[main]`: Default service, description
- `[database]`: Override default SQLite/JSON-LD paths  
- `[tools]`: Preprocessing and postprocessing hooks

### API Keys

Required environment variables for OCR services:
- `MISTRAL_API_KEY` - For Mistral vision API
- `OPENAI_API_KEY` - For OpenAI GPT-4o vision
- `OPENROUTER_API_KEY` - For OpenRouter API access
- `OCR_SPACE_API_KEY` - For OCR.Space cloud service

## Testing Strategy

Tests use pytest with comprehensive coverage:
- `conftest.py`: Sets up Python path for imports
- `test_config.py`: Configuration loading and precedence
- `test_db.py`: Basic database backend functionality
- `test_ocr.py`: OCR text extraction and parsing
- `test_crud.py`: Full CRUD operations for both database backends
- Uses protocol-based design for easy mocking of database backends

Run all tests: `uv run pytest -v`
Run specific test module: `uv run pytest tests/test_crud.py -v`

## Submodule Accessibility Guidelines

- Accessible submodules should allow the mainmodule-submodule syntax as well as mainmodule submodule
