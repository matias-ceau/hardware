from __future__ import annotations

import argparse
import sys
import os
import json
from datetime import datetime
from pathlib import Path
import uuid
import subprocess

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel

from . import config
from . import utils


console = Console()


def _resolve_db_paths(args: argparse.Namespace) -> utils.BaseDB:
    """Resolve database paths with new auto-discovery logic."""
    sqlite_path, json_path = config.resolve_db_paths(
        db_sqlite=args.db_sqlite,
        db_json=args.db_json
    )
    
    # SQLite is now the primary database
    if sqlite_path:
        return utils.SQLiteDB(Path(sqlite_path))
    elif json_path:
        return utils.JSONDB(Path(json_path))
    else:
        # This should not happen due to XDG fallback, but just in case
        console.print("[bold red]Error:[/] Could not resolve database path")
        sys.exit(1)


def _review(candidate: dict, db: utils.BaseDB, service: str) -> dict | None:
    table = Table()
    table.add_column("Field")
    table.add_column("Value")
    for k, v in candidate.items():
        table.add_row(k, str(v))
    console.print(table)
    if not Confirm.ask("Accept entry?", default=True):
        return None
    for k in list(candidate):
        candidate[k] = Prompt.ask(k, default=str(candidate[k]))
    candidate.setdefault("id", str(uuid.uuid4()))
    candidate.setdefault("timestamp", datetime.utcnow().isoformat())
    candidate.setdefault("source", service)
    if "type" in candidate:
        candidate["type"] = db.normalize_type(candidate["type"])
    return candidate


def _process(
    path: Path,
    db: utils.BaseDB,
    args: argparse.Namespace,
    pre: list[str],
    post: list[str],
) -> None:
    if args.resume and db.has_file(str(path)):
        return
    text = utils.ocr_extract(path, args.service)
    text_hash = utils.text_hash(text)
    if db.has_hash(text_hash):
        return
    for t in pre:
        fn = getattr(utils, t, lambda x: x)
        text = fn(text)
    candidate = utils.parse_fields(text)
    entry = _review(candidate, db, args.service)
    if entry:
        for t in post:
            fn = getattr(utils, t, lambda x: x)
            entry = fn(entry)
        db.add(entry, str(path), text_hash)


def _add_command(args: argparse.Namespace) -> None:
    """Add components from OCR processing."""
    cfg = config.CONFIG
    proc_tools = cfg.get("tools", {}).get("preprocess", [])
    post_tools = cfg.get("tools", {}).get("postprocess", [])
    
    db = _resolve_db_paths(args)
    if args.import_db:
        db.import_db(Path(args.import_db))

    exts = {e if e.startswith(".") else f".{e}" for e in args.ext.split(",")}
    target = Path(args.path)
    files: list[Path] = []
    if target.is_dir():
        files = [p for p in target.iterdir() if p.suffix.lower() in exts]
    elif target.is_file():
        files = [target]
    else:
        console.print(f"[red]Path not found: {target}")
        sys.exit(1)
    files.sort()

    for p in files:
        console.rule(p.name)
        _process(p, db, args, proc_tools, post_tools)

    console.print("[green]Done. Database updated.[/]")


def _list_command(args: argparse.Namespace) -> None:
    """List components in the database."""
    db = _resolve_db_paths(args)
    
    components = db.list_all(limit=args.limit, offset=args.offset)
    
    if not components:
        console.print("[yellow]No components found in database.[/]")
        return
    
    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Value", style="blue")
    table.add_column("Qty", style="yellow")
    table.add_column("Description", style="white")
    
    for component in components:
        table.add_row(
            component.get("id", "N/A")[:8],  # Show first 8 chars of ID
            component.get("type", "unknown"),
            component.get("value", "N/A"),
            component.get("qty", "N/A"),
            component.get("description", "N/A")[:50]  # Truncate long descriptions
        )
    
    console.print(table)
    console.print(f"\nShowing {len(components)} components")


def _search_command(args: argparse.Namespace) -> None:
    """Search components in the database."""
    db = _resolve_db_paths(args)
    
    results = db.search(args.query, args.field)
    
    if not results:
        console.print(f"[yellow]No components found matching '{args.query}'[/]")
        return
    
    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Value", style="blue")
    table.add_column("Description", style="white")
    
    for component in results:
        table.add_row(
            component.get("id", "N/A")[:8],
            component.get("type", "unknown"),
            component.get("value", "N/A"),
            component.get("description", "N/A")[:50]
        )
    
    console.print(table)
    console.print(f"\nFound {len(results)} matching components")


