"""Windows encoding detection and UTF-8 conversion utilities.

This module provides automatic file encoding detection and UTF-8 conversion,
with special focus on Windows compatibility and Chinese character handling.
"""

import chardet
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

# Configure logger
logger = logging.getLogger(__name__)

# Common encodings to try, prioritizing Windows and Chinese encodings
COMMON_ENCODINGS = [
    'utf-8',
    'utf-8-sig',  # UTF-8 with BOM
    'gbk',        # Chinese (Simplified) - Windows
    'gb2312',     # Chinese (Simplified) - Legacy
    'big5',       # Chinese (Traditional)
    'cp1252',     # Windows Western European
    'cp936',      # Windows Chinese Simplified
    'cp950',      # Windows Chinese Traditional
    'ascii',
    'latin1',
    'iso-8859-1',
]

def detect_file_encoding(file_path: Union[str, Path], 
                        sample_size: int = 8192,
                        confidence_threshold: float = 0.7) -> Dict[str, Union[str, float, None]]:
    """
    Detect the encoding of a file using multiple strategies.
    
    Args:
        file_path: Path to the file to analyze
        sample_size: Number of bytes to read for detection (default: 8192)
        confidence_threshold: Minimum confidence required for detection (default: 0.7)
    
    Returns:
        Dictionary containing:
        - encoding: Detected encoding name
        - confidence: Detection confidence score (0.0-1.0)
        - method: Detection method used ('chardet', 'heuristic', 'fallback')
        - error: Error message if detection failed
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {
            'encoding': None,
            'confidence': 0.0,
            'method': 'error',
            'error': f"File not found: {file_path}"
        }
    
    try:
        # Read sample bytes for detection
        with open(file_path, 'rb') as f:
            raw_data = f.read(sample_size)
        
        if not raw_data:
            return {
                'encoding': 'utf-8',
                'confidence': 1.0,
                'method': 'empty_file',
                'error': None
            }
        
        # Method 1: Use chardet library
        chardet_result = chardet.detect(raw_data)
        if chardet_result and chardet_result['encoding'] and chardet_result['confidence'] >= confidence_threshold:
            logger.debug(f"Chardet detection: {chardet_result}")
            return {
                'encoding': chardet_result['encoding'].lower(),
                'confidence': chardet_result['confidence'],
                'method': 'chardet',
                'error': None
            }
        
        # Method 2: Try common encodings heuristically
        for encoding in COMMON_ENCODINGS:
            try:
                raw_data.decode(encoding)
                logger.debug(f"Heuristic detection successful: {encoding}")
                return {
                    'encoding': encoding,
                    'confidence': 0.8,  # Good confidence for successful decode
                    'method': 'heuristic',
                    'error': None
                }
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Method 3: Fallback with lower confidence chardet result
        if chardet_result and chardet_result['encoding']:
            logger.warning(f"Low confidence chardet detection: {chardet_result}")
            return {
                'encoding': chardet_result['encoding'].lower(),
                'confidence': chardet_result['confidence'],
                'method': 'chardet_fallback',
                'error': None
            }
        
        # Method 4: Final fallback to UTF-8
        logger.warning(f"No encoding detected for {file_path}, falling back to utf-8")
        return {
            'encoding': 'utf-8',
            'confidence': 0.1,  # Low confidence
            'method': 'fallback',
            'error': 'No encoding detected, using UTF-8 fallback'
        }
        
    except Exception as e:
        logger.error(f"Error detecting encoding for {file_path}: {e}")
        return {
            'encoding': None,
            'confidence': 0.0,
            'method': 'error',
            'error': str(e)
        }

def read_file_with_encoding_detection(file_path: Union[str, Path], 
                                    encoding: Optional[str] = None,
                                    fallback_encoding: str = 'utf-8',
                                    error_handling: str = 'replace') -> Tuple[str, Dict[str, Union[str, float, None]]]:
    """
    Read a file with automatic encoding detection and error handling.
    
    Args:
        file_path: Path to the file to read
        encoding: Force specific encoding (skip detection if provided)
        fallback_encoding: Encoding to use if detection fails
        error_handling: How to handle decode errors ('strict', 'ignore', 'replace')
    
    Returns:
        Tuple of (file_content, encoding_info)
        - file_content: Decoded text content
        - encoding_info: Detection result dictionary
    """
    file_path = Path(file_path)
    
    # Use provided encoding or detect it
    if encoding:
        encoding_info = {
            'encoding': encoding,
            'confidence': 1.0,
            'method': 'provided',
            'error': None
        }
    else:
        encoding_info = detect_file_encoding(file_path)
        encoding = encoding_info['encoding']
    
    # Try to read with detected/provided encoding
    if encoding:
        try:
            with open(file_path, 'r', encoding=encoding, errors=error_handling) as f:
                content = f.read()
            logger.info(f"Successfully read {file_path} with encoding {encoding}")
            return content, encoding_info
        except Exception as e:
            logger.warning(f"Failed to read {file_path} with encoding {encoding}: {e}")
            encoding_info['error'] = f"Failed to read with {encoding}: {e}"
    
    # Fallback to specified fallback encoding
    try:
        with open(file_path, 'r', encoding=fallback_encoding, errors=error_handling) as f:
            content = f.read()
        logger.warning(f"Read {file_path} with fallback encoding {fallback_encoding}")
        encoding_info.update({
            'encoding': fallback_encoding,
            'confidence': 0.1,
            'method': 'fallback_read',
            'error': f"Used fallback encoding {fallback_encoding}"
        })
        return content, encoding_info
    except Exception as e:
        logger.error(f"Failed to read {file_path} even with fallback encoding: {e}")
        raise IOError(f"Could not read file {file_path} with any encoding: {e}")

def convert_file_to_utf8(source_path: Union[str, Path], 
                        target_path: Optional[Union[str, Path]] = None,
                        source_encoding: Optional[str] = None,
                        backup: bool = True) -> Dict[str, Union[str, bool, None]]:
    """
    Convert a file to UTF-8 encoding.
    
    Args:
        source_path: Source file path
        target_path: Target file path (defaults to source_path)
        source_encoding: Source encoding (auto-detect if None)
        backup: Whether to create a backup of the original file
    
    Returns:
        Dictionary containing conversion result:
        - success: Whether conversion succeeded
        - source_encoding: Original file encoding
        - target_path: Path to converted file
        - backup_path: Path to backup file (if created)
        - error: Error message if conversion failed
    """
    source_path = Path(source_path)
    target_path = Path(target_path) if target_path else source_path
    
    result = {
        'success': False,
        'source_encoding': None,
        'target_path': str(target_path),
        'backup_path': None,
        'error': None
    }
    
    try:
        # Read source file with encoding detection
        content, encoding_info = read_file_with_encoding_detection(
            source_path, 
            encoding=source_encoding
        )
        result['source_encoding'] = encoding_info['encoding']
        
        # Skip conversion if already UTF-8
        if encoding_info['encoding'] in ['utf-8', 'utf-8-sig'] and target_path == source_path:
            result.update({
                'success': True,
                'error': f"File already in UTF-8 format"
            })
            return result
        
        # Create backup if requested
        if backup and target_path == source_path:
            backup_path = source_path.with_suffix(source_path.suffix + '.bak')
            source_path.rename(backup_path)
            result['backup_path'] = str(backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Write content as UTF-8
        with open(target_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        
        result.update({
            'success': True,
            'error': None
        })
        
        logger.info(f"Successfully converted {source_path} to UTF-8")
        return result
        
    except Exception as e:
        error_msg = f"Error converting {source_path} to UTF-8: {e}"
        logger.error(error_msg)
        result['error'] = error_msg
        return result

def get_system_encoding_info() -> Dict[str, str]:
    """
    Get system encoding information for debugging.
    
    Returns:
        Dictionary with system encoding details
    """
    import locale
    import os
    
    info = {
        'platform': sys.platform,
        'default_encoding': sys.getdefaultencoding(),
        'filesystem_encoding': sys.getfilesystemencoding(),
        'locale_encoding': locale.getpreferredencoding(),
        'stdin_encoding': getattr(sys.stdin, 'encoding', 'unknown'),
        'stdout_encoding': getattr(sys.stdout, 'encoding', 'unknown'),
    }
    
    # Windows-specific information
    if sys.platform.startswith('win'):
        try:
            import codecs
            info['ansi_codepage'] = locale.getpreferredencoding()
            info['oem_codepage'] = locale.getpreferredencoding(False)
        except Exception:
            pass
    
    return info

def is_windows_system() -> bool:
    """Check if running on Windows system."""
    return sys.platform.startswith('win')

def handle_windows_path_encoding(path: Union[str, Path]) -> Path:
    """
    Handle Windows path encoding issues.
    
    Args:
        path: File path that may have encoding issues
        
    Returns:
        Properly encoded Path object
    """
    if not is_windows_system():
        return Path(path)
    
    # Convert to Path and resolve to handle any encoding issues
    try:
        path_obj = Path(path).resolve()
        # Test if path exists and is accessible
        path_obj.exists()
        return path_obj
    except (OSError, UnicodeError) as e:
        logger.warning(f"Path encoding issue: {e}, attempting to fix")
        # Try to encode/decode the path string
        try:
            if isinstance(path, str):
                # Try to encode as UTF-8 and decode back
                fixed_path = path.encode('utf-8').decode('utf-8')
                return Path(fixed_path).resolve()
        except Exception:
            pass
        
        # If all else fails, return the original path
        logger.error(f"Could not fix path encoding for: {path}")
        return Path(path)

def detect_and_decode(data: Union[str, bytes], 
                      encoding: Optional[str] = None) -> str:
    """
    Detect encoding and decode bytes to string, or return string as-is.
    
    Args:
        data: Input data (string or bytes)
        encoding: Force specific encoding (skip detection if provided)
        
    Returns:
        Decoded string
    """
    if isinstance(data, str):
        return data
    
    if isinstance(data, bytes):
        if encoding:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode with provided encoding {encoding}")
        
        # Use chardet for detection
        result = chardet.detect(data)
        detected_encoding = result.get('encoding', 'utf-8') if result else 'utf-8'
        
        try:
            return data.decode(detected_encoding)
        except UnicodeDecodeError:
            # Fallback to UTF-8 with error replacement
            return data.decode('utf-8', errors='replace')
    
    # Fallback for other types
    return str(data)

# Export main functions for easy import
__all__ = [
    'detect_file_encoding',
    'read_file_with_encoding_detection', 
    'convert_file_to_utf8',
    'get_system_encoding_info',
    'is_windows_system',
    'handle_windows_path_encoding',
    'detect_and_decode'
]
