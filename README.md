# Hardware

**Hardware** is a small experimental command-line tool for keeping track of computer parts and other equipment. The current code base only prints a greeting but is structured to eventually support an inventory subcommand.

## Installation

Use `pip` to install the project in editable mode during development:

```bash
pip install -e .
```

This installs the `hardware` command.

## Example usage

Run the command after installation:

```bash
hardware inventory
```

This currently prints `Hello from hardware!` but will be extended with real inventory management features.

## Configuration file schema

Configuration is expected in `cfg.toml`. An excerpt from the documentation shows the schema:

```toml
[main]
# Purpose / description of this loader
description = "Component OCR & DB updater"
# Which extraction model to use by default
service     = "mistral"    # or "tavily", "ocr-space"
# How many concurrent uploads (if you ever batch)
concurrency = 1

[database]
# Default file names or paths
sqlite_path = "metadata.db"
jsonld_path = "components.jsonld"

[tools]
# Define optional preprocessing or postprocessing steps
# Each tool can have its own command or script to run.
# This mimics an MCP-like “toolchain” concept without needing a real MCP.
preprocess  = ["trim_whitespace", "normalize_unicode"]
postprocess = ["validate_schema", "dedupe_entries"]
```

See `docs/dev/conv_ref.md` for full details.
