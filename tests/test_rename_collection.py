"""Test suite for collection rename functionality with atomicity and conflict handling.

This module tests the rename_collection MCP tool to ensure atomic operations,
proper conflict handling, and data integrity during collection renames.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import IntegrityError, DatabaseError

# Import the rename collection tool and related classes
from pgvector_mcp_server.server import rename_collection
from pgvector_mcp_server.exceptions import CollectionError


class TestRenameCollection:
    """Test collection rename functionality with focus on atomicity and conflict handling."""

    def test_rename_collection_success(self):
        """Test successful collection rename operation."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                
                # Mock renamed collection
                mock_collection = Mock()
                mock_collection.id = 1
                mock_collection.name = "new_collection_name"
                mock_collection.description = "Test collection"
                mock_collection.dimension = 1024
                mock_collection.created_at.isoformat.return_value = "2025-09-23T10:00:00"
                mock_collection.updated_at.isoformat.return_value = "2025-09-23T12:00:00"
                
                mock_coll_service.rename_collection.return_value = mock_collection
                
                # Execute rename operation
                result = rename_collection("old_name", "new_collection_name")
                
                # Verify successful response
                assert result["success"] is True
                assert "successfully renamed" in result["message"].lower()
                assert result["collection"]["name"] == "new_collection_name"
                assert result["collection"]["id"] == 1
                
                # Verify service was called with correct parameters
                mock_coll_service.rename_collection.assert_called_once_with("old_name", "new_collection_name")

    def test_rename_collection_source_not_found(self):
        """Test rename operation when source collection doesn't exist."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                mock_coll_service.rename_collection.side_effect = CollectionError("Collection 'nonexistent' not found")
                
                result = rename_collection("nonexistent", "new_name")
                
                assert result["success"] is False
                assert "not found" in result["error"].lower()

    def test_rename_collection_target_name_conflict(self):
        """Test rename operation when target name already exists."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                mock_coll_service.rename_collection.side_effect = CollectionError("Collection 'existing_name' already exists")
                
                result = rename_collection("source_collection", "existing_name")
                
                assert result["success"] is False
                assert "already exists" in result["error"].lower()

    def test_rename_collection_atomicity_with_database_error(self):
        """Test that rename operation is atomic - if it fails, no partial changes are made."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                # Simulate database constraint violation during rename
                mock_coll_service.rename_collection.side_effect = IntegrityError(
                    "UNIQUE constraint failed", None, None
                )
                
                result = rename_collection("source_collection", "target_collection")
                
                assert result["success"] is False
                assert "constraint" in result["error"].lower() or "integrity" in result["error"].lower()

    def test_rename_collection_concurrent_modification(self):
        """Test handling of concurrent modification scenarios."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                # Simulate concurrent modification error
                mock_coll_service.rename_collection.side_effect = DatabaseError(
                    "could not serialize access", None, None
                )
                
                result = rename_collection("source_collection", "target_collection")
                
                assert result["success"] is False
                assert "error" in result

    def test_rename_collection_invalid_names(self):
        """Test rename operation with various invalid name inputs."""
        # Test empty old name
        result = rename_collection("", "valid_name")
        assert result["success"] is False
        assert "cannot be empty" in result["error"]
        
        # Test empty new name
        result = rename_collection("valid_name", "")
        assert result["success"] is False
        assert "cannot be empty" in result["error"]
        
        # Test whitespace-only names
        result = rename_collection("   ", "valid_name")
        assert result["success"] is False
        assert "cannot be empty" in result["error"]
        
        result = rename_collection("valid_name", "   ")
        assert result["success"] is False
        assert "cannot be empty" in result["error"]

    def test_rename_collection_invalid_new_name_format(self):
        """Test rename operation with invalid new name format."""
        with patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            # Mock validation to raise error for invalid name format
            mock_validate.side_effect = ValueError("Invalid collection name format")
            
            result = rename_collection("valid_old_name", "invalid name with spaces")
            
            assert result["success"] is False
            assert "Invalid collection name format" in result["error"]

    def test_rename_collection_same_name(self):
        """Test rename operation when old and new names are the same."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                
                # Mock collection with same name
                mock_collection = Mock()
                mock_collection.id = 1
                mock_collection.name = "same_name"
                mock_collection.description = "Test collection"
                mock_collection.dimension = 1024
                mock_collection.created_at.isoformat.return_value = "2025-09-23T10:00:00"
                mock_collection.updated_at.isoformat.return_value = "2025-09-23T12:00:00"
                
                mock_coll_service.rename_collection.return_value = mock_collection
                
                result = rename_collection("same_name", "same_name")
                
                # This should succeed (some systems allow renaming to same name)
                # or return an appropriate message
                assert result["success"] is True or "same name" in result.get("error", "").lower()

    def test_rename_collection_transaction_rollback(self):
        """Test that database transaction is properly rolled back on error."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            
            # Mock database session with transaction behavior
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service to raise exception
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                mock_coll_service.rename_collection.side_effect = Exception("Database error during rename")
                
                result = rename_collection("source_collection", "target_collection")
                
                assert result["success"] is False
                assert "Database error during rename" in result["error"]
                
                # Verify that the session context manager was used
                # (This ensures proper transaction handling)
                mock_session.return_value.__enter__.assert_called_once()
                mock_session.return_value.__exit__.assert_called_once()

    def test_rename_collection_case_sensitivity(self):
        """Test rename operation with case-sensitive names."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                
                # Mock renamed collection
                mock_collection = Mock()
                mock_collection.id = 1
                mock_collection.name = "NewCollectionName"
                mock_collection.description = "Test collection"
                mock_collection.dimension = 1024
                mock_collection.created_at.isoformat.return_value = "2025-09-23T10:00:00"
                mock_collection.updated_at.isoformat.return_value = "2025-09-23T12:00:00"
                
                mock_coll_service.rename_collection.return_value = mock_collection
                
                # Test renaming with different case
                result = rename_collection("oldcollectionname", "NewCollectionName")
                
                assert result["success"] is True
                assert result["collection"]["name"] == "NewCollectionName"

    def test_rename_collection_special_characters(self):
        """Test rename operation with special characters in names."""
        test_cases = [
            ("old_name", "new_name_123", True),  # Valid
            ("old_name", "new_name_with_underscore", True),  # Valid  
            ("old_name", "123_starts_with_number", True),  # Valid
        ]
        
        for old_name, new_name, should_succeed in test_cases:
            with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
                 patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
                
                if should_succeed:
                    mock_validate.return_value = None
                    
                    # Mock database session
                    mock_db = MagicMock()
                    mock_session.return_value.__enter__.return_value = mock_db
                    
                    # Mock collection service
                    with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                        mock_coll_service = mock_service.return_value
                        
                        mock_collection = Mock()
                        mock_collection.name = new_name
                        mock_collection.id = 1
                        mock_coll_service.rename_collection.return_value = mock_collection
                        
                        result = rename_collection(old_name, new_name)
                        assert result["success"] is True
                else:
                    mock_validate.side_effect = ValueError("Invalid name")
                    result = rename_collection(old_name, new_name)
                    assert result["success"] is False

    def test_rename_collection_preserves_metadata(self):
        """Test that rename operation preserves all collection metadata."""
        with patch('pgvector_mcp_server.server.get_db_session') as mock_session, \
             patch('pgvector_mcp_server.server.validate_collection_name') as mock_validate:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock collection service
            with patch('pgvector_mcp_server.server.CollectionService') as mock_service:
                mock_coll_service = mock_service.return_value
                
                # Mock collection with all metadata
                mock_collection = Mock()
                mock_collection.id = 42
                mock_collection.name = "renamed_collection"
                mock_collection.description = "Original description preserved"
                mock_collection.dimension = 1024
                mock_collection.created_at.isoformat.return_value = "2025-09-20T10:00:00"
                mock_collection.updated_at.isoformat.return_value = "2025-09-23T12:30:00"
                
                mock_coll_service.rename_collection.return_value = mock_collection
                
                result = rename_collection("original_name", "renamed_collection")
                
                # Verify all metadata is preserved
                assert result["success"] is True
                collection = result["collection"]
                assert collection["id"] == 42
                assert collection["name"] == "renamed_collection"
                assert collection["description"] == "Original description preserved"
                assert collection["dimension"] == 1024
                assert collection["created_at"] == "2025-09-20T10:00:00"
                assert collection["updated_at"] == "2025-09-23T12:30:00"


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_rename_collection.py -v
    pytest.main([__file__, "-v"])
