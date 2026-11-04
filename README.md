# Hardware Inventory

A small command-line inventory for electronic components. Photos or PDFs of
components (bags, reels, screenshots of orders...) are read with a vision/OCR
service, parsed into structured fields, and stored in a local database.

> The project used to also cover projects/BOMs, datasheet search and an MCP
> server. Those were removed; only the inventory remains.

## Install

```bash
uv sync
```

## Usage

```bash
uv run hardware inventory add photos/ --service mistral   # ingest images/PDFs
uv run hardware inventory list --limit 20
uv run hardware inventory search resistor
uv run hardware inventory show <id>
uv run hardware inventory update <id> --set qty="25 pcs"
uv run hardware inventory delete <id>
uv run hardware inventory stats
uv run hardware inventory ask "Do I have any 10k resistors?"
uv run hardware inventory info        # which database is active, health check
```

`hardware-inventory <command>` is equivalent to `hardware inventory <command>`.

Shell completion: `hardware completion bash|zsh|fish`.

## Database

Auto-discovered in this order:

1. `.hardware-inventory.db` in the current directory
2. `$XDG_DATA_HOME/hardware/inventory-main.db` (default `~/.local/share/hardware/inventory-main.db`)
3. Legacy `metadata.db` / `components.jsonld` in the current directory
4. Paths set in `~/.component_loader.toml` or `./cfg.toml`

Backends: SQLite (default) and JSON-LD.

## OCR services

Selected with `--service`; API keys come from the environment:

| Service      | Variable             |
|--------------|----------------------|
| `mistral`    | `MISTRAL_API_KEY`    |
| `openai`     | `OPENAI_API_KEY`     |
| `openrouter` | `OPENROUTER_API_KEY` |
| `anthropic`  | `ANTHROPIC_API_KEY`  |
| `ocr.space`  | `OCR_SPACE_API_KEY`  |
| `local`      | Ollama on `localhost:11434` |

## Tests

```bash
uv run pytest
```
