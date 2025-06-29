"""Entry point for the ``hardware`` command line tool."""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .inventory import cli as inventory_cli
from .projects import cli as projects_cli  
from .resources import cli as resources_cli

console = Console()


def _show_rich_help() -> None:
    """Display rich colored help for the hardware command."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Hardware Management CLI[/] - Comprehensive electronics management system",
        border_style="cyan"
    ))
    
    console.print("\n[bold yellow]DESCRIPTION[/]")
    console.print("A comprehensive system for managing electronics hardware projects, components,")
    console.print("and documentation with AI-powered OCR and natural language interfaces.")
    
    console.print("\n[bold yellow]MODULES[/]")
    
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Module", style="cyan", width=12)
    table.add_column("Status", width=10)
    table.add_column("Description", style="white")
    
    table.add_row(
        "inventory", 
        "[green]✓ Ready[/]", 
        "Component management with OCR extraction and CRUD operations"
    )
    table.add_row(
        "projects", 
        "[yellow]🚧 Framework[/]", 
        "Project and BOM (Bill of Materials) management"
    )
    table.add_row(
        "resources", 
        "[yellow]🚧 Framework[/]", 
        "Documentation, datasheets, and reference search"
    )
    console.print(table)
    
    console.print("\n[bold yellow]USAGE[/]")
    console.print("  [bold]hardware[/] [cyan]<module>[/] [dim]<command>[/] [dim][options][/]")
    console.print("  [bold]hardware-<module>[/] [dim]<command>[/] [dim][options][/]")
    
    console.print("\n[bold yellow]EXAMPLES[/]")
    examples = [
        ("hardware inventory add photos/", "Process component images with OCR"),
        ("hardware inventory ask \"Do I have 10k resistors?\"", "Natural language inventory query"),
        ("hardware inventory chat", "Interactive chat mode"),
        ("hardware projects create \"LED Matrix\"", "Create new project"),
        ("hardware resources search \"datasheet\"", "Search documentation"),
        ("hardware inventory info", "System health check"),
    ]
    
    for cmd, desc in examples:
        console.print(f"  [dim]$[/] [bold]{cmd}[/]")
        console.print(f"    [dim]{desc}[/]")
    
    console.print("\n[bold yellow]DIRECT ACCESS[/]")
    console.print("Each module can also be accessed directly:")
    console.print("  [cyan]hardware-inventory[/], [cyan]hardware-projects[/], [cyan]hardware-resources[/], [cyan]hardware-mcp-server[/]")
    
    console.print("\n[bold yellow]MORE INFO[/]")
    console.print("  hardware [cyan]<module>[/] --help    # Detailed module help")
    console.print("  hardware inventory info       # System status and configuration")
    console.print()


def main(argv: list[str] | None = None) -> None:
    """Dispatch command line arguments to the appropriate handler."""
    # Handle argument parsing
    if argv is None:
        argv = sys.argv[1:]

    # Special case: no arguments or help requested
    if not argv or argv[0] in ['-h', '--help', 'help']:
        _show_rich_help()
        return
        
    module_name = argv[0]
    remaining_args = argv[1:]
    
    # Route to appropriate module using match/case
    match module_name:
        case "inventory":
            inventory_cli.main(remaining_args)
        case "projects":
            projects_cli.main(remaining_args)
        case "resources":
            resources_cli.main(remaining_args)
        case "info":
            # Special case: show system info
            console.print("[bold cyan]Hardware Management System[/]")
            console.print("For detailed system information, use: [bold]hardware inventory info[/]")
        case _:
            # Unknown module or help request
            if module_name in ['-h', '--help', 'help']:
                _show_rich_help()
            else:
                console.print(f"[red]Error:[/] Unknown module '{module_name}'")
                console.print("Available modules: [cyan]inventory[/], [cyan]projects[/], [cyan]resources[/]")
                console.print("Use [bold]hardware --help[/] for more information.")


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
