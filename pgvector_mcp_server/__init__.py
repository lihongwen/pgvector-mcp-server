"""
pgvector MCP Server - A Model Context Protocol server for vector database operations.

This package provides a comprehensive MCP server for managing PostgreSQL collections 
with pgvector extension, supporting document processing, vector search, and collection management.
"""

# Lazy imports to avoid requiring database configuration for basic package info
_app = None


def _get_app():
    """Get the MCP server app instance (lazy loaded)."""
    global _app
    if _app is None:
        from .server import mcp
        _app = mcp
    return _app


# Make app available through property access
class AppProxy:
    def __getattr__(self, name):
        return getattr(_get_app(), name)
        
    def run(self):
        """Run the MCP server."""
        return _get_app().run()


app = AppProxy()

__version__ = "1.0.0"
__author__ = "FastAI Team"
__description__ = "Model Context Protocol server for PostgreSQL vector database management with pgvector extension"

# Main components available for import
__all__ = [
    # Core server
    "app",
    "run_server",
    # Package info
    "__version__",
    "__author__",
    "__description__",
]


def run_server():
    """
    Convenience function to run the MCP server.
    
    This is the main entry point for programmatic usage:
    
    Example:
        from pgvector_mcp_server import run_server
        run_server()
    """
    app.run()


# Lazy import functions for advanced usage
def get_settings():
    """Get application settings (lazy loaded)."""
    from .config import get_settings
    return get_settings()


def get_database_session():
    """Get database session (lazy loaded)."""
    from .database import get_db_session
    return get_db_session()