def _show_command(args: argparse.Namespace) -> None:
    """Show detailed information about a specific component."""
    db = _resolve_db_paths(args)
    
    component = db.get_by_id(args.id)
    
    if not component:
        console.print(f"[red]Component with ID '{args.id}' not found[/]")
        sys.exit(1)
    
    table = Table()
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in component.items():
        if key not in ["file", "hash"]:  # Hide internal fields
            table.add_row(key, str(value))
    
    console.print(table)


def _update_command(args: argparse.Namespace) -> None:
    """Update a component in the database."""
    db = _resolve_db_paths(args)
    
    # Parse field updates from --set arguments
    updates = {}
    if args.set:
        for update_str in args.set:
            if "=" in update_str:
                key, value = update_str.split("=", 1)
                updates[key.strip()] = value.strip()
    
    if not updates:
        console.print("[red]No updates specified. Use --set field=value[/]")
        sys.exit(1)
    
    success = db.update(args.id, updates)
    
    if success:
        console.print(f"[green]Component '{args.id}' updated successfully[/]")
    else:
        console.print(f"[red]Component with ID '{args.id}' not found[/]")
        sys.exit(1)


def _delete_command(args: argparse.Namespace) -> None:
    """Delete a component from the database."""
    db = _resolve_db_paths(args)
    
    # Show component details before deletion
    component = db.get_by_id(args.id)
    if not component:
        console.print(f"[red]Component with ID '{args.id}' not found[/]")
        sys.exit(1)
    
    console.print(f"[yellow]About to delete component:[/]")
    console.print(f"ID: {component.get('id', 'N/A')}")
    console.print(f"Type: {component.get('type', 'unknown')}")
    console.print(f"Description: {component.get('description', 'N/A')}")
    
    if not args.force:
        if not Confirm.ask("Are you sure you want to delete this component?"):
            console.print("[yellow]Deletion cancelled[/]")
            return
    
    success = db.delete(args.id)
    
    if success:
        console.print(f"[green]Component '{args.id}' deleted successfully[/]")
    else:
        console.print(f"[red]Failed to delete component '{args.id}'[/]")
        sys.exit(1)


def _stats_command(args: argparse.Namespace) -> None:
    """Show database statistics."""
    db = _resolve_db_paths(args)
    
    stats = db.get_stats()
    
    console.print("[bold cyan]Database Statistics[/]")
    console.print(f"Total components: {stats['total_components']}")
    console.print(f"Total quantity: {stats['total_quantity']}")
    
    if stats['most_common_type']:
        console.print(f"Most common type: {stats['most_common_type']}")
    
    if stats['types']:
        console.print("\n[bold]Components by type:[/]")
        table = Table()
        table.add_column("Type", style="green")
        table.add_column("Count", style="yellow")
        
        for comp_type, count in sorted(stats['types'].items(), key=lambda x: x[1], reverse=True):
            table.add_row(comp_type, str(count))
        
        console.print(table)


def _config_command(args: argparse.Namespace) -> None:
    """Handle config command and subcommands."""
    if args.config_subcommand == "show":
        _config_show()
    elif args.config_subcommand == "help":
        _config_help()
    elif args.config_subcommand == "paths":
        _config_paths()
    else:
        console.print("[red]Unknown config subcommand. Use 'show', 'help', or 'paths'[/]")


