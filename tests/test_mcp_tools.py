"""Test suite for basic MCP tools: status, create_collection, list_collections.

This module tests the core MCP tool functionality including database connectivity,
collection management, and system status reporting.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import the MCP tools from the server
from pgvector_mcp_server.server import status, create_collection, list_collections
from pgvector_mcp_server.config import get_settings
from pgvector_mcp_server.exceptions import CollectionError, DatabaseError


class TestMCPTools:
    """Test basic MCP tools functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Note: Tests should use environment variables for API keys
        # Do not hardcode sensitive information in tests
        self.test_db_url = os.getenv("TEST_DATABASE_URL", "sqlite:///test.db")
        self.dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        
        if not self.dashscope_key:
            pytest.skip("DASHSCOPE_API_KEY environment variable not set")

    def test_status_tool_success(self):
        """Test status tool returns comprehensive system information."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.get_settings') as mock_settings:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock settings
            mock_settings.return_value.database_url = "postgresql://user:***@localhost/test"
            
            # Mock database queries
            mock_execute_result = Mock()
            mock_db.execute.return_value = mock_execute_result
            
            # Mock pgvector extension check
            mock_extension_result = Mock()
            mock_extension_result.__getitem__ = Mock(side_effect=lambda x: "0.5.1" if x == 1 else "vector")
            mock_execute_result.first.return_value = mock_extension_result
            
            # Mock collection services
            with patch('pgvector_mcp_server.server.CollectionService') as mock_coll_service, \
                 patch('pgvector_mcp_server.server.VectorService') as mock_vec_service, \
                 patch('pgvector_mcp_server.server.EmbeddingService') as mock_embed_service:
                
                mock_coll_service.return_value.get_collections.return_value = []
                mock_vec_service.return_value.get_vector_count.return_value = 0
                
                # Mock embedding service
                mock_embed_service.return_value.embed_text.return_value = [0.1] * 1024
                
                # Execute status tool
                result = status()
                
                # Verify response structure
                assert result["success"] is True
                assert "timestamp" in result
                assert "database" in result
                assert "embedding_service" in result
                assert "collections" in result
                assert "system" in result
                
                # Verify database info
                assert result["database"]["connected"] is True
                assert result["database"]["pgvector_installed"] is True
                assert result["database"]["pgvector_version"] == "0.5.1"
                
                # Verify embedding service
                assert result["embedding_service"]["available"] is True
                assert result["embedding_service"]["dimension"] == 1024

    def test_status_tool_database_error(self):
        """Test status tool handles database connection errors gracefully."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session:
            # Simulate database connection error
            mock_session.side_effect = Exception("Connection failed")
            
            result = status()
            
            assert result["success"] is False
            assert result["database"]["connected"] is False
            assert "error" in result["database"]

    def test_create_collection_success(self):
        """Test successful collection creation."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate_name, \
             patch('pgvector_mcp_server.server.validate_dimension') as mock_validate_dim:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                mock_coll_service.get_collection_by_name.return_value = None  # No existing collection
                
                # Mock created collection
                mock_collection = Mock()
                mock_collection.id = 1
                mock_collection.name = "test_collection"
                mock_collection.description = "Test description"
                mock_collection.dimension = 1024
                mock_collection.created_at.isoformat.return_value = "2025-09-23T10:00:00"
                
                mock_coll_service.create_collection.return_value = mock_collection
                
                # Execute create_collection tool
                result = create_collection("test_collection", "Test description", 1024)
                
                # Verify response
                assert result["success"] is True
                assert result["collection"]["name"] == "test_collection"
                assert result["collection"]["description"] == "Test description"
                assert result["collection"]["dimension"] == 1024
                assert result["collection"]["total_vectors"] == 0

    def test_create_collection_duplicate_name(self):
        """Test creating collection with duplicate name fails."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate_name, \
             patch('pgvector_mcp_server.server.validate_dimension') as mock_validate_dim:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                # Return existing collection
                mock_coll_service.get_collection_by_name.return_value = Mock(name="existing_collection")
                
                # Execute create_collection tool
                result = create_collection("existing_collection", "Test description")
                
                # Verify error response
                assert result["success"] is False
                assert "already exists" in result["error"]

    def test_create_collection_invalid_name(self):
        """Test creating collection with invalid name fails."""
        with patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            # Mock validation to raise error
            mock_validate.side_effect = ValueError("Invalid collection name")
            
            result = create_collection("invalid name with spaces")
            
            assert result["success"] is False
            assert "Invalid collection name" in result["error"]

    def test_list_collections_success(self):
        """Test successful collection listing."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_coll_service, \
                 patch('pgvector_mcp_server.server.VectorService') as mock_vec_service:
                
                # Mock collections
                mock_collection1 = Mock()
                mock_collection1.id = 1
                mock_collection1.name = "collection1"
                mock_collection1.description = "First collection"
                mock_collection1.dimension = 1024
                mock_collection1.created_at.isoformat.return_value = "2025-09-23T10:00:00"
                mock_collection1.updated_at = None
                
                mock_collection2 = Mock()
                mock_collection2.id = 2
                mock_collection2.name = "collection2"
                mock_collection2.description = "Second collection"
                mock_collection2.dimension = 1024
                mock_collection2.created_at.isoformat.return_value = "2025-09-23T11:00:00"
                mock_collection2.updated_at.isoformat.return_value = "2025-09-23T12:00:00"
                
                mock_collections = [mock_collection1, mock_collection2]
                
                mock_coll_service.return_value.get_collections.return_value = mock_collections
                mock_vec_service.return_value.get_vector_count.side_effect = [10, 25]  # Vector counts
                
                # Execute list_collections tool
                result = list_collections()
                
                # Verify response
                assert result["success"] is True
                assert result["total"] == 2
                assert len(result["collections"]) == 2
                
                # Verify first collection
                coll1 = result["collections"][0]
                assert coll1["name"] == "collection1"
                assert coll1["total_vectors"] == 10
                
                # Verify second collection
                coll2 = result["collections"][1]
                assert coll2["name"] == "collection2"
                assert coll2["total_vectors"] == 25
                assert coll2["updated_at"] == "2025-09-23T12:00:00"

    def test_list_collections_empty(self):
        """Test listing collections when none exist."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_service.return_value.get_collections.return_value = []
                
                result = list_collections()
                
                assert result["success"] is True
                assert result["total"] == 0
                assert result["collections"] == []

    def test_list_collections_database_error(self):
        """Test list_collections handles database errors gracefully."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session:
            # Simulate database error
            mock_session.side_effect = Exception("Database connection lost")
            
            result = list_collections()
            
            assert result["success"] is False
            assert "Database connection lost" in result["error"]

    @pytest.mark.parametrize("collection_name,expected_valid", [
        ("valid_name", True),
        ("123_numbers", True),
        ("", False),
        ("name with spaces", False),
        ("name-with-hyphens", False),
        ("very_long_name_" + "x" * 50, False),
    ])
    def test_collection_name_validation(self, collection_name, expected_valid):
        """Test collection name validation with various inputs."""
        with patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            if not expected_valid:
                mock_validate.side_effect = ValueError("Invalid name")
            else:
                mock_validate.return_value = None
            
            with patch('pgvector_mcp_server.server.get_db_session'):
                result = create_collection(collection_name)
                
                if expected_valid:
                    # If name is valid, success depends on other factors (mocked)
                    # We're just checking that validation doesn't raise an error
                    mock_validate.assert_called_once_with(collection_name)
                else:
                    assert result["success"] is False
                    assert "error" in result

    def test_tool_error_handling(self):
        """Test that all tools handle unexpected errors gracefully."""
        # Test status tool error handling
        with patch('pgvector_mcp_server.server.get_db_session', side_effect=Exception("Unexpected error")):
            result = status()
            assert result["success"] is False
            
        # Test create_collection error handling
        with patch('pgvector_mcp_server.server.get_db_session', side_effect=Exception("Unexpected error")):
            result = create_collection("test")
            assert result["success"] is False
            
        # Test list_collections error handling
        with patch('pgvector_mcp_server.server.get_db_session', side_effect=Exception("Unexpected error")):
            result = list_collections()
            assert result["success"] is False

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_mcp_tools.py -v
    pytest.main([__file__, "-v"])
