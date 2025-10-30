# Getting Started with Hardware Management System

Welcome! This guide will help you get up and running with the Hardware Management System in under 5 minutes.

## What You'll Learn

1. Install the system
2. Set up your first OCR service
3. Extract components from a photo
4. Search and manage your inventory
5. Use natural language queries

## Prerequisites

- Python 3.12 or higher
- One of: Google, OpenAI, Anthropic, or Mistral API key (free tiers available)
- Component photos (optional for testing)

## Step 1: Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/matias-ceau/hardware
cd hardware

# Install dependencies
pip install -e .
```

### Verify Installation

```bash
# Check that the system is installed
hardware --help

# You should see the main help menu with available modules
```

## Step 2: Choose and Set Up an OCR Service

We recommend starting with **Google Gemini 2.0 Flash** - it's the newest model (Dec 2024), very fast, and has a generous free tier.

### Get a Google AI API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your key

### Set the API Key

```bash
# On Linux/macOS
export GOOGLE_API_KEY="your-api-key-here"

# On Windows (PowerShell)
$env:GOOGLE_API_KEY="your-api-key-here"

# Make it permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export GOOGLE_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Alternative Services

Don't have a Google key? No problem! Choose another:

**Anthropic Claude 3.5** (best vision quality):
```bash
# Get key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY="your-key"
```

**OpenAI GPT-4o** (reliable and well-tested):
```bash
# Get key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY="your-key"
```

**Mistral Pixtral** (cost-effective):
```bash
# Get key from: https://console.mistral.ai/
export MISTRAL_API_KEY="your-key"
```

## Step 3: System Check

Verify everything is working:

```bash
hardware inventory info
```

You should see:
- ✓ Your Python version
- ✓ Available dependencies
- ✓ API keys detected (Google/Gemini should show "✓ detected")
- ✓ Database location (will be auto-created)

## Step 4: Your First Component Extraction

### If You Have Component Photos

```bash
# Create a test directory
mkdir ~/test-components
cd ~/test-components

# Add your component photos here, then:
hardware inventory add . --service gemini

# The system will:
# 1. Process each image with AI vision
# 2. Extract component information
# 3. Ask you to review and confirm each entry
# 4. Save to your local database
```

### If You Don't Have Photos Yet

That's okay! Let's create a test database:

```bash
# Create a manual entry
hardware inventory add <(echo "10kΩ Resistor
Value: 10,000 Ohms
Tolerance: ±5%
Quantity: 25 pieces
Package: Through-hole") --service gemini
```

Or skip to the next section and explore with an empty database.

## Step 5: Explore Your Inventory

### List Components

```bash
# List all components
hardware inventory list

# List with pagination
hardware inventory list --limit 5
```

### Search Components

```bash
# Search by keyword
hardware inventory search "resistor"
hardware inventory search "10k"

# Search in specific field
hardware inventory search "resistor" --field type
```

### View Statistics

```bash
hardware inventory stats

# Shows:
# - Total components
# - Total quantity
# - Breakdown by type
# - Most common component
```

## Step 6: Natural Language Queries

One of the coolest features - ask questions in plain English!

### Set Up Chat (One-Time)

You'll need an OpenAI API key for the chat feature:

```bash
export OPENAI_API_KEY="your-openai-key"
```

### Ask Questions

```bash
# Single questions
hardware inventory ask "Do I have any 10k resistors?"
hardware inventory ask "What capacitors are in my inventory?"
hardware inventory ask "How many components do I have?"

# Interactive chat
hardware inventory chat
```

In chat mode, you can have a conversation:
```
You> What resistors do I have?
Assistant> You have 5 resistors in your inventory: 3x 10kΩ, 2x 1kΩ...

You> Show me the 10k ones
Assistant> Here are your 10kΩ resistors: R001 (25 pcs), R002 (10 pcs)...

You> quit
```

## Step 7: Update and Manage

### Update Quantities

