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
    """Generate shell completion script."""
    if not argcomplete:
        console.print("[red]Error:[/] argcomplete not available")
        return
    
    match shell:
        case "bash":
            script = '''# Hardware CLI completion for Bash
# Add this to ~/.bashrc or source directly:
# . <(hardware completion bash)

_hardware_completion() {
    COMPREPLY=()
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "inventory projects resources completion info help" -- ${cur}))
        return 0
    fi
    
    case "${COMP_WORDS[1]}" in
        inventory)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=($(compgen -W "add list search show update delete stats config info ask chat test" -- ${cur}))
            fi
            ;;
        projects)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=($(compgen -W "create list show bom add-component delete" -- ${cur}))
            fi
            ;;
        resources)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=($(compgen -W "add search list extract show delete" -- ${cur}))
            fi
            ;;
        completion)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=($(compgen -W "bash zsh fish" -- ${cur}))
            fi
            ;;
    esac
}

complete -F _hardware_completion hardware'''
            print(script)
            
        case "zsh":
            script = '''# Hardware CLI completion for Zsh
# Add this to ~/.zshrc or source directly:
# . <(hardware completion zsh)

_hardware() {
    local context state line
    
    _arguments -C \
        '1: :->modules' \
        '*: :->args'
    
    case $state in
        modules)
            _values "modules" \
                "inventory[Component management]" \
                "projects[Project and BOM management]" \
                "resources[Documentation management]" \
                "completion[Shell completion]" \
                "info[System information]"
            ;;
        args)
            case $words[2] in
                inventory)
                    _values "inventory commands" \
                        "add[Add components from OCR]" \
                        "list[List components]" \
                        "search[Search components]" \
                        "show[Show component details]" \
                        "update[Update component]" \
                        "delete[Delete component]" \
                        "stats[Database statistics]" \
                        "config[Configuration management]" \
                        "info[System information]" \
                        "ask[Natural language query]" \
                        "chat[Interactive chat]" \
                        "test[API and database tests]"
                    ;;
                projects)
                    _values "project commands" \
                        "create[Create project]" \
                        "list[List projects]" \
                        "show[Show project]" \
                        "bom[Show BOM]" \
                        "add-component[Add component to BOM]" \
                        "delete[Delete project]"
                    ;;
                resources)
                    _values "resource commands" \
                        "add[Add document]" \
                        "search[Search documents]" \
                        "list[List documents]" \
                        "extract[Extract text]" \
                        "show[Show document]" \
                        "delete[Delete document]"
                    ;;
                completion)
                    _values "shells" "bash" "zsh" "fish"
                    ;;
            esac
            ;;
    esac
}

compdef _hardware hardware'''
            print(script)
            
        case "fish":
            script = '''# Hardware CLI completion for Fish
# Save to ~/.config/fish/completions/hardware.fish or source directly:
# hardware completion fish | source

# Main modules
complete -c hardware -n "not __fish_seen_subcommand_from inventory projects resources completion info" -a "inventory" -d "Component management"
complete -c hardware -n "not __fish_seen_subcommand_from inventory projects resources completion info" -a "projects" -d "Project and BOM management"  
complete -c hardware -n "not __fish_seen_subcommand_from inventory projects resources completion info" -a "resources" -d "Documentation management"
complete -c hardware -n "not __fish_seen_subcommand_from inventory projects resources completion info" -a "completion" -d "Shell completion"
complete -c hardware -n "not __fish_seen_subcommand_from inventory projects resources completion info" -a "info" -d "System information"

# Inventory subcommands
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "add" -d "Add components from OCR"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "list" -d "List components"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "search" -d "Search components"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "show" -d "Show component details"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "update" -d "Update component"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "delete" -d "Delete component"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "stats" -d "Database statistics"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "config" -d "Configuration management"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "info" -d "System information"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "ask" -d "Natural language query"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "chat" -d "Interactive chat"
complete -c hardware -n "__fish_seen_subcommand_from inventory" -a "test" -d "API and database tests"

# Projects subcommands
complete -c hardware -n "__fish_seen_subcommand_from projects" -a "create" -d "Create project"
complete -c hardware -n "__fish_seen_subcommand_from projects" -a "list" -d "List projects"
complete -c hardware -n "__fish_seen_subcommand_from projects" -a "show" -d "Show project"
complete -c hardware -n "__fish_seen_subcommand_from projects" -a "bom" -d "Show BOM"
complete -c hardware -n "__fish_seen_subcommand_from projects" -a "add-component" -d "Add component to BOM"
complete -c hardware -n "__fish_seen_subcommand_from projects" -a "delete" -d "Delete project"

# Resources subcommands  
complete -c hardware -n "__fish_seen_subcommand_from resources" -a "add" -d "Add document"
complete -c hardware -n "__fish_seen_subcommand_from resources" -a "search" -d "Search documents"
complete -c hardware -n "__fish_seen_subcommand_from resources" -a "list" -d "List documents"
complete -c hardware -n "__fish_seen_subcommand_from resources" -a "extract" -d "Extract text"
complete -c hardware -n "__fish_seen_subcommand_from resources" -a "show" -d "Show document"
complete -c hardware -n "__fish_seen_subcommand_from resources" -a "delete" -d "Delete document"

# Completion shells
complete -c hardware -n "__fish_seen_subcommand_from completion" -a "bash zsh fish" -d "Shell type"'''
            print(script)
            
        case _:
            console.print("[red]Error:[/] Unsupported shell. Available: bash, zsh, fish")


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
    console.print("• Context-aware suggestions")
    console.print("• File path completion")
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
