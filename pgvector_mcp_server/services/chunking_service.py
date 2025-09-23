"""Text chunking service for pgvector MCP server."""

import re
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
    """Service for chunking text documents into manageable pieces."""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_documents(self, documents: List) -> List[TextChunk]:
        """Chunk a list of parsed documents."""
        chunks = []
        
        for doc in documents:
            doc_chunks = self.chunk_text(doc.content, doc.metadata)
            chunks.extend(doc_chunks)
        
        return chunks
    
    def chunk_text(self, text: str, base_metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """Chunk text into overlapping pieces."""
        if not text or len(text) <= self.chunk_size:
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
            # Calculate end position
            end = min(start + self.chunk_size, len(text))
            
            # Try to break at sentence boundaries if possible
            if end < len(text):
                end = self._find_sentence_boundary(text, start, end)
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if chunk_text:  # Only add non-empty chunks
                metadata = (base_metadata or {}).copy()
                metadata.update({
                    'chunk_index': chunk_index,
                    'chunk_start': start,
                    'chunk_end': end,
                    'total_length': len(text)
                })
                
                chunks.append(TextChunk(
                    content=chunk_text,
                    metadata=metadata,
                    start_index=start,
                    end_index=end
                ))
                
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + self.chunk_size - self.overlap, end)
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """Find a good sentence boundary near the end position."""
        # Look for sentence endings in the last portion of the chunk
        search_start = max(start + self.chunk_size // 2, end - 100)
        
        # Look for common sentence endings
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        
        best_pos = end
        for ending in sentence_endings:
            pos = text.find(ending, search_start, end)
            if pos != -1:
                # Found a sentence ending, use position after the ending
                return pos + len(ending)
        
        # If no sentence ending found, try to break at word boundaries
        return self._find_word_boundary(text, start, end)
    
    def _find_word_boundary(self, text: str, start: int, end: int) -> int:
        """Find a word boundary near the end position."""
        # Look backwards from end to find a space
        for i in range(end - 1, max(start, end - 50), -1):
            if text[i].isspace():
                return i + 1
        
        # If no word boundary found, use original end
        return end
