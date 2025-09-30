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
        """Parse text/markdown file and return complete text without pre-splitting."""
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

            # Return single complete document (no pre-splitting)
            return [ParsedDocument(content=text, metadata=base_metadata)]

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
