"""Test suite for pgvector MCP server.

This package contains comprehensive tests for:
- MCP tool functionality (test_mcp_tools.py)
- Collection rename operations (test_rename_collection.py) 
- Encoding detection and Windows compatibility (test_encoding.py)
- Integration workflows (test_integration.py)

To run tests:
    python -m pytest tests/ -v
    
To run specific test module:
    python -m pytest tests/test_mcp_tools.py -v

Environment variables required for testing:
    DASHSCOPE_API_KEY: API key for DashScope embedding service (for testing only)
    TEST_DATABASE_URL: Optional test database URL (defaults to SQLite)

Note: Tests use mocking extensively to avoid external dependencies.
"""
