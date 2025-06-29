"""CLI for hardware projects management."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt

try:
    import argcomplete
except ImportError:
    argcomplete = None

console = Console()


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point for projects management."""
    parser = argparse.ArgumentParser(
        description="""
Hardware Projects Management

Manage hardware projects, BOMs (Bill of Materials), and component allocation:
• Create and manage project definitions
• Track component requirements and availability
• Generate BOMs and parts lists
• Allocate components from inventory to projects

EXAMPLES:
  hardware-projects create "Arduino LED Matrix"     # Create new project
  hardware-projects list                           # List all projects
  hardware-projects show project-001               # Show project details
  hardware-projects bom project-001                # Show project BOM
  hardware-projects add-component project-001 resistor "10k" 5  # Add component to BOM
        """,
        prog="hardware-projects",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create project
    create_parser = subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--description", help="Project description")
    create_parser.add_argument("--category", help="Project category (e.g., 'Arduino', 'PCB', 'Repair')")
    
    # List projects
    list_parser = subparsers.add_parser("list", help="List all projects")
    list_parser.add_argument("--status", help="Filter by status (active, completed, archived)")
    
    # Show project
    show_parser = subparsers.add_parser("show", help="Show project details")
    show_parser.add_argument("project_id", help="Project ID")
    
    # BOM commands
    bom_parser = subparsers.add_parser("bom", help="Show project BOM")
    bom_parser.add_argument("project_id", help="Project ID")
    
    # Add component to BOM
    add_parser = subparsers.add_parser("add-component", help="Add component to project BOM")
    add_parser.add_argument("project_id", help="Project ID")
    add_parser.add_argument("component_type", help="Component type")
    add_parser.add_argument("value", help="Component value")
    add_parser.add_argument("quantity", type=int, help="Required quantity")
    add_parser.add_argument("--reference", help="Reference designator (e.g., R1, C2)")
    
    # Delete project
    delete_parser = subparsers.add_parser("delete", help="Delete project")
    delete_parser.add_argument("project_id", help="Project ID")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    # Enable argcomplete if available
    if argcomplete:
        argcomplete.autocomplete(parser)
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to command handlers
    if args.command == "create":
        _create_project(args)
    elif args.command == "list":
        _list_projects(args)
    elif args.command == "show":
        _show_project(args)
    elif args.command == "bom":
        _show_bom(args)
    elif args.command == "add-component":
        _add_component(args)
    elif args.command == "delete":
        _delete_project(args)
    else:
        parser.print_help()


def _create_project(args: argparse.Namespace) -> None:
    """Create a new project."""
    # TODO: Implement project creation
    console.print(f"[yellow]Creating project: {args.name}[/]")
    console.print("[dim]Projects functionality coming soon...[/]")


def _list_projects(args: argparse.Namespace) -> None:
    """List all projects."""
    # TODO: Implement project listing
    console.print("[yellow]Listing projects...[/]")
    console.print("[dim]Projects functionality coming soon...[/]")


def _show_project(args: argparse.Namespace) -> None:
    """Show project details."""
    # TODO: Implement project details
    console.print(f"[yellow]Showing project: {args.project_id}[/]")
    console.print("[dim]Projects functionality coming soon...[/]")


def _show_bom(args: argparse.Namespace) -> None:
    """Show project BOM."""
    # TODO: Implement BOM display
    console.print(f"[yellow]Showing BOM for project: {args.project_id}[/]")
    console.print("[dim]BOM functionality coming soon...[/]")


def _add_component(args: argparse.Namespace) -> None:
    """Add component to project BOM."""
    # TODO: Implement component addition
    console.print(f"[yellow]Adding {args.component_type} {args.value} (qty: {args.quantity}) to {args.project_id}[/]")
    console.print("[dim]Component addition functionality coming soon...[/]")


def _delete_project(args: argparse.Namespace) -> None:
    """Delete a project."""
    # TODO: Implement project deletion
    console.print(f"[yellow]Deleting project: {args.project_id}[/]")
    console.print("[dim]Project deletion functionality coming soon...[/]")


if __name__ == "__main__":
    main()