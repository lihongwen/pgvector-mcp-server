"""Text chunking service for pgvector MCP server - Simplified fixed-size chunking."""

from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    metadata: Dict[str, Any]
    start_index: int = 0
    end_index: int = 0


class ChunkingService:
    """Service for chunking text documents with fixed-size strategy."""

    def __init__(self, chunk_size: int = 500, overlap: int = 150):
        """
        Initialize chunking service with fixed parameters.

        Args:
            chunk_size: Fixed size for each chunk (default: 500 characters)
            overlap: Overlap size between chunks (default: 150 characters, 30%)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_documents(self, documents: List) -> List[TextChunk]:
        """Chunk a list of parsed documents using fixed-size strategy."""
        chunks = []

        for doc in documents:
            doc_chunks = self.chunk_text(doc.content, doc.metadata)
            chunks.extend(doc_chunks)

        return chunks

    def chunk_text(self, text: str, base_metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """
        Chunk text into fixed-size overlapping pieces.

        This simplified approach uses pure fixed-size chunking without boundary detection,
        relying on overlap to preserve semantic continuity and vector model tolerance.

        Args:
            text: Input text to chunk
            base_metadata: Base metadata to attach to all chunks

        Returns:
            List of TextChunk objects with fixed sizes
        """
        if not text:
            return []

        # Handle short text
        if len(text) <= self.chunk_size:
            return [TextChunk(
                content=text,
                metadata=base_metadata or {},
                start_index=0,
                end_index=len(text)
            )]

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Fixed-size chunking: simple slice
            end = min(start + self.chunk_size, len(text))

            # Extract chunk (no boundary detection)
            chunk_text = text[start:end]

            # Build metadata
            metadata = (base_metadata or {}).copy()
            metadata.update({
                'chunk_index': chunk_index,
                'chunk_start': start,
                'chunk_end': end,
                'chunk_size': len(chunk_text),
                'total_length': len(text)
            })

            chunks.append(TextChunk(
                content=chunk_text,
                metadata=metadata,
                start_index=start,
                end_index=end
            ))

            chunk_index += 1

            # Move to next position with fixed overlap
            start = end - self.overlap

            # Prevent infinite loop for edge cases
            if start >= len(text) - self.overlap:
                break

        return chunks
