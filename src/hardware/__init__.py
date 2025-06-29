"""Entry point for the ``hardware`` command line tool."""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    import argcomplete
except ImportError:
    argcomplete = None

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
    
    console.print("\n[bold yellow]SHELL COMPLETION[/]")
    console.print("  hardware completion bash      # Generate bash completion script")
    console.print("  hardware completion zsh       # Generate zsh completion script")
    console.print("  hardware completion fish      # Generate fish completion script")
    
    console.print("\n[bold yellow]MORE INFO[/]")
    console.print("  hardware [cyan]<module>[/] --help    # Detailed module help")
    console.print("  hardware inventory info       # System status and configuration")
    console.print()


def _generate_completion_script(shell: str) -> None:
    """Generate shell completion script using argcomplete."""
    if not argcomplete:
        print("Error: argcomplete not available", file=sys.stderr)
        return
    
    # Create a parser that matches our CLI structure
    parser = argparse.ArgumentParser(prog='hardware')
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='module', help='Hardware management modules')
    
    # Inventory subcommand
    inventory_parser = subparsers.add_parser('inventory', help='Component management')
    inventory_subparsers = inventory_parser.add_subparsers(dest='command')
    inventory_subparsers.add_parser('add', help='Add components from OCR')
    inventory_subparsers.add_parser('import', help='Import from database')
    inventory_subparsers.add_parser('list', help='List components')
    inventory_subparsers.add_parser('search', help='Search components')
    inventory_subparsers.add_parser('show', help='Show component details')
    inventory_subparsers.add_parser('update', help='Update component')
    inventory_subparsers.add_parser('delete', help='Delete component')
    inventory_subparsers.add_parser('stats', help='Database statistics')
    inventory_subparsers.add_parser('config', help='Configuration management')
    inventory_subparsers.add_parser('info', help='System information')
    inventory_subparsers.add_parser('ask', help='Natural language query')
    inventory_subparsers.add_parser('chat', help='Interactive chat')
    inventory_subparsers.add_parser('test', help='API and database tests')
    
    # Projects subcommand  
    projects_parser = subparsers.add_parser('projects', help='Project and BOM management')
    projects_subparsers = projects_parser.add_subparsers(dest='command')
    projects_subparsers.add_parser('create', help='Create project')
    projects_subparsers.add_parser('list', help='List projects')
    projects_subparsers.add_parser('show', help='Show project')
    projects_subparsers.add_parser('bom', help='Show BOM')
    projects_subparsers.add_parser('add-component', help='Add component to BOM')
    projects_subparsers.add_parser('delete', help='Delete project')
    
    # Resources subcommand
    resources_parser = subparsers.add_parser('resources', help='Documentation management')
    resources_subparsers = resources_parser.add_subparsers(dest='command')
    resources_subparsers.add_parser('add', help='Add document')
    resources_subparsers.add_parser('search', help='Search documents')
    resources_subparsers.add_parser('list', help='List documents')
    resources_subparsers.add_parser('extract', help='Extract text')
    resources_subparsers.add_parser('show', help='Show document')
    resources_subparsers.add_parser('delete', help='Delete document')
    
    # Completion subcommand
    completion_parser = subparsers.add_parser('completion', help='Shell completion')
    completion_parser.add_argument('shell', choices=['bash', 'zsh', 'fish'], help='Shell type')
    
    # Info subcommand
    subparsers.add_parser('info', help='System information')
    
    # Generate completion script using argcomplete
    try:
        script = argcomplete.shellcode(['hardware'], shell=shell, argcomplete_script='hardware')
        print(script)
    except Exception as e:
        print(f"Error generating {shell} completion: {e}", file=sys.stderr)


def _show_completion_help() -> None:
    """Show completion setup help."""
    console.print(Panel.fit(
        "[bold cyan]Shell Completion Setup[/]",
        border_style="cyan"
    ))
    
    console.print("\n[bold yellow]Quick Setup:[/]")
    console.print("Add to your shell config file (~/.bashrc, ~/.zshrc, etc.):")
    console.print()
    console.print("[dim]# For Bash/Zsh:[/]")
    console.print("[cyan]. <(hardware completion bash)[/]")
    console.print()
    console.print("[dim]# For Fish:[/]") 
    console.print("[cyan]hardware completion fish | source[/]")
    console.print()
    
    console.print("[bold yellow]Available Shells:[/]")
    console.print("• [cyan]bash[/] - Bash completion script")
    console.print("• [cyan]zsh[/] - Zsh completion script") 
    console.print("• [cyan]fish[/] - Fish completion script")
    console.print()
    
    console.print("[bold yellow]Features:[/]")
    console.print("• Command completion (inventory, projects, resources)")
    console.print("• Subcommand completion (add, list, search, etc.)")
    console.print("• Optional argument completion (--help, --db-sqlite, etc.)")
    console.print("• File path completion for file arguments")
    console.print("• Context-aware suggestions powered by argcomplete")
    console.print()
    
    console.print("[bold yellow]Examples:[/]")
    console.print("  hardware completion bash > ~/hardware-completion.bash")
    console.print("  source ~/hardware-completion.bash")
    console.print()
    console.print("  echo '. <(hardware completion zsh)' >> ~/.zshrc")
    console.print()
    console.print("  hardware completion fish > ~/.config/fish/completions/hardware.fish")


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
        case "completion":
            if remaining_args and remaining_args[0] in ["bash", "zsh", "fish"]:
                _generate_completion_script(remaining_args[0])
            elif remaining_args and remaining_args[0] in ["-h", "--help"]:
                _show_completion_help()
            else:
                _show_completion_help()
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
                console.print("Available modules: [cyan]inventory[/], [cyan]projects[/], [cyan]resources[/], [cyan]completion[/]")
                console.print("Use [bold]hardware --help[/] for more information.")


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
