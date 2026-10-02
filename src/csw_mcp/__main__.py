"""Entry point for the csw-mcp server.

Run via the installed console script (`csw-mcp`) or `python -m csw_mcp`.
Uses stdio transport, per the project's v1 transport decision.
"""

from __future__ import annotations

from .server import mcp


def main() -> None:
    """Start the MCP server on stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
