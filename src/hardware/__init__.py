from __future__ import annotations

import argparse

from .inventory.cli import main as inventory_main


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="hardware")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("inventory", help="Component loader", add_help=False)

    ns, remaining = parser.parse_known_args(argv)
    if ns.command == "inventory":
        inventory_main(remaining)
    else:
        parser.print_help()

