"""Text and Markdown parser for plain text files."""

import re
from pathlib import Path
from typing import Any, Dict, List

from .base_parser import BaseParser, ParsedDocument
from ...utils.encoding import read_file_with_encoding_detection, handle_windows_path_encoding


class TextParser(BaseParser):
    """Parser for text and markdown files."""

    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.markdown', '.rst'}

    def can_parse(self, file_path: Path) -> bool:
        """Check if file is text or markdown format."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def parse(self, file_path: Path) -> List[ParsedDocument]:
        """Parse text/markdown file."""
        try:
            # Handle Windows path encoding issues
            file_path = handle_windows_path_encoding(file_path)
            
            # Detect and read file with proper encoding using enhanced encoding detection
            text, encoding_info = read_file_with_encoding_detection(file_path)

            if not text or not text.strip():
                return []

            # Get base metadata
            base_metadata = self.get_file_metadata(file_path)
            base_metadata.update({
                'parser_type': 'text',
                'file_type': self._detect_file_type(file_path, text),
                'encoding_info': {
                    'detected_encoding': encoding_info.get('encoding'),
                    'encoding_confidence': encoding_info.get('confidence'),
                    'encoding_method': encoding_info.get('method'),
                    'encoding_error': encoding_info.get('error')
                }
            })

            # Parse based on file type
            if file_path.suffix.lower() in {'.md', '.markdown'}:
                return self._parse_markdown(text, base_metadata)
            else:
                return self._parse_plain_text(text, base_metadata)

        except Exception as e:
            # Handle Windows path encoding issues
            try:
                file_path = handle_windows_path_encoding(file_path)
            except Exception:
                pass
            
            base_metadata = self.get_file_metadata(file_path)
            base_metadata['error'] = str(e)

            return [ParsedDocument(
                content=f"Error parsing text file {file_path.name}: {str(e)}",
                metadata=base_metadata
            )]

    def _detect_file_type(self, file_path: Path, text: str) -> str:
        """Detect the specific type of text file."""
        extension = file_path.suffix.lower()

        if extension in {'.md', '.markdown'}:
            return 'markdown'
        elif extension == '.rst':
            return 'restructuredtext'
        else:
            # Analyze content for type hints
            if re.search(r'^#{1,6}\s', text, re.MULTILINE):
                return 'markdown_like'
            elif '.. ' in text or '====' in text:
                return 'restructuredtext_like'
            else:
                return 'plain_text'

    def _parse_markdown(self, text: str, base_metadata: Dict[str, Any]) -> List[ParsedDocument]:
        """Parse markdown content into sections."""
        documents = []

        # Split by headers
        sections = re.split(r'\n(?=#{1,6}\s)', text)

        if len(sections) <= 1:
            # No clear sections, split by paragraphs to avoid huge documents
            paragraphs = self._split_by_paragraphs(text)
            documents = []

            for idx, paragraph in enumerate(paragraphs):
                if not paragraph.strip():
                    continue

                metadata = base_metadata.copy()
                metadata.update({
                    'chunk_type': 'markdown_paragraph',
                    'chunk_id': f"para_{idx}",
                    'section_number': idx + 1
                })

                documents.append(ParsedDocument(content=paragraph.strip(), metadata=metadata))

            return documents if documents else [ParsedDocument(
                content=text.strip(),
                metadata={**base_metadata, 'chunk_type': 'markdown_paragraph', 'chunk_id': 'single'}
            )]

        # Process each section
        for idx, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            # Extract section information
            lines = section.split('\n')
            title = ""
            header_level = 0

            if lines and lines[0].startswith('#'):
                header_match = re.match(r'^(#{1,6})\s*(.*)$', lines[0])
                if header_match:
                    header_level = len(header_match.group(1))
                    title = header_match.group(2).strip()

            metadata = base_metadata.copy()
            metadata.update({
                'chunk_type': 'markdown_section',
                'chunk_id': f"section_{idx}",
                'section_number': idx + 1,
                'section_title': title,
                'header_level': header_level,
                'has_title': bool(title)
            })

            documents.append(ParsedDocument(content=section, metadata=metadata))

        return documents

    def _parse_plain_text(self, text: str, base_metadata: Dict[str, Any]) -> List[ParsedDocument]:
        """Parse plain text content."""
        # For plain text, we can split by double line breaks (paragraphs)
        # or return as single document if it's not too long

        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Remove length-based special handling, split uniformly by paragraphs to avoid overly long documents
        # Even if there's only 1 paragraph, if it's very long, let ChunkingService handle it further

        # Multiple paragraphs - create separate documents
        documents = []
        for idx, paragraph in enumerate(paragraphs):
            if not paragraph:
                continue

            metadata = base_metadata.copy()
            metadata.update({
                'chunk_type': 'text_paragraph',
                'chunk_id': f"paragraph_{idx}",
                'paragraph_number': idx + 1,
                'total_paragraphs': len(paragraphs)
            })

            documents.append(ParsedDocument(content=paragraph, metadata=metadata))

        return documents

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs to avoid huge document blocks."""
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)

        # Filter out empty paragraphs and clean
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # If still too few paragraphs, split by single newlines
        if len(paragraphs) <= 2 and len(text) > 1000:
            paragraphs = text.split('\n')
            paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs
