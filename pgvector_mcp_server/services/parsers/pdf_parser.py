"""PDF parser using pymupdf4llm for optimal text extraction."""

import re
from pathlib import Path
from typing import Any, Dict, List

from .base_parser import BaseParser, ParsedDocument


class PDFParser(BaseParser):
    """Parser for PDF files using pymupdf4llm."""

    def can_parse(self, file_path: Path) -> bool:
        """Check if file is PDF format."""
        return file_path.suffix.lower() == '.pdf'

    def parse(self, file_path: Path) -> List[ParsedDocument]:
        """Parse PDF file and extract complete text content without pre-splitting."""
        try:
            import pymupdf4llm

            # Extract text with markdown formatting
            markdown_text = pymupdf4llm.to_markdown(str(file_path))

            if not markdown_text or not markdown_text.strip():
                return []

            # Get base metadata
            base_metadata = self.get_file_metadata(file_path)
            base_metadata.update({
                'parser_type': 'pdf',
                'extraction_method': 'pymupdf4llm'
            })

            # Return single complete document (no pre-splitting)
            return [ParsedDocument(content=markdown_text, metadata=base_metadata)]

        except ImportError:
            # Fallback error if pymupdf4llm is not available
            base_metadata = self.get_file_metadata(file_path)
            base_metadata['error'] = 'pymupdf4llm not available'

            return [ParsedDocument(
                content=f"Error: pymupdf4llm not available for parsing {file_path.name}",
                metadata=base_metadata
            )]
        except Exception as e:
            base_metadata = self.get_file_metadata(file_path)
            base_metadata['error'] = str(e)

            return [ParsedDocument(
                content=f"Error parsing PDF {file_path.name}: {str(e)}",
                metadata=base_metadata
            )]
