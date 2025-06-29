"""Entry point for the ``hardware`` command line tool."""

import argparse
from .inventory import cli as inventory_cli
from .projects import cli as projects_cli  
from .resources import cli as resources_cli


def main(argv: list[str] | None = None) -> None:
    """Dispatch command line arguments to the appropriate handler."""
    parser = argparse.ArgumentParser(
        description="""
Hardware Management CLI - Comprehensive hardware component inventory system

This tool provides OCR-based component extraction from images/PDFs and 
complete CRUD operations for managing your electronics component inventory.

EXAMPLES:
  hardware inventory add photos/          # Process images for components
  hardware inventory list --limit 10     # List first 10 components  
  hardware inventory ask "Do I have 10k resistors?"  # Natural language query
  hardware projects create "LED Matrix"   # Create new project
  hardware resources add datasheet.pdf    # Add component datasheet
  hardware inventory info                 # System health check

Use 'hardware inventory --help' for detailed inventory management options.
        """,
        prog="hardware",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add subcommands
    inventory_parser = subparsers.add_parser(
        "inventory", 
        help="Manage hardware inventory with OCR processing and CRUD operations"
    )
    
    projects_parser = subparsers.add_parser(
        "projects",
        help="Manage hardware projects and BOMs"
    )
    
    resources_parser = subparsers.add_parser(
        "resources", 
        help="Manage documentation, datasheets, and reference materials"
    )

    # Handle argument parsing
    if argv is None:
        import sys
        argv = sys.argv[1:]  # Get arguments from command line

    # If no arguments provided, show help
    if not argv:
        parser.print_help()
        return

    # Parse just the first argument to get the command
    try:
        args, remaining_args = parser.parse_known_args(argv)
    except SystemExit:
        return

    if args.command == "inventory":
        # Pass remaining arguments to inventory CLI
        inventory_cli.main(remaining_args)
    elif args.command == "projects":
        # Pass remaining arguments to projects CLI
        projects_cli.main(remaining_args)
    elif args.command == "resources":
        # Pass remaining arguments to resources CLI  
        resources_cli.main(remaining_args)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
