"""MCP server for hardware management system."""

import asyncio
from .server import main as async_main

def main():
    """Synchronous entry point for the MCP server."""
    asyncio.run(async_main())

__all__ = ["main"]