def _config_show() -> None:
    """Show current configuration."""
    cfg = config.CONFIG
    
    console.print("[bold cyan]Current Configuration:[/]")
    
    # Format config as JSON for better display
    config_json = json.dumps(cfg, indent=2)
    syntax = Syntax(config_json, "json", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Active Configuration", border_style="blue"))


def _config_help() -> None:
    """Show configuration help and format documentation."""
    help_text = """
[bold cyan]Configuration File Format[/]

The hardware inventory system loads configuration from TOML files in this order:
1. ~/.component_loader.toml (global user config)
2. ./cfg.toml (project-specific config - takes precedence)

[bold yellow]Example Configuration:[/]

[main]
service = "mistral"
description = "My hardware component inventory"

[database]
sqlite_path = "~/.hardware_inventory.db"
json_path = "~/hardware_components.json"

[tools]
preprocess = []
postprocess = []

[bold green]Configuration Sections:[/]

[yellow]main[/] - General settings
  • service: Default OCR service (mistral, local, ocr.space, openai, openrouter)
  • description: CLI description text

[yellow]database[/] - Database paths
  • sqlite_path: Default SQLite database location
  • json_path: Default JSON-LD database location

[yellow]tools[/] - Processing hooks
  • preprocess: Commands to run before OCR processing
  • postprocess: Commands to run after OCR processing

[yellow]Services Configuration:[/]
OCR services are configured with these endpoints:
  • mistral: https://api.mistral.ai/v1/chat/completions (requires MISTRAL_API_KEY)
  • local: http://localhost:11434/api/generate (local Ollama instance)
  • ocr.space: https://api.ocr.space/parse/image (requires API key)
  • openai: https://api.openai.com/v1/chat/completions (requires OPENAI_API_KEY)
  • openrouter: https://openrouter.ai/api/v1/chat/completions (requires OPENROUTER_API_KEY)
"""
    
    console.print(Panel(help_text, title="Configuration Help", border_style="green"))


def _config_paths() -> None:
    """Show configuration file paths and their status."""
    paths = [
        ("Global config", Path.home() / ".component_loader.toml"),
        ("Project config", Path.cwd() / "cfg.toml")
    ]
    
    table = Table()
    table.add_column("Type", style="cyan")
    table.add_column("Path", style="white")
    table.add_column("Status", style="green")
    table.add_column("Priority", style="yellow")
    
    for name, path in paths:
        exists = "✓ exists" if path.exists() else "✗ missing"
        priority = "2 (highest)" if name == "Project config" else "1 (lower)"
        table.add_row(name, str(path), exists, priority)
    
    console.print(table)
    console.print("\n[dim]Note: Project config takes precedence over global config[/]")


def _info_command(args: argparse.Namespace) -> None:
    """System health check and coordination info."""
    console.print("[bold cyan]Hardware Inventory System Info[/]")
    
    # Python environment
    console.print(f"\n[yellow]Python Environment:[/]")
    console.print(f"Python version: {sys.version.split()[0]}")
    console.print(f"Platform: {sys.platform}")
    
    # Dependencies check
    console.print(f"\n[yellow]Dependencies:[/]")
    deps_status = _check_dependencies()
    for dep, status in deps_status.items():
        status_color = "green" if status else "red"
        status_text = "✓ available" if status else "✗ missing"
        console.print(f"{dep}: [{status_color}]{status_text}[/]")
    
    # Configuration status
    console.print(f"\n[yellow]Configuration:[/]")
    cfg = config.CONFIG
    
    # Check which config files actually exist
    config_paths = [
        ("Global", Path.home() / ".component_loader.toml"),
        ("Project", Path.cwd() / "cfg.toml")
    ]
    
    config_files_found = []
    for name, path in config_paths:
        if path.exists():
            config_files_found.append(f"{name}: {path}")
    
    if config_files_found:
        console.print("[green]✓ Configuration files found:[/]")
        for file_info in config_files_found:
            console.print(f"  {file_info}")
    else:
        console.print("[yellow]⚠ No config files found - using defaults[/]")
        console.print("  Create ~/.component_loader.toml or ./cfg.toml for custom settings")
    
    console.print(f"Active service: {cfg.get('main', {}).get('service', 'mistral')}")
    
    # Database backends
    console.print(f"\n[yellow]Database Backends:[/]")
    try:
        # Test JSON backend
        test_json_path = Path("/tmp/test_hardware_inventory.json")  
        json_db = utils.JSONDB(test_json_path)
        console.print("[green]✓ JSON-LD backend available[/]")
        test_json_path.unlink(missing_ok=True)
    except Exception as e:
        console.print(f"[red]✗ JSON-LD backend error: {e}[/]")
    
    try:
        # Test SQLite backend
        test_sqlite_path = Path("/tmp/test_hardware_inventory.db")
        sqlite_db = utils.SQLiteDB(test_sqlite_path) 
        console.print("[green]✓ SQLite backend available[/]")
        test_sqlite_path.unlink(missing_ok=True)
    except Exception as e:
        console.print(f"[red]✗ SQLite backend error: {e}[/]")
    
    # OCR services
    console.print(f"\n[yellow]OCR Services:[/]")
    for service, endpoint in utils.DEFAULT_ENDPOINTS.items():
        console.print(f"{service}: {endpoint}")
    
    # API Key detection
    console.print(f"\n[yellow]API Keys:[/]")
    api_keys = _check_api_keys()
    for key_name, status in api_keys.items():
        status_color = "green" if status else "red"
        status_text = "✓ detected" if status else "✗ not found"
        console.print(f"{key_name}: [{status_color}]{status_text}[/]")
    
    # UV/package manager
    console.print(f"\n[yellow]Package Manager:[/]")
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            console.print(f"[green]✓ UV: {result.stdout.strip()}[/]")
        else:
            console.print("[red]✗ UV not working properly[/]")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[red]✗ UV not found or not responding[/]")
    
    # Project structure
    console.print(f"\n[yellow]Project Structure:[/]")
    project_files = [
        "pyproject.toml",
        "src/hardware/__init__.py", 
        "src/hardware/inventory/cli.py",
        "src/hardware/inventory/config.py",
        "src/hardware/inventory/utils.py"
    ]
    
    for file in project_files:
        path = Path(file)
        exists = "✓ present" if path.exists() else "✗ missing"
        color = "green" if path.exists() else "red"
        console.print(f"{file}: [{color}]{exists}[/]")


def _check_dependencies() -> dict[str, bool]:
    """Check if required dependencies are available."""
    deps = {}
    
    # Core dependencies
    try:
        import rich
        deps["rich"] = True
    except ImportError:
        deps["rich"] = False
    
    try:
        import requests
        deps["requests"] = True
    except ImportError:
        deps["requests"] = False
    
    try:
        import sqlite3
        deps["sqlite3"] = True
    except ImportError:
        deps["sqlite3"] = False
    
    return deps


def _ask_command(args: argparse.Namespace) -> None:
    """Handle ask command for natural language inventory queries."""
    db = _resolve_db_paths(args)
    
    # Get inventory data for context
    components = db.list_all(limit=100)  # Limit for context size
    stats = db.get_stats()
    
    # Build context
    context = f"""You are helping with a hardware component inventory system.

Inventory Statistics:
- Total components: {stats['total_components']}
- Total quantity: {stats['total_quantity']}

Recent components in inventory:
"""
    
    for i, comp in enumerate(components[:10]):  # Show first 10 for context
        context += f"- {comp.get('type', 'unknown')} {comp.get('value', '')} (qty: {comp.get('qty', 'N/A')}) - {comp.get('description', 'N/A')[:50]}\n"
    
    if len(components) > 10:
        context += f"... and {len(components) - 10} more components\n"
    
    context += f"\nUser question: {args.question}\n\nPlease provide a helpful answer based on the inventory data above."
    
    try:
        # Use OpenAI API for the question
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("[red]Error: OPENAI_API_KEY environment variable not set[/]")
            sys.exit(1)
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=args.model,
            messages=[
                {"role": "system", "content": "You are a helpful hardware inventory assistant."},
                {"role": "user", "content": context}
            ],
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        console.print(f"\n[bold cyan]Answer:[/] {answer}\n")
        
    except ImportError:
        console.print("[red]Error: openai package not installed. Install with: uv add openai[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")


def _chat_command(args: argparse.Namespace) -> None:
    """Handle interactive chat mode for inventory."""
    console.print("[bold cyan]Hardware Inventory Chat Mode[/]")
    console.print("Ask questions about your inventory. Type 'quit' to exit.\n")
    
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("[red]Error: OPENAI_API_KEY environment variable not set[/]")
            sys.exit(1)
        
        client = openai.OpenAI(api_key=api_key)
        db = _resolve_db_paths(args)
        
        # Get initial context
        stats = db.get_stats()
        context = f"""You are a hardware inventory assistant. 
        
Current inventory: {stats['total_components']} components, {stats['total_quantity']} total quantity.
Component types: {', '.join(stats.get('types', {}).keys())}

You can help with questions about finding components, checking availability, or general inventory queries."""
        
        messages = [{"role": "system", "content": context}]
        
        while True:
            try:
                question = Prompt.ask("[bold green]You")
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                messages.append({"role": "user", "content": question})
                
                response = client.chat.completions.create(
                    model=args.model,
                    messages=messages,
                    max_tokens=300
                )
                
                answer = response.choices[0].message.content
                console.print(f"[bold cyan]Assistant:[/] {answer}\n")
                
                messages.append({"role": "assistant", "content": answer})
                
                # Keep conversation history manageable
                if len(messages) > 20:
                    messages = messages[:1] + messages[-19:]  # Keep system message + last 19
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/]")
        
        console.print("[dim]Chat session ended.[/]")
        
    except ImportError:
        console.print("[red]Error: openai package not installed. Install with: uv add openai[/]")


