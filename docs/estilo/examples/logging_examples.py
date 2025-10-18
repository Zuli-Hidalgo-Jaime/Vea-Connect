"""
Logging Examples for VeaConnect Coding Standards.

This module demonstrates proper logging practices following the
established standards. All log messages should be professional,
clear, and informative without using emojis.

Example:
    >>> from logging_examples import DocumentService
    >>> service = DocumentService()
    >>> service.process_document("sample.pdf")
    'Document processed successfully'
"""

import logging
import time
from typing import Dict, Optional
from pathlib import Path

# Configure logger for this module
logger = logging.getLogger(__name__)


class DocumentService:
    """Service for processing documents with proper logging.
    
    This class demonstrates how to implement proper logging practices
    throughout a service, including different log levels, structured
    logging, and error handling.
    
    Attributes:
        processing_timeout: Timeout for processing operations in seconds.
        max_retries: Maximum number of retry attempts for failed operations.
    """
    
    def __init__(self, processing_timeout: int = 300, max_retries: int = 3):
        """Initialize DocumentService.
        
        Args:
            processing_timeout: Timeout for processing operations. Defaults to 300.
            max_retries: Maximum retry attempts. Defaults to 3.
        """
        self.processing_timeout = processing_timeout
        self.max_retries = max_retries
        
        logger.info("DocumentService initialized", extra={
            'processing_timeout': processing_timeout,
            'max_retries': max_retries
        })
    
    def process_document(self, file_path: str) -> str:
        """Process a document with comprehensive logging.
        
        This method demonstrates proper logging at different stages
        of document processing, including debug, info, warning, and error levels.
        
        Args:
            file_path: Path to the document to process.
        
        Returns:
            Processing result message.
        
        Raises:
            FileNotFoundError: If the document file doesn't exist.
            ProcessingError: If document processing fails.
        """
        logger.debug("Starting document processing", extra={
            'file_path': file_path,
            'timeout': self.processing_timeout
        })
        
        # Validate file exists
        if not Path(file_path).exists():
            logger.error("Document file not found", extra={
                'file_path': file_path,
                'error_type': 'FileNotFoundError'
            })
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size
        file_size = Path(file_path).stat().st_size
        logger.info("Document validation successful", extra={
            'file_path': file_path,
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2)
        })
        
        # Process with retries
        for attempt in range(self.max_retries):
            try:
                logger.debug("Processing attempt", extra={
                    'attempt': attempt + 1,
                    'max_attempts': self.max_retries
                })
                
                result = self._perform_processing(file_path)
                
                logger.info("Document processing completed successfully", extra={
                    'file_path': file_path,
                    'attempt': attempt + 1,
                    'result': result
                })
                
                return result
                
            except Exception as e:
                logger.warning("Processing attempt failed", extra={
                    'file_path': file_path,
                    'attempt': attempt + 1,
                    'max_attempts': self.max_retries,
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                
                if attempt == self.max_retries - 1:
                    logger.error("All processing attempts failed", extra={
                        'file_path': file_path,
                        'total_attempts': self.max_retries,
                        'final_error': str(e)
                    })
                    raise ProcessingError(f"Processing failed after {self.max_retries} attempts: {e}")
        
        return "Processing completed"
    
    def _perform_processing(self, file_path: str) -> str:
        """Perform the actual document processing.
        
        Args:
            file_path: Path to the document file.
        
        Returns:
            Processing result.
        
        Raises:
            ProcessingError: If processing fails.
        """
        # Simulate processing time
        time.sleep(0.1)
        
        # Simulate occasional failures
        if "error" in file_path.lower():
            raise ProcessingError("Simulated processing error")
        
        return "Document processed successfully"
    
    def batch_process(self, file_paths: list) -> Dict[str, str]:
        """Process multiple documents in batch.
        
        Args:
            file_paths: List of file paths to process.
        
        Returns:
            Dictionary mapping file paths to processing results.
        """
        logger.info("Starting batch processing", extra={
            'total_files': len(file_paths),
            'file_paths': file_paths
        })
        
        results = {}
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            try:
                result = self.process_document(file_path)
                results[file_path] = result
                successful += 1
                
                logger.debug("Batch processing successful for file", extra={
                    'file_path': file_path,
                    'successful_count': successful,
                    'failed_count': failed
                })
                
            except Exception as e:
                results[file_path] = f"Failed: {str(e)}"
                failed += 1
                
                logger.warning("Batch processing failed for file", extra={
                    'file_path': file_path,
                    'error': str(e),
                    'successful_count': successful,
                    'failed_count': failed
                })
        
        logger.info("Batch processing completed", extra={
            'total_files': len(file_paths),
            'successful': successful,
            'failed': failed,
            'success_rate': round(successful / len(file_paths) * 100, 2)
        })
        
        return results


class ProcessingError(Exception):
    """Custom exception for processing errors."""
    pass


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration.
    
    This function demonstrates how to configure logging properly
    with different handlers and formatters.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional file path for file logging.
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        logger.info("File logging enabled", extra={
            'log_file': log_file,
            'level': level
        })
    
    logger.info("Logging configuration completed", extra={
        'level': level,
        'file_logging': log_file is not None
    })


def demonstrate_logging_levels():
    """Demonstrate different logging levels with proper context."""
    
    # DEBUG level - detailed information for debugging
    logger.debug("Processing user request", extra={
        'user_id': 12345,
        'request_id': 'req-abc-123',
        'endpoint': '/api/documents',
        'method': 'POST'
    })
    
    # INFO level - general information about program execution
    logger.info("User authentication successful", extra={
        'user_id': 12345,
        'method': 'oauth2',
        'provider': 'google'
    })
    
    # WARNING level - something unexpected happened but the program can continue
    logger.warning("High memory usage detected", extra={
        'memory_usage': 85.5,
        'threshold': 80.0,
        'service': 'document_processor'
    })
    
    # ERROR level - a serious problem occurred
    logger.error("Database connection failed", extra={
        'database': 'postgresql',
        'error_code': 'ECONNREFUSED',
        'retry_attempt': 3,
        'max_retries': 5
    }, exc_info=True)
    
    # CRITICAL level - a critical error that may prevent the program from running
    logger.critical("Application startup failed", extra={
        'component': 'database',
        'error': 'Cannot connect to required services'
    }, exc_info=True)


def demonstrate_structured_logging():
    """Demonstrate structured logging with consistent context."""
    
    # Define common context
    request_context = {
        'request_id': 'req-xyz-789',
        'user_id': 67890,
        'session_id': 'sess-abc-456'
    }
    
    # Log with consistent context
    logger.info("Request processing started", extra=request_context)
    
    # Add operation-specific context
    operation_context = {**request_context, 'operation': 'document_upload'}
    logger.info("Document upload initiated", extra=operation_context)
    
    # Add performance metrics
    performance_context = {
        **operation_context,
        'processing_time_ms': 1250,
        'file_size_mb': 2.5
    }
    logger.info("Document upload completed", extra=performance_context)
    
    # Log errors with full context
    error_context = {
        **operation_context,
        'error_type': 'ValidationError',
        'error_message': 'File format not supported'
    }
    logger.error("Document upload failed", extra=error_context)


def demonstrate_logging_best_practices():
    """Demonstrate logging best practices and anti-patterns."""
    
    # ✅ GOOD: Clear, professional messages
    logger.info("Document processing completed successfully")
    logger.warning("High memory usage detected")
    logger.error("Database connection failed")
    
    # ❌ BAD: Emojis in log messages
    # logger.info("✅ Document processing completed successfully!")
    # logger.warning("⚠️  High memory usage detected!")
    # logger.error("💥 Database connection failed!")
    
    # ✅ GOOD: Structured logging with context
    logger.info("User login successful", extra={
        'user_id': 12345,
        'method': 'password',
        'ip_address': '192.168.1.100'
    })
    
    # ❌ BAD: Unstructured logging
    # logger.info("User 12345 logged in with password from IP 192.168.1.100")
    
    # ✅ GOOD: Appropriate log levels
    logger.debug("Processing step 1 of 5")  # Detailed debugging info
    logger.info("User session created")      # General information
    logger.warning("API rate limit approaching")  # Potential issue
    logger.error("Payment processing failed")     # Error condition
    
    # ❌ BAD: Wrong log levels
    # logger.error("User session created")  # Not an error
    # logger.info("Processing step 1 of 5")  # Too verbose for info
    
    # ✅ GOOD: Exception logging with context
    try:
        # Some operation that might fail
        raise ValueError("Invalid input data")
    except Exception as e:
        logger.error("Data validation failed", extra={
            'error_type': type(e).__name__,
            'error_message': str(e),
            'input_data': 'sample_data'
        }, exc_info=True)
    
    # ❌ BAD: Generic exception logging
    # try:
    #     # Some operation
    #     pass
    # except Exception as e:
    #     logger.error(f"Error: {e}")  # No context, no stack trace


if __name__ == "__main__":
    # Setup logging for demonstration
    setup_logging(level="DEBUG")
    
    # Demonstrate different logging practices
    demonstrate_logging_levels()
    demonstrate_structured_logging()
    demonstrate_logging_best_practices()
    
    # Demonstrate service with logging
    service = DocumentService()
    service.process_document("sample.pdf")
    service.batch_process(["doc1.pdf", "doc2.txt", "error.pdf"])
