"""Command line interface for the inventory subsystem."""

from __future__ import annotations

import argparse
from typing import Any

from .config import InventoryConfig
from .utils import generate_id, load_inventory, save_inventory


# ---------------------------------------------------------------------------
# parser construction
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hardware", description="Hardware utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    inv = sub.add_parser("inventory", help="Manage inventory records")
    inv_sub = inv.add_subparsers(dest="action", required=True)

    add_p = inv_sub.add_parser("add", help="Add an item")
    add_p.add_argument("name")
    add_p.add_argument("quantity", type=int)

    inv_sub.add_parser("list", help="List items")

    rm_p = inv_sub.add_parser("remove", help="Remove item by id")
    rm_p.add_argument("id")

    return parser


# ---------------------------------------------------------------------------
# command handlers
# ---------------------------------------------------------------------------

def handle_inventory(args: argparse.Namespace) -> None:
    cfg = InventoryConfig()
    data = load_inventory(cfg.path)

    if args.action == "add":
        item = {"id": generate_id(), "name": args.name, "quantity": args.quantity}
        data.append(item)
        save_inventory(cfg.path, data)
        print(f"Added {item['name']} with id {item['id']}")

    elif args.action == "list":
        for item in data:
            print(f"{item['id']}: {item['name']} (x{item['quantity']})")

    elif args.action == "remove":
        new_data = [it for it in data if it.get("id") != args.id]
        if len(new_data) != len(data):
            save_inventory(cfg.path, new_data)
            print(f"Removed item {args.id}")
        else:
            print(f"No item with id {args.id} found")