def _check_api_keys() -> dict[str, bool]:
    """Check for API keys in environment variables."""
    api_keys = {}
    
    # Common OCR and AI service API keys
    key_patterns = {
        "OpenAI": ["OPENAI_API_KEY"],
        "OpenRouter": ["OPENROUTER_API_KEY"],
        "OCR.Space": ["OCR_SPACE_API_KEY"],
        "Anthropic": ["ANTHROPIC_API_KEY"],
        "Google": ["GOOGLE_API_KEY", "GOOGLE_CLOUD_API_KEY"],
        "Azure": ["AZURE_API_KEY", "AZURE_OPENAI_API_KEY"],
        "Mistral": ["MISTRAL_API_KEY"],
        "Groq": ["GROQ_API_KEY"],
    }
    
    for service, env_vars in key_patterns.items():
        found = any(os.getenv(var) for var in env_vars)
        api_keys[service] = found
    
    return api_keys


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point with subcommands for inventory management."""
    cfg = config.CONFIG
    service_default = cfg.get("main", {}).get("service", "mistral")
    
    parser = argparse.ArgumentParser(
        description="""
Hardware Component Inventory Management

A comprehensive CLI for managing electronics component inventory with:
• OCR-based component extraction from images and PDFs  
• Multiple database backends (JSON-LD and SQLite)
• Full CRUD operations (Create, Read, Update, Delete)
• Search and filtering capabilities
• Database statistics and analytics
• Configuration management
• System health monitoring

