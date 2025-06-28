"""Entry point for the ``hardware`` command line tool."""

import argparse
from .inventory import cli as inventory_cli


def main(argv: list[str] | None = None) -> None:
    """Dispatch command line arguments to the appropriate handler."""
    parser = argparse.ArgumentParser(
        description="Hardware management command line tool",
        prog="hardware",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add inventory subcommand
    subparsers.add_parser("inventory", help="Manage hardware inventory")

    # Parse only the main command first
    if argv is None:
        argv = []

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
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
