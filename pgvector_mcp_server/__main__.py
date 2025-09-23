#!/usr/bin/env python3
"""
Main entry point for pgvector MCP Server when run as a module.

This allows the server to be started with:
    python -m pgvector_mcp_server
"""

import sys


def main():
    """Main entry point for the MCP server."""
    try:
        from .server import mcp
        
        # Run the MCP server
        mcp.run()
        
    except KeyboardInterrupt:
        # Gracefully handle Ctrl+C without error message
        sys.exit(0)
    except Exception as e:
        try:
            print(f"Error starting pgvector MCP server: {e}", file=sys.stderr)
        except:
            # If stderr is closed, just exit
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
