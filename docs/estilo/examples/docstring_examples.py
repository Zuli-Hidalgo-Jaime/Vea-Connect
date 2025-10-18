"""
Docstring Examples for VeaConnect Coding Standards.

This module demonstrates proper docstring formatting following the
Google style guide. All docstrings should be in English and provide
clear, concise documentation.

Example:
    >>> from docstring_examples import DocumentProcessor
    >>> processor = DocumentProcessor()
    >>> result = processor.process("document.pdf")
    >>> print(result.status)
    'success'

Classes:
    DocumentProcessor: Main document processing class.
    ProcessingResult: Result container for processing operations.
    ProcessingError: Custom exception for processing failures.

Functions:
    validate_file: Validate file format and size.
    extract_text: Extract text content from documents.
    calculate_embeddings: Generate embeddings for text content.
"""

import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Custom exception for document processing errors.
    
    This exception is raised when document processing fails due to
    format issues, size limitations, or other processing errors.
    
    Attributes:
        message: Human-readable error message.
        error_code: Machine-readable error code.
        file_path: Path to the file that caused the error.
    """
    
    def __init__(self, message: str, error_code: str, file_path: Optional[str] = None):
        """Initialize ProcessingError.
        
        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
            file_path: Path to the file that caused the error.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.file_path = file_path


class ProcessingResult:
    """Container for document processing results.
    
    This class holds the results of document processing operations,
    including extracted text, metadata, and processing status.
    
    Attributes:
        text_content: Extracted text content from the document.
        metadata: Document metadata (title, author, etc.).
        processing_time: Time taken for processing in seconds.
        status: Processing status ('success', 'error', 'partial').
        error_message: Error message if processing failed.
    """
    
    def __init__(self, text_content: str = "", metadata: Optional[Dict] = None):
        """Initialize ProcessingResult.
        
        Args:
            text_content: Extracted text content. Defaults to empty string.
            metadata: Document metadata. Defaults to None.
        """
        self.text_content = text_content
        self.metadata = metadata or {}
        self.processing_time = 0.0
        self.status = "pending"
        self.error_message = None
    
    def is_successful(self) -> bool:
        """Check if processing was successful.
        
        Returns:
            True if processing completed successfully, False otherwise.
        """
        return self.status == "success"
    
    def get_word_count(self) -> int:
        """Get the word count of extracted text.
        
        Returns:
            Number of words in the extracted text.
        """
        return len(self.text_content.split())


