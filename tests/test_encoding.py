"""Test suite for encoding detection and Windows compatibility.

This module tests the encoding detection utilities to ensure proper handling
of various file encodings, especially for Windows systems and Chinese characters.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

# Import encoding utilities
from pgvector_mcp_server.utils.encoding import (
    detect_file_encoding,
    read_file_with_encoding_detection,
    convert_file_to_utf8,
    get_system_encoding_info,
    is_windows_system,
    handle_windows_path_encoding
)


class TestEncodingDetection:
    """Test encoding detection functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_file(self, content: str, encoding: str, filename: str = "test.txt") -> Path:
        """Create a test file with specific content and encoding."""
        file_path = self.temp_dir_path / filename
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return file_path

    def create_binary_test_file(self, content_bytes: bytes, filename: str = "test.txt") -> Path:
        """Create a test file with specific binary content."""
        file_path = self.temp_dir_path / filename
        with open(file_path, 'wb') as f:
            f.write(content_bytes)
        return file_path

    def test_detect_utf8_encoding(self):
        """Test detection of UTF-8 encoded files."""
        content = "Hello, world! 你好世界! 🌟"
        file_path = self.create_test_file(content, 'utf-8')
        
        result = detect_file_encoding(file_path)
        
        assert result['encoding'] == 'utf-8'
        assert result['confidence'] > 0.7
        assert result['method'] in ['chardet', 'heuristic']
        assert result['error'] is None

    def test_detect_utf8_bom_encoding(self):
        """Test detection of UTF-8 with BOM."""
        content = "Hello, world! 你好世界!"
        file_path = self.create_test_file(content, 'utf-8-sig')
        
        result = detect_file_encoding(file_path)
        
        assert result['encoding'].startswith('utf-8')
        assert result['confidence'] > 0.7
        assert result['error'] is None

    def test_detect_gbk_encoding(self):
        """Test detection of GBK (Chinese) encoding."""
        content = "你好世界！这是中文测试。"
        # Create GBK encoded file
        file_path = self.temp_dir_path / "gbk_test.txt"
        with open(file_path, 'w', encoding='gbk') as f:
            f.write(content)
        
        result = detect_file_encoding(file_path)
        
        # Should detect GBK or a related Chinese encoding
        assert result['encoding'] in ['gbk', 'gb2312', 'cp936']
        assert result['error'] is None

    def test_detect_ascii_encoding(self):
        """Test detection of ASCII encoding."""
        content = "Hello, this is ASCII text only."
        file_path = self.create_test_file(content, 'ascii')
        
        result = detect_file_encoding(file_path)
        
        # ASCII should be detected as ASCII or UTF-8 (compatible)
        assert result['encoding'] in ['ascii', 'utf-8']
        assert result['error'] is None

    def test_detect_empty_file(self):
        """Test detection behavior with empty files."""
        file_path = self.temp_dir_path / "empty.txt"
        file_path.touch()
        
        result = detect_file_encoding(file_path)
        
        assert result['encoding'] == 'utf-8'
        assert result['method'] == 'empty_file'
        assert result['confidence'] == 1.0
        assert result['error'] is None

    def test_detect_nonexistent_file(self):
        """Test detection behavior with non-existent files."""
        file_path = self.temp_dir_path / "nonexistent.txt"
        
        result = detect_file_encoding(file_path)
        
        assert result['encoding'] is None
        assert result['confidence'] == 0.0
        assert result['method'] == 'error'
        assert "not found" in result['error'].lower()

    def test_detect_binary_file(self):
        """Test detection behavior with binary files."""
        # Create a binary file
        binary_content = b'\x00\x01\x02\x03\xff\xfe\xfd'
        file_path = self.create_binary_test_file(binary_content, "binary.bin")
        
        result = detect_file_encoding(file_path)
        
        # Should fall back to UTF-8 or return low confidence
        assert result['encoding'] is not None
        # Binary files might have very low confidence
        assert result['confidence'] >= 0.0

    def test_read_file_with_encoding_detection_utf8(self):
        """Test reading UTF-8 files with automatic detection."""
        content = "Hello, world! 你好世界! 🌟"
        file_path = self.create_test_file(content, 'utf-8')
        
        read_content, encoding_info = read_file_with_encoding_detection(file_path)
        
        assert read_content == content
        assert encoding_info['encoding'] == 'utf-8'
        assert encoding_info['error'] is None

    def test_read_file_with_encoding_detection_gbk(self):
        """Test reading GBK files with automatic detection."""
        content = "你好世界！这是GBK编码测试。"
        file_path = self.temp_dir_path / "gbk_test.txt"
        with open(file_path, 'w', encoding='gbk') as f:
            f.write(content)
        
        read_content, encoding_info = read_file_with_encoding_detection(file_path)
        
        assert read_content == content
        assert encoding_info['encoding'] in ['gbk', 'gb2312', 'cp936']

    def test_read_file_with_forced_encoding(self):
        """Test reading files with forced encoding parameter."""
        content = "Hello, world!"
        file_path = self.create_test_file(content, 'utf-8')
        
        read_content, encoding_info = read_file_with_encoding_detection(
            file_path, encoding='ascii'
        )
        
        assert read_content == content
        assert encoding_info['encoding'] == 'ascii'
        assert encoding_info['method'] == 'provided'

    def test_read_file_with_fallback_encoding(self):
        """Test reading files with fallback encoding when detection fails."""
        # Create a file that might be difficult to detect
        binary_content = b'\xff\xfe\x48\x00\x65\x00\x6c\x00\x6c\x00\x6f\x00'  # UTF-16 LE
        file_path = self.create_binary_test_file(binary_content, "utf16.txt")
        
        with patch('pgvector_mcp_server.utils.encoding.detect_file_encoding') as mock_detect:
            # Mock detection failure
            mock_detect.return_value = {
                'encoding': None,
                'confidence': 0.0,
                'method': 'error',
                'error': 'Detection failed'
            }
            
            read_content, encoding_info = read_file_with_encoding_detection(
                file_path, fallback_encoding='utf-8', error_handling='ignore'
            )
            
            # Should succeed with fallback encoding
            assert isinstance(read_content, str)
            assert encoding_info['method'] == 'fallback_read'

    def test_convert_file_to_utf8_from_gbk(self):
        """Test converting GBK file to UTF-8."""
        content = "你好世界！这是GBK转UTF-8测试。"
        
        # Create GBK file
        gbk_file = self.temp_dir_path / "gbk_source.txt"
        with open(gbk_file, 'w', encoding='gbk') as f:
            f.write(content)
        
        utf8_file = self.temp_dir_path / "utf8_target.txt"
        
        result = convert_file_to_utf8(gbk_file, utf8_file, backup=False)
        
        assert result['success'] is True
        assert result['source_encoding'] in ['gbk', 'gb2312', 'cp936']
        assert result['error'] is None
        
        # Verify the converted file
        with open(utf8_file, 'r', encoding='utf-8') as f:
            converted_content = f.read()
        assert converted_content == content

    def test_convert_file_to_utf8_already_utf8(self):
        """Test converting UTF-8 file (should skip)."""
        content = "Hello, already UTF-8! 你好世界!"
        file_path = self.create_test_file(content, 'utf-8')
        
        result = convert_file_to_utf8(file_path, backup=False)
        
        assert result['success'] is True
        assert "already in UTF-8" in result['error']

    def test_convert_file_to_utf8_with_backup(self):
        """Test converting file with backup creation."""
        content = "Test content for backup"
        source_file = self.create_test_file(content, 'ascii', "source.txt")
        
        result = convert_file_to_utf8(source_file, backup=True)
        
        assert result['success'] is True
        assert result['backup_path'] is not None
        
        # Verify backup file exists
        backup_path = Path(result['backup_path'])
        assert backup_path.exists()

    def test_get_system_encoding_info(self):
        """Test getting system encoding information."""
        info = get_system_encoding_info()
        
        assert 'platform' in info
        assert 'default_encoding' in info
        assert 'filesystem_encoding' in info
        assert 'locale_encoding' in info
        assert isinstance(info['platform'], str)

    def test_is_windows_system(self):
        """Test Windows system detection."""
        result = is_windows_system()
        assert isinstance(result, bool)
        
        # Test with mocked platform
        with patch('pgvector_mcp_server.utils.encoding.sys.platform', 'win32'):
            assert is_windows_system() is True
        
        with patch('pgvector_mcp_server.utils.encoding.sys.platform', 'linux'):
            assert is_windows_system() is False

    def test_handle_windows_path_encoding_windows(self):
        """Test Windows path encoding handling on Windows."""
        test_path = "C:\\测试\\文件.txt"
        
        with patch('pgvector_mcp_server.utils.encoding.is_windows_system', return_value=True):
            result = handle_windows_path_encoding(test_path)
            assert isinstance(result, Path)

    def test_handle_windows_path_encoding_non_windows(self):
        """Test Windows path encoding handling on non-Windows systems."""
        test_path = "/test/file.txt"
        
        with patch('pgvector_mcp_server.utils.encoding.is_windows_system', return_value=False):
            result = handle_windows_path_encoding(test_path)
            assert isinstance(result, Path)
            assert str(result) == "/test/file.txt"

    def test_encoding_detection_with_mixed_content(self):
        """Test encoding detection with mixed language content."""
        mixed_content = "Hello 你好 Bonjour こんにちは مرحبا"
        
        file_path = self.create_test_file(mixed_content, 'utf-8')
        result = detect_file_encoding(file_path)
        
        assert result['encoding'] == 'utf-8'
        assert result['confidence'] > 0.7
        assert result['error'] is None

    def test_encoding_detection_confidence_threshold(self):
        """Test encoding detection with different confidence thresholds."""
        content = "Simple ASCII text"
        file_path = self.create_test_file(content, 'ascii')
        
        # Test with high confidence threshold
        result_high = detect_file_encoding(file_path, confidence_threshold=0.9)
        
        # Test with low confidence threshold
        result_low = detect_file_encoding(file_path, confidence_threshold=0.1)
        
        # Both should succeed, but methods might differ
        assert result_high['encoding'] is not None
        assert result_low['encoding'] is not None

    def test_error_handling_in_read_operation(self):
        """Test error handling in file read operations."""
        file_path = self.temp_dir_path / "nonexistent.txt"
        
        with pytest.raises(IOError):
            read_file_with_encoding_detection(file_path)

    def test_windows_specific_encodings(self):
        """Test detection of Windows-specific encodings."""
        # Test CP1252 (Windows Latin-1)
        content = "Café résumé naïve"  # Contains accented characters
        
        try:
            file_path = self.temp_dir_path / "cp1252_test.txt"
            with open(file_path, 'w', encoding='cp1252') as f:
                f.write(content)
            
            result = detect_file_encoding(file_path)
            
            # Should detect a compatible encoding
            assert result['encoding'] is not None
            assert result['error'] is None
            
        except (UnicodeError, LookupError):
            # Skip if CP1252 is not available on this system
            pytest.skip("CP1252 encoding not available on this system")

    def test_large_file_sample_size(self):
        """Test encoding detection with different sample sizes."""
        content = "A" * 10000 + "你好世界" + "B" * 10000  # Large file with Chinese in middle
        file_path = self.create_test_file(content, 'utf-8')
        
        # Test with small sample size
        result_small = detect_file_encoding(file_path, sample_size=1000)
        
        # Test with large sample size
        result_large = detect_file_encoding(file_path, sample_size=50000)
        
        # Both should detect UTF-8 or ASCII (which is compatible), but confidence might differ
        assert result_small['encoding'] in ['utf-8', 'ascii']
        assert result_large['encoding'] in ['utf-8', 'ascii']


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_encoding.py -v
    pytest.main([__file__, "-v"])
