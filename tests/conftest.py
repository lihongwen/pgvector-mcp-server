"""Pytest configuration and shared fixtures for pgvector MCP server tests.

This module provides common test configuration and fixtures used across
all test modules.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture(autouse=True)
def env_setup():
    """Set up environment variables for testing."""
    # Ensure required environment variables are available
    if not os.getenv("DASHSCOPE_API_KEY"):
        pytest.skip("DASHSCOPE_API_KEY environment variable not set")


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_collection():
    """Provide a mock collection object for testing."""
    collection = Mock()
    collection.id = 1
    collection.name = "test_collection"
    collection.description = "Test collection for unit tests"
    collection.dimension = 1024
    collection.created_at.isoformat.return_value = "2025-09-23T10:00:00"
    collection.updated_at = None
    return collection


@pytest.fixture
def mock_vector_record():
    """Provide a mock vector record object for testing."""
    vector = Mock()
    vector.id = 1
    vector.content = "Test vector content"
    vector.extra_metadata = {"source": "test", "type": "text"}
    vector.created_at.isoformat.return_value = "2025-09-23T10:00:00"
    return vector


@pytest.fixture
def sample_test_content():
    """Provide sample content for testing."""
    return {
        "english": "Hello, world! This is a test document.",
        "chinese": "你好世界！这是一个测试文档。",
        "mixed": "Hello 你好 world 世界! Mixed content test.",
        "unicode": "Hello, world! 你好世界! 🌟 Émojis and accents: café résumé",
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "encoding: mark test as encoding-related test"
    )
    config.addinivalue_line(
        "markers", "mcp_tools: mark test as MCP tool test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test file names
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_encoding" in item.nodeid:
            item.add_marker(pytest.mark.encoding)
        elif "test_mcp_tools" in item.nodeid:
            item.add_marker(pytest.mark.mcp_tools)
