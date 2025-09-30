"""Test fixed-size chunking implementation."""

import pytest
from pgvector_mcp_server.services.chunking_service import ChunkingService, TextChunk
from pgvector_mcp_server.services.parsers import PDFParser, TextParser, ParsedDocument
from pathlib import Path
import tempfile


# Mark all tests to skip env_setup fixture
pytestmark = pytest.mark.usefixtures()


class TestFixedChunking:
    """Test suite for fixed-size chunking strategy."""

    def test_simple_fixed_chunking(self):
        """Test basic fixed-size chunking without boundary detection."""
        service = ChunkingService(chunk_size=10, overlap=3)

        text = "0123456789ABCDEFGHIJ"  # 20 characters
        chunks = service.chunk_text(text)

        # Expected chunks with overlap
        # Chunk 0: [0:10] = "0123456789"
        # Chunk 1: [7:17] = "789ABCDEFG" (start = 10-3 = 7)
        # Chunk 2: [14:20] = "DEFGHIJ" (start = 17-3 = 14)

        assert len(chunks) == 3
        assert chunks[0].content == "0123456789"
        assert chunks[1].content == "789ABCDEFG"
        assert chunks[2].content == "EFGHIJ"

        # Verify overlap
        assert chunks[0].content[-3:] == chunks[1].content[:3]  # "789"
        assert chunks[1].content[-3:] == chunks[2].content[:3]  # "EFG"

    def test_chunking_with_exact_size(self):
        """Test chunking when text length equals chunk size."""
        service = ChunkingService(chunk_size=10, overlap=3)

        text = "0123456789"  # Exactly 10 characters
        chunks = service.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].start_index == 0
        assert chunks[0].end_index == 10

    def test_chunking_shorter_than_size(self):
        """Test chunking when text is shorter than chunk size."""
        service = ChunkingService(chunk_size=100, overlap=30)

        text = "Short text"
        chunks = service.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_chunking_with_overlap(self):
        """Test that overlap is correctly implemented."""
        service = ChunkingService(chunk_size=20, overlap=5)

        text = "A" * 50  # 50 'A' characters
        chunks = service.chunk_text(text)

        # Verify overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            current_end = chunks[i].content[-5:]
            next_start = chunks[i + 1].content[:5]
            assert current_end == next_start

    def test_chunking_metadata(self):
        """Test that metadata is correctly attached to chunks."""
        service = ChunkingService(chunk_size=10, overlap=3)

        text = "0123456789ABCDEFGHIJ"
        base_metadata = {'file': 'test.txt', 'type': 'test'}
        chunks = service.chunk_text(text, base_metadata)

        # Check metadata preservation
        for i, chunk in enumerate(chunks):
            assert chunk.metadata['file'] == 'test.txt'
            assert chunk.metadata['type'] == 'test'
            assert chunk.metadata['chunk_index'] == i
            assert 'chunk_start' in chunk.metadata
            assert 'chunk_end' in chunk.metadata
            assert 'chunk_size' in chunk.metadata

    def test_empty_text(self):
        """Test handling of empty text."""
        service = ChunkingService(chunk_size=10, overlap=3)

        chunks = service.chunk_text("")
        assert len(chunks) == 0

        chunks = service.chunk_text(None)
        assert len(chunks) == 0

    def test_chinese_text_chunking(self):
        """Test fixed chunking with Chinese characters."""
        service = ChunkingService(chunk_size=20, overlap=5)

        text = "这是一个测试文本，用于验证中文字符的固定分块功能。我们希望确保分块逻辑对中文字符同样有效。"
        chunks = service.chunk_text(text)

        assert len(chunks) > 0

        # Verify each chunk is approximately the target size
        for chunk in chunks[:-1]:  # Exclude last chunk
            assert 15 <= len(chunk.content) <= 20

        # Verify overlap exists
        for i in range(len(chunks) - 1):
            current = chunks[i].content
            next_chunk = chunks[i + 1].content
            # Check that some overlap exists
            overlap_found = False
            for j in range(1, min(6, len(current), len(next_chunk))):
                if current[-j:] == next_chunk[:j]:
                    overlap_found = True
                    break
            assert overlap_found

    def test_parser_returns_single_document(self):
        """Test that parsers now return single complete document."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Line 1\n\nLine 2\n\nLine 3")
            temp_path = Path(f.name)

        try:
            parser = TextParser()
            documents = parser.parse(temp_path)

            # Should return single document (no pre-splitting)
            assert len(documents) == 1
            assert "Line 1" in documents[0].content
            assert "Line 2" in documents[0].content
            assert "Line 3" in documents[0].content
        finally:
            temp_path.unlink()

    def test_default_chunking_parameters(self):
        """Test that default parameters match specifications."""
        service = ChunkingService()

        assert service.chunk_size == 500
        assert service.overlap == 150

        # Verify 30% overlap ratio
        assert service.overlap / service.chunk_size == 0.3

    def test_performance_large_text(self):
        """Test performance with large text (simplified chunking should be faster)."""
        import time

        service = ChunkingService(chunk_size=500, overlap=150)

        # Generate large text (1MB)
        text = "A" * (1024 * 1024)

        start_time = time.time()
        chunks = service.chunk_text(text)
        elapsed = time.time() - start_time

        # Should complete quickly (< 100ms for 1MB)
        assert elapsed < 0.1, f"Chunking took {elapsed:.3f}s, expected < 0.1s"

        # Verify chunking correctness
        assert len(chunks) > 0
        expected_chunks = (len(text) - service.overlap) // (service.chunk_size - service.overlap) + 1
        # Allow some variance due to edge cases
        assert abs(len(chunks) - expected_chunks) <= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])