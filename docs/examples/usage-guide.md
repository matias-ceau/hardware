# Hardware Inventory Examples

This guide provides practical examples for using the hardware inventory system with cutting-edge vision models.

## Quick Start

### Basic Setup

```bash
# Set up your API keys (choose one or more services)
export MISTRAL_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
export GOOGLE_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"

# Check system status
hardware inventory info
```

## OCR Extraction Examples

### Using Different Vision Models

```bash
# Google Gemini 2.0 Flash (newest, fastest)
hardware inventory add component-photos/ --service gemini

# Anthropic Claude 3.5 Sonnet (best accuracy)
hardware inventory add component-photos/ --service anthropic

# OpenAI GPT-4o (latest, well-tested)
hardware inventory add component-photos/ --service openai

# Mistral Pixtral Large (cost-effective)
hardware inventory add component-photos/ --service mistral

# Process a single image
hardware inventory add resistor-label.jpg --service gemini
```

### Batch Processing

```bash
# Process all images in a directory
hardware inventory add ~/electronics/components/ --service anthropic

# Process only specific file types
hardware inventory add ~/photos/ --ext png,jpg --service gemini

# Resume processing (skip already processed files)
hardware inventory add ~/photos/ --service openai --continue
```

## Database Operations

### Viewing Components

```bash
# List all components
hardware inventory list

# List with pagination
hardware inventory list --limit 20 --offset 0

# Show detailed information
hardware inventory show r001
```

### Searching

```bash
# Search by keyword
hardware inventory search "resistor"
hardware inventory search "10k"
hardware inventory search "capacitor 100uF"

# Search in specific field
hardware inventory search "SMD" --field package
hardware inventory search "resistor" --field type
```

### Updating Components

```bash
# Update quantity
hardware inventory update r001 --set qty="50 pcs"

# Update multiple fields
hardware inventory update c005 --set value="100uF" --set voltage="25V"

# Add notes
hardware inventory update ic012 --set notes="Used in power supply"
```

### Statistics

```bash
# Show database statistics
hardware inventory stats

# Example output:
# Total components: 245
# Total quantity: 1,523
# Most common type: resistor
# 
# Components by type:
# resistor      89
# capacitor     67
# ic            45
# transistor    28
# diode         16
```

## Natural Language Queries

### Using the Ask Command

```bash
# Check component availability
hardware inventory ask "Do I have any 10k resistors?"

# Find specific components
hardware inventory ask "What capacitors do I have over 100uF?"

# Get component count
hardware inventory ask "How many transistors are in inventory?"

# Check specifications
hardware inventory ask "What voltage ratings do my capacitors have?"
```

### Interactive Chat Mode

```bash
# Start interactive chat
hardware inventory chat

# Example conversation:
# You> What resistors do I have?
# Assistant> You have 89 resistors in inventory...
# 
# You> Show me capacitors above 100uF
# Assistant> Here are your capacitors above 100uF...
# 
# You> quit
```

## Import/Export

### Importing Data

```bash
# Import from another database
hardware inventory import backup-2024-01.json

# Import with confirmation
hardware inventory import external-db.json --force
```

## Database Location

### Finding Your Database

```bash
# Check current database location
hardware inventory info

# Output shows:
# 📁 CURRENT DATABASE LOCATION:
# ✓ SQLite: /home/user/.local/share/hardware/inventory-main.db
```

### Using Project-Specific Databases

```bash
# Create project-specific database (in current directory)
cd ~/projects/robot-arm/
touch .hardware-inventory.db

# Now all operations use the local database
hardware inventory add parts/ --service gemini
hardware inventory list
```

## Configuration

### Creating a Config File

Create `~/.component_loader.toml`:

```toml
[main]
service = "gemini"  # Default OCR service
description = "My electronics workshop inventory"

[database]
sqlite_path = "~/.local/share/hardware/my-inventory.db"

[tools]
preprocess = []
postprocess = []
```

Or create project-specific config `./cfg.toml`:

```toml
[main]
service = "anthropic"  # Use best quality for this project

[database]
sqlite_path = "./project-inventory.db"
```

## Testing API Connectivity

```bash
# Test all configured APIs
hardware inventory test --all

# Test specific aspects
hardware inventory test --api-keys    # Check API key availability
hardware inventory test --database    # Test database operations
hardware inventory test --ocr         # Interactive OCR testing
hardware inventory test --parsing     # Test text parsing
```

## Advanced Usage

### Model Selection Guide

| Use Case | Recommended Service | Why |
|----------|-------------------|-----|
| General purpose | Gemini 2.0 | Fastest, newest, great accuracy |
| Complex images | Claude 3.5 | Best vision, highest accuracy |
| Cost-sensitive | Mistral | Good quality, lower cost |
| Legacy/tested | OpenAI | Well-tested, reliable |

### Shell Completion

```bash
# Enable bash completion
echo '. <(hardware completion bash)' >> ~/.bashrc
source ~/.bashrc

# Enable zsh completion
echo '. <(hardware completion zsh)' >> ~/.zshrc
source ~/.zshrc

# Enable fish completion
hardware completion fish > ~/.config/fish/completions/hardware.fish
```

### Workflow Example

Complete workflow for managing a new project:

```bash
# 1. Create project directory
mkdir ~/projects/weather-station
cd ~/projects/weather-station

# 2. Create local database
touch .hardware-inventory.db

# 3. Add component photos
hardware inventory add photos/ --service gemini

# 4. Review components
hardware inventory list --limit 10

# 5. Update quantities as needed
hardware inventory update sensor001 --set qty="3 pcs"

# 6. Search for specific parts
hardware inventory search "temperature sensor"

# 7. Check inventory status
hardware inventory stats

# 8. Export for documentation
hardware inventory list > components.txt
```

## Troubleshooting

### Common Issues

**No API key error:**
```bash
# Check which keys are detected
hardware inventory info

# Set missing keys
export GOOGLE_API_KEY="your-key"
```

**Database not found:**
```bash
# Check database location
hardware inventory info

# Create default location
mkdir -p ~/.local/share/hardware
```

**OCR extraction fails:**
```bash
# Try different service
hardware inventory add photo.jpg --service anthropic

# Check API connectivity
hardware inventory test --api-keys
```

## Best Practices

1. **Use project-specific databases** for better organization
2. **Start with Gemini 2.0** for best speed/quality balance
3. **Switch to Claude 3.5** for complex/unclear images
4. **Regular backups** of your database files
5. **Use natural language queries** for quick lookups
6. **Enable shell completion** for faster CLI usage
7. **Keep API keys secure** in environment variables
8. **Review OCR results** before accepting them

## Next Steps

- Learn about [MCP Server Integration](../architecture/mcp-implementation.md)
- Explore [Project Management](./project-management.md) (coming soon)
- Set up [Resource Library](./resource-library.md) (coming soon)
