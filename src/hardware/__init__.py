"""Entry point for the ``hardware`` command line tool."""

from .inventory import cli as inventory_cli


def main(argv: list[str] | None = None) -> None:
    """Dispatch command line arguments to the appropriate handler."""
    parser = inventory_cli.build_parser()
    args = parser.parse_args(argv)

    if args.command == "inventory":
        inventory_cli.handle_inventory(args)


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