class DocumentProcessor:
    """Process and analyze documents for text extraction and indexing.
    
    This class provides functionality to process various document formats,
    extract text content, and prepare documents for search indexing.
    It supports PDF, DOCX, TXT, and Markdown formats.
    
    Attributes:
        supported_formats: List of supported file formats.
        max_file_size: Maximum file size in bytes for processing.
        extraction_timeout: Timeout in seconds for text extraction.
        processing_stats: Statistics about processing operations.
    
    Example:
        >>> processor = DocumentProcessor(max_file_size=10*1024*1024)
        >>> result = processor.process_document("document.pdf")
        >>> if result.is_successful():
        ...     print(f"Extracted {result.get_word_count()} words")
        ... else:
        ...     print(f"Processing failed: {result.error_message}")
    """
    
    def __init__(self, max_file_size: int = 50 * 1024 * 1024, 
                 extraction_timeout: int = 300):
        """Initialize the DocumentProcessor.
        
        Args:
            max_file_size: Maximum file size in bytes. Defaults to 50MB.
            extraction_timeout: Timeout in seconds for text extraction. 
                Defaults to 300 seconds.
        
        Raises:
            ValueError: If max_file_size or extraction_timeout is negative.
        """
        if max_file_size < 0:
            raise ValueError("max_file_size cannot be negative")
        if extraction_timeout < 0:
            raise ValueError("extraction_timeout cannot be negative")
        
        self.supported_formats = ['.pdf', '.docx', '.txt', '.md']
        self.max_file_size = max_file_size
        self.extraction_timeout = extraction_timeout
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_processing_time': 0.0
        }
    
    def process_document(self, file_path: str) -> ProcessingResult:
        """Process a single document and extract its content.
        
        This method validates the file, extracts text content, and returns
        a ProcessingResult with the extracted content and metadata.
        
        Args:
            file_path: Path to the document file.
        
        Returns:
            ProcessingResult containing extracted text and metadata.
        
        Raises:
            FileNotFoundError: If the document file doesn't exist.
            ProcessingError: If the file format is not supported or processing fails.
            ValueError: If file_path is empty or None.
        
        Example:
            >>> processor = DocumentProcessor()
            >>> result = processor.process_document("sample.pdf")
            >>> print(f"Status: {result.status}")
            >>> print(f"Words: {result.get_word_count()}")
        """
        if not file_path:
            raise ValueError("file_path cannot be empty or None")
        
        # Validate file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Validate file format
        if not self._is_supported_format(file_path):
            raise ProcessingError(
                f"Unsupported file format: {Path(file_path).suffix}",
                "UNSUPPORTED_FORMAT",
                file_path
            )
        
        # Process the document
        result = ProcessingResult()
        try:
            result.text_content = self._extract_text_content(file_path)
            result.metadata = self._extract_metadata(file_path)
            result.status = "success"
            self.processing_stats['successful'] += 1
        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            self.processing_stats['failed'] += 1
            logger.error("Document processing failed", extra={
                'file_path': file_path,
                'error': str(e)
            })
        
        self.processing_stats['total_processed'] += 1
        return result
    
    def _is_supported_format(self, file_path: str) -> bool:
        """Check if the file format is supported.
        
        Args:
            file_path: Path to the file to check.
        
        Returns:
            True if the file format is supported, False otherwise.
        """
        return Path(file_path).suffix.lower() in self.supported_formats
    
    def _extract_text_content(self, file_path: str) -> str:
        """Extract text content from the document.
        
        Args:
            file_path: Path to the document file.
        
        Returns:
            Extracted text content as a string.
        
        Raises:
            ProcessingError: If text extraction fails.
        """
        # Implementation would go here
        # This is a placeholder for demonstration
        return "Extracted text content from document"
    
    def _extract_metadata(self, file_path: str) -> Dict:
        """Extract metadata from the document.
        
        Args:
            file_path: Path to the document file.
        
        Returns:
            Dictionary containing document metadata.
        """
        # Implementation would go here
        # This is a placeholder for demonstration
        return {
            'title': 'Document Title',
            'author': 'Document Author',
            'created_date': '2024-01-01',
            'file_size': Path(file_path).stat().st_size
        }
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics.
        
        Returns:
            Dictionary containing processing statistics.
        """
        return self.processing_stats.copy()


def validate_file(file_path: str, max_size: Optional[int] = None) -> bool:
    """Validate file format and size.
    
    This function checks if a file exists, has a supported format,
    and meets size requirements.
    
    Args:
        file_path: Path to the file to validate.
        max_size: Maximum file size in bytes. If None, no size check is performed.
    
    Returns:
        True if the file is valid, False otherwise.
    
    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If file_path is empty or None.
    
    Example:
        >>> validate_file("document.pdf", max_size=10*1024*1024)
        True
        >>> validate_file("document.txt", max_size=1024)
        False  # if file is larger than 1KB
    """
    if not file_path:
        raise ValueError("file_path cannot be empty or None")
    
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check file size if max_size is specified
    if max_size is not None and file_path_obj.stat().st_size > max_size:
        logger.warning("File size exceeds maximum allowed size", extra={
            'file_path': file_path,
            'file_size': file_path_obj.stat().st_size,
            'max_size': max_size
        })
        return False
    
    return True


def extract_text(file_path: str, encoding: str = "utf-8") -> str:
    """Extract text content from a text file.
    
    This function reads and returns the text content from a text file.
    It handles different encodings and provides error handling.
    
    Args:
        file_path: Path to the text file.
        encoding: File encoding. Defaults to "utf-8".
    
    Returns:
        Text content from the file.
    
    Raises:
        FileNotFoundError: If the file doesn't exist.
        UnicodeDecodeError: If the file cannot be decoded with the specified encoding.
        ValueError: If file_path is empty or None.
    
    Example:
        >>> content = extract_text("sample.txt")
        >>> print(f"File contains {len(content)} characters")
        >>> content = extract_text("sample.txt", encoding="latin-1")
    """
    if not file_path:
        raise ValueError("file_path cannot be empty or None")
    
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
        
        logger.info("Text extraction successful", extra={
            'file_path': file_path,
            'encoding': encoding,
            'content_length': len(content)
        })
        
        return content
    except FileNotFoundError:
        logger.error("File not found during text extraction", extra={
            'file_path': file_path
        })
        raise
    except UnicodeDecodeError as e:
        logger.error("Encoding error during text extraction", extra={
            'file_path': file_path,
            'encoding': encoding,
            'error': str(e)
        })
        raise


def calculate_embeddings(text: str, model_name: str = "text-embedding-ada-002") -> List[float]:
    """Calculate text embeddings using OpenAI's embedding model.
    
    This function generates vector embeddings for text content using
    OpenAI's embedding API. The embeddings can be used for semantic
    search and similarity calculations.
    
    Args:
        text: The input text to embed.
        model_name: The embedding model to use. Defaults to "text-embedding-ada-002".
    
    Returns:
        The embedding vector as a list of floats.
    
    Raises:
        ValueError: If text is empty or None.
        ProcessingError: If the API call fails or returns an error.
    
    Example:
        >>> text = "Hello, world!"
        >>> embedding = calculate_embeddings(text)
        >>> print(f"Embedding dimensions: {len(embedding)}")
        >>> print(f"First few values: {embedding[:5]}")
        
        >>> # Use a different model
        >>> embedding = calculate_embeddings(text, "text-embedding-3-small")
    """
    if not text or not text.strip():
        raise ValueError("text cannot be empty or None")
    
    # Implementation would go here
    # This is a placeholder for demonstration
    logger.info("Calculating embeddings", extra={
        'text_length': len(text),
        'model_name': model_name
    })
    
    # Return a mock embedding vector
    return [0.1] * 1536  # 1536 dimensions for text-embedding-ada-002


def process_batch(file_paths: List[str], processor: DocumentProcessor) -> List[ProcessingResult]:
    """Process multiple documents in batch.
    
    This function processes a list of documents using the provided
    DocumentProcessor and returns results for all documents.
    
    Args:
        file_paths: List of file paths to process.
        processor: DocumentProcessor instance to use for processing.
    
    Returns:
        List of ProcessingResult objects, one for each input file.
    
    Raises:
        ValueError: If file_paths is empty or None, or if processor is None.
    
    Example:
        >>> processor = DocumentProcessor()
        >>> files = ["doc1.pdf", "doc2.txt", "doc3.docx"]
        >>> results = process_batch(files, processor)
        >>> successful = [r for r in results if r.is_successful()]
        >>> print(f"Successfully processed {len(successful)} files")
    """
    if not file_paths:
        raise ValueError("file_paths cannot be empty or None")
    
    if processor is None:
        raise ValueError("processor cannot be None")
    
    results = []
    for file_path in file_paths:
        try:
            result = processor.process_document(file_path)
            results.append(result)
        except Exception as e:
            logger.error("Batch processing failed for file", extra={
                'file_path': file_path,
                'error': str(e)
            })
            # Create a failed result
            failed_result = ProcessingResult()
            failed_result.status = "error"
            failed_result.error_message = str(e)
            results.append(failed_result)
    
    return results