EXAMPLES:
  hardware-inventory add photos/ --service mistral    # Extract from images
  hardware-inventory list --limit 20                 # List components
  hardware-inventory search "10k resistor"           # Search inventory  
  hardware-inventory update r001 --set qty="50 pcs"  # Update component
  hardware-inventory config help                     # Configuration help
  hardware-inventory info                            # System health check

DATABASE OPTIONS:
  --db-json path/to/data.json     # Use JSON-LD backend
  --db-sqlite path/to/data.db     # Use SQLite backend
        """,
        prog="hardware-inventory",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--db-sqlite", help="SQLite database path")
    parser.add_argument("--db-json", help="JSON database path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add command (OCR processing)
    add_parser = subparsers.add_parser("add", help="Add components from OCR processing")
    add_parser.add_argument("path", help="Path to image/PDF files or directory")
    add_parser.add_argument("--import-db", help="Import from another database")
    add_parser.add_argument(
        "--service", default=service_default, choices=list(utils.DEFAULT_ENDPOINTS),
        help="OCR service to use"
    )
    add_parser.add_argument("--ext", default=",".join([".png", ".jpg", ".jpeg", ".pdf"]),
                           help="File extensions to process")
    add_parser.add_argument("--continue", dest="resume", action="store_true",
                           help="Resume processing, skip already processed files")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List components in database")
    list_parser.add_argument("--limit", type=int, help="Maximum number of components to show")
    list_parser.add_argument("--offset", type=int, default=0, help="Number of components to skip")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search components")
    search_parser.add_argument("query", help="Search term")
    search_parser.add_argument("--field", help="Specific field to search in")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show component details")
    show_parser.add_argument("id", help="Component ID")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update component")
    update_parser.add_argument("id", help="Component ID")
    update_parser.add_argument("--set", action="append", help="Field updates (field=value)")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete component")
    delete_parser.add_argument("id", help="Component ID")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_subcommand", help="Config subcommands")
    config_subparsers.add_parser("show", help="Show current configuration")
    config_subparsers.add_parser("help", help="Show configuration format help")
    config_subparsers.add_parser("paths", help="Show configuration file paths")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="System health check and info")
    
    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask natural language question about inventory")
    ask_parser.add_argument("question", help="Question about your inventory")
    ask_parser.add_argument("--model", default="gpt-4o", help="LLM model to use")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode for inventory")
    chat_parser.add_argument("--model", default="gpt-4o", help="LLM model to use")
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to appropriate command handler
    if args.command == "add":
        _add_command(args)
    elif args.command == "list":
        _list_command(args)
    elif args.command == "search":
        _search_command(args)
    elif args.command == "show":
        _show_command(args)
    elif args.command == "update":
        _update_command(args)
    elif args.command == "delete":
        _delete_command(args)
    elif args.command == "stats":
        _stats_command(args)
    elif args.command == "config":
        _config_command(args)
    elif args.command == "info":
        _info_command(args)
    elif args.command == "ask":
        _ask_command(args)
    elif args.command == "chat":
        _chat_command(args)
    else:
        parser.print_help()