```bash
# Update quantity
hardware inventory update r001 --set qty="15 pcs"

# Update multiple fields
hardware inventory update r001 --set value="10kΩ" --set notes="Used in power supply"
```

### Show Details

```bash
# Show full details of a component
hardware inventory show r001
```

### Delete Components

```bash
# Delete with confirmation
hardware inventory delete r001

# Delete without confirmation
hardware inventory delete r001 --force
```

## Step 8: Project-Specific Inventory

For better organization, use project-specific databases:

```bash
# Create a project
mkdir ~/projects/arduino-weather
cd ~/projects/arduino-weather

# Create local database
touch .hardware-inventory.db

# Now all commands use this database
hardware inventory add parts/ --service gemini
hardware inventory list
hardware inventory stats
```

## Common Workflows

### Workflow 1: New Project Setup

```bash
# 1. Create project
mkdir ~/projects/robot-arm
cd ~/projects/robot-arm

# 2. Initialize inventory
touch .hardware-inventory.db

# 3. Add components
hardware inventory add photos/ --service gemini

# 4. Review
hardware inventory list
hardware inventory stats
```

### Workflow 2: Adding to Existing Inventory

```bash
# 1. Navigate to project
cd ~/projects/robot-arm

# 2. Add new photos
hardware inventory add new-parts/ --service gemini

# 3. Update quantities
hardware inventory update servo-001 --set qty="5 pcs"

# 4. Check inventory
hardware inventory search "servo"
```

### Workflow 3: Organizing Mixed Components

```bash
# 1. Process all photos
hardware inventory add unsorted-photos/ --service anthropic

# 2. Search and categorize
hardware inventory search "resistor"
hardware inventory search "capacitor"

# 3. Update with notes
hardware inventory update r001 --set notes="Power supply section"
hardware inventory update c001 --set notes="Power supply section"

# 4. View by category
hardware inventory stats
```

## Tips for Success

### 1. Photo Quality Matters
- **Good**: Clear, well-lit, focused photos of components
- **Bad**: Blurry, dark, or distant shots

### 2. Choose the Right Model
- **Gemini 2.0**: Best for general use, fast, newest
- **Claude 3.5**: Best for complex/unclear images
- **GPT-4o**: Good balance, very reliable

### 3. Review Before Accepting
- Always review OCR results before accepting
- Fix any incorrect values during the review step
- You can edit later with `update` command

### 4. Use Project Databases
- One database per project keeps things organized
- Use `.hardware-inventory.db` in project root
- Global database at `~/.local/share/hardware/inventory-main.db`

### 5. Regular Backups
```bash
# Backup your database
cp .hardware-inventory.db backup-$(date +%Y%m%d).db

# Or for global database
cp ~/.local/share/hardware/inventory-main.db ~/backups/
```

## Next Steps

### Learn More
- [Complete Usage Guide](usage-guide.md) - 20+ detailed examples
- [Model Selection Guide](../README.md#choosing-the-right-ocr-service) - Choose the best AI model
- [Configuration Guide](usage-guide.md#configuration) - Customize your setup

### Advanced Features
- **MCP Integration**: Use with Claude Desktop for AI assistance
- **Project Management**: BOM tracking (coming soon)
- **Resource Library**: Datasheet management (coming soon)

### Get Help
- Run `hardware inventory info` to check system status
- Run `hardware inventory test --all` to test connectivity
- Check [Troubleshooting](../README.md#troubleshooting) for common issues

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| "API key not found" | Run `hardware inventory info` and set missing key |
| OCR fails | Try different service: `--service anthropic` |
| No components found | Check photo quality, try Claude 3.5 |
| Database error | Check path with `hardware inventory info` |
| Command not found | Reinstall: `pip install -e .` |

## Success! 🎉

You're now ready to use the Hardware Management System!

Start by adding some component photos or exploring the examples in the [Usage Guide](usage-guide.md).

**Questions?** Check the [main README](../README.md) or open an issue on GitHub.
