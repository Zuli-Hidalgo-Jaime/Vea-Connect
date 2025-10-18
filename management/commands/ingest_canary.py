"""
Django management command for canary ingestion testing.

This command processes PDF and image files with vision/OCR without indexing
to test the ingestion pipeline in isolation.
"""

import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# Import vision service
try:
    from apps.vision.azure_vision_service import AzureVisionService
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

# Import embedding service
try:
    from utilities.embedding_manager import EmbeddingManager
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Canary ingestion command for testing vision/OCR processing.
    
    Processes PDF and image files without indexing to test the pipeline
    in isolation. Outputs processed data to stdout for inspection.
    """
    
    help = 'Test ingestion pipeline with vision/OCR processing (canary mode)'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--path',
            type=str,
            required=True,
            help='Path to test folder containing PDF and image files'
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=1000,
            help='Chunk size for text splitting (default: 1000)'
        )
        parser.add_argument(
            '--overlap',
            type=int,
            default=200,
            help='Overlap between chunks (default: 200)'
        )
        parser.add_argument(
            '--output-format',
            choices=['json', 'text', 'summary'],
            default='summary',
            help='Output format (default: summary)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        # Check if canary mode is enabled
        if not self.is_canary_enabled():
            self.stdout.write(
                self.style.WARNING('Canary ingestion is disabled. Set CANARY_INGEST_ENABLED=True to enable.')
            )
            return
        
        # Validate path
        test_path = Path(options['path'])
        if not test_path.exists():
            raise CommandError(f"Test path does not exist: {test_path}")
        if not test_path.is_dir():
            raise CommandError(f"Test path is not a directory: {test_path}")
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting canary ingestion test')
        )
        self.stdout.write('=' * 60)
        
        # Initialize services
        services = self.initialize_services()
        
        # Process files
        results = self.process_test_folder(
            test_path, 
            services, 
            options['chunk_size'],
            options['overlap'],
            options['verbose']
        )
        
        # Output results
        self.output_results(results, options['output_format'])
        
        self.stdout.write(
            self.style.SUCCESS('🏁 Canary ingestion test completed')
        )
    
    def is_canary_enabled(self) -> bool:
        """Check if canary mode is enabled."""
        return getattr(settings, 'CANARY_INGEST_ENABLED', False)
    
    def initialize_services(self) -> Dict[str, Any]:
        """Initialize required services."""
        services = {
            'vision_available': VISION_AVAILABLE,
            'embedding_available': EMBEDDING_AVAILABLE,
            'vision_service': None,
            'embedding_manager': None
        }
        
        # Initialize vision service
        if VISION_AVAILABLE:
            try:
                services['vision_service'] = AzureVisionService()
                if services['vision_service'].is_service_available():
                    self.stdout.write(
                        self.style.SUCCESS('✅ Azure Vision service available')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️ Azure Vision service not available')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to initialize Vision service: {e}')
                )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ Azure Vision service not available (import failed)')
            )
        
        # Initialize embedding manager
        if EMBEDDING_AVAILABLE:
            try:
                services['embedding_manager'] = EmbeddingManager()
                self.stdout.write(
                    self.style.SUCCESS('✅ Embedding manager available')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Embedding manager not available: {e}')
                )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ Embedding manager not available (import failed)')
            )
        
        return services
    
    def process_test_folder(
        self, 
        folder_path: Path, 
        services: Dict[str, Any],
        chunk_size: int,
        overlap: int,
        verbose: bool
    ) -> List[Dict[str, Any]]:
        """Process all files in the test folder."""
        results = []
        
        # Supported file extensions
        supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        # Find all supported files
        files = []
        for ext in supported_extensions:
            files.extend(folder_path.glob(f'*{ext}'))
            files.extend(folder_path.glob(f'*{ext.upper()}'))
        
        if not files:
            self.stdout.write(
                self.style.WARNING(f'No supported files found in: {folder_path}')
            )
            return results
        
        self.stdout.write(f'Found {len(files)} files to process')
        
        # Process each file
        for file_path in files:
            try:
                result = self.process_single_file(
                    file_path, 
                    services, 
                    chunk_size, 
                    overlap, 
                    verbose
                )
                results.append(result)
            except Exception as e:
                error_result = {
                    'file_path': str(file_path),
                    'status': 'error',
                    'error': str(e),
                    'processing_time': 0
                }
                results.append(error_result)
                self.stdout.write(
                    self.style.ERROR(f'❌ Error processing {file_path.name}: {e}')
                )
        
        return results
    
    def process_single_file(
        self, 
        file_path: Path, 
        services: Dict[str, Any],
        chunk_size: int,
        overlap: int,
        verbose: bool
    ) -> Dict[str, Any]:
        """Process a single file with vision/OCR."""
        import time
        start_time = time.time()
        
        result = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_extension': file_path.suffix.lower(),
            'status': 'processing',
            'processing_time': 0,
            'sha256': None,
            'extracted_text': None,
            'chunks': [],
            'embeddings': [],
            'payloads': []
        }
        
        # Calculate SHA256
        result['sha256'] = self.calculate_sha256(file_path)
        
        # Extract text based on file type
        if file_path.suffix.lower() == '.pdf':
            result['extracted_text'] = self.extract_text_from_pdf(
                file_path, services['vision_service']
            )
        else:
            result['extracted_text'] = self.extract_text_from_image(
                file_path, services['vision_service']
            )
        
        if not result['extracted_text']:
            result['status'] = 'no_text_extracted'
            result['processing_time'] = time.time() - start_time
            return result
        
        # Generate chunks
        result['chunks'] = self.generate_chunks(
            result['extracted_text'], 
            chunk_size, 
            overlap
        )
        
        # Generate embeddings (if available)
        if services['embedding_manager'] and result['chunks']:
            result['embeddings'] = self.generate_embeddings(
                result['chunks'], 
                services['embedding_manager']
            )
        
        # Generate search payloads
        result['payloads'] = self.generate_search_payloads(
            result['chunks'],
            result['embeddings'],
            result['sha256'],
            file_path.name
        )
        
        result['status'] = 'success'
        result['processing_time'] = time.time() - start_time
        
        if verbose:
            self.stdout.write(f'✅ Processed {file_path.name} in {result["processing_time"]:.2f}s')
        
        return result
    
    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def extract_text_from_pdf(
        self, 
        file_path: Path, 
        vision_service: Optional[Any]
    ) -> Optional[str]:
        """Extract text from PDF file."""
        if not vision_service:
            return f"[MOCK] PDF text extraction for {file_path.name}"
        
        try:
            return vision_service.extract_text_from_pdf(str(file_path))
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return None
    
    def extract_text_from_image(
        self, 
        file_path: Path, 
        vision_service: Optional[Any]
    ) -> Optional[str]:
        """Extract text from image file."""
        if not vision_service:
            return f"[MOCK] Image text extraction for {file_path.name}"
        
        try:
            return vision_service.extract_text_from_image(str(file_path))
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {e}")
            return None
    
    def generate_chunks(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: int
    ) -> List[Dict[str, Any]]:
        """Generate text chunks with overlap."""
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this is not the last chunk, try to break at a word boundary
            if end < len(text):
                # Look for the last space or punctuation in the chunk
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'start': start,
                    'end': end,
                    'length': len(chunk_text)
                })
            
            # Move start position for next chunk
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def generate_embeddings(
        self, 
        chunks: List[Dict[str, Any]], 
        embedding_manager: Any
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for text chunks."""
        embeddings = []
        
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                embedding_result = embedding_manager.openai_service.generate_embedding(
                    chunk['text']
                )
                
                embeddings.append({
                    'chunk_index': i,
                    'embedding': embedding_result,
                    'dimensions': len(embedding_result) if embedding_result else 0
                })
            except Exception as e:
                logger.error(f"Error generating embedding for chunk {i}: {e}")
                embeddings.append({
                    'chunk_index': i,
                    'embedding': None,
                    'error': str(e)
                })
        
        return embeddings
    
    def generate_search_payloads(
        self, 
        chunks: List[Dict[str, Any]],
        embeddings: List[Dict[str, Any]],
        sha256: str,
        filename: str
    ) -> List[Dict[str, Any]]:
        """Generate search payloads ready for indexing."""
        payloads = []
        
        for i, chunk in enumerate(chunks):
            # Find corresponding embedding
            embedding = None
            for emb in embeddings:
                if emb['chunk_index'] == i:
                    embedding = emb
                    break
            
            payload = {
                'id': f"{sha256}_{i}",
                'document_id': sha256,
                'text': chunk['text'],
                'title': filename,
                'content': chunk['text'],
                'embedding': embedding['embedding'] if embedding and embedding.get('embedding') else None,
                'metadata': json.dumps({
                    'filename': filename,
                    'sha256': sha256,
                    'chunk_index': i,
                    'chunk_start': chunk['start'],
                    'chunk_end': chunk['end'],
                    'chunk_length': chunk['length'],
                    'source_type': 'canary_test'
                }),
                'created_at': None,  # Will be set by search service
                'updated_at': None,  # Will be set by search service
                'source_type': 'canary_test',
                'filename': filename
            }
            
            payloads.append(payload)
        
        return payloads
    
    def output_results(
        self, 
        results: List[Dict[str, Any]], 
        output_format: str
    ):
        """Output results in specified format."""
        if output_format == 'json':
            self.stdout.write(json.dumps(results, indent=2, default=str))
        elif output_format == 'text':
            self.output_text_format(results)
        else:  # summary
            self.output_summary_format(results)
    
    def output_text_format(self, results: List[Dict[str, Any]]):
        """Output results in text format."""
        for result in results:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"File: {result['file_name']}")
            self.stdout.write(f"Status: {result['status']}")
            self.stdout.write(f"Processing Time: {result['processing_time']:.2f}s")
            self.stdout.write(f"SHA256: {result['sha256']}")
            self.stdout.write(f"Chunks: {len(result['chunks'])}")
            self.stdout.write(f"Embeddings: {len(result['embeddings'])}")
            self.stdout.write(f"Payloads: {len(result['payloads'])}")
            
            if result.get('extracted_text'):
                self.stdout.write(f"\nExtracted Text (first 500 chars):")
                self.stdout.write(result['extracted_text'][:500] + "...")
    
    def output_summary_format(self, results: List[Dict[str, Any]]):
        """Output results in summary format."""
        total_files = len(results)
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = total_files - successful
        
        total_chunks = sum(len(r.get('chunks', [])) for r in results)
        total_embeddings = sum(len(r.get('embeddings', [])) for r in results)
        total_payloads = sum(len(r.get('payloads', [])) for r in results)
        
        total_time = sum(r.get('processing_time', 0) for r in results)
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS('CANARY INGESTION SUMMARY'))
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Total Files: {total_files}")
        self.stdout.write(f"Successful: {successful}")
        self.stdout.write(f"Failed: {failed}")
        self.stdout.write(f"Total Chunks: {total_chunks}")
        self.stdout.write(f"Total Embeddings: {total_embeddings}")
        self.stdout.write(f"Total Payloads: {total_payloads}")
        self.stdout.write(f"Total Processing Time: {total_time:.2f}s")
        
        if successful > 0:
            avg_time = total_time / successful
            self.stdout.write(f"Average Time per File: {avg_time:.2f}s")
        
        # Show failed files
        if failed > 0:
            self.stdout.write(f"\nFailed Files:")
            for result in results:
                if result['status'] != 'success':
                    self.stdout.write(f"  - {result['file_name']}: {result.get('error', 'Unknown error')}")
        
        # Show sample payload structure
        if results and results[0].get('payloads'):
            sample_payload = results[0]['payloads'][0]
            self.stdout.write(f"\nSample Payload Structure:")
            self.stdout.write(f"  ID: {sample_payload['id']}")
            self.stdout.write(f"  Document ID: {sample_payload['document_id']}")
            self.stdout.write(f"  Text Length: {len(sample_payload['text'])}")
            self.stdout.write(f"  Has Embedding: {sample_payload['embedding'] is not None}")
            self.stdout.write(f"  Metadata: {sample_payload['metadata'][:100]}...")
