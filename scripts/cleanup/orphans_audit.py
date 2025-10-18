#!/usr/bin/env python3
"""
Orphaned Data Audit Tool - Dry Run by Default

This script performs a comprehensive audit of orphaned data across:
- Azure Blob Storage (orphaned blobs)
- Database records (orphaned documents/contacts)
- Redis cache entries (orphaned keys)

By default, it runs in dry-run mode and only lists candidates for cleanup.
Use --force to perform actual deletion (use with extreme caution).

Usage:
    python scripts/cleanup/orphans_audit.py [--force] [--days 30] [--verbose]
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import django
from django.conf import settings
from django.utils import timezone

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup local environment if needed
try:
    from scripts.setup_local_env import setup_local_environment
    setup_local_environment()
except ImportError:
    pass

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

# Import Django models and utilities
from apps.documents.models import Document
from apps.directory.models import Contact
from django.core.cache import cache
from django.db import connection

# Import Azure utilities
try:
    from utilities.azureblobstorage import AzureBlobStorage
    from utilities.azure_search_client import AzureSearchClient
    AZURE_AVAILABLE = True
except ImportError:
    try:
        from utils.azureblobstorage import AzureBlobStorage
        from utils.azure_search_client import AzureSearchClient
        AZURE_AVAILABLE = True
    except ImportError:
        AZURE_AVAILABLE = False
        print("Warning: Azure utilities not available. Blob audit will be limited.")

# Import Redis utilities
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: Redis not available. Cache audit will be limited.")


class OrphanedDataAuditor:
    """Auditor for orphaned data across different storage systems."""
    
    def __init__(self, dry_run: bool = True, days_threshold: int = 30, verbose: bool = False):
        self.dry_run = dry_run
        self.days_threshold = days_threshold
        self.verbose = verbose
        self.cutoff_date = timezone.now() - timedelta(days=days_threshold)
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize storage clients
        self.blob_client = None
        self.redis_client = None
        self._initialize_clients()
        
        # Results storage
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'days_threshold': days_threshold,
            'cutoff_date': self.cutoff_date.isoformat(),
            'summary': {},
            'details': {
                'orphaned_blobs': [],
                'orphaned_documents': [],
                'orphaned_contacts': [],
                'orphaned_redis_keys': [],
                'orphaned_search_documents': []
            }
        }
    
    def _initialize_clients(self):
        """Initialize Azure and Redis clients if available."""
        try:
            if AZURE_AVAILABLE:
                self.blob_client = AzureBlobStorage()
                self.logger.info("Azure Blob Storage client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Azure client: {e}")
        
        try:
            if REDIS_AVAILABLE and hasattr(settings, 'REDIS_URL'):
                self.redis_client = redis.from_url(settings.REDIS_URL)
                self.redis_client.ping()  # Test connection
                self.logger.info("Redis client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Redis client: {e}")
    
    def audit_orphaned_blobs(self) -> List[Dict[str, Any]]:
        """Audit orphaned blobs in Azure Storage."""
        orphaned_blobs = []
        
        if not self.blob_client:
            self.logger.warning("Blob client not available - skipping blob audit")
            return orphaned_blobs
        
        try:
            # Get all blobs in the container
            container_name = getattr(settings, 'AZURE_STORAGE_CONTAINER_NAME', 'documents')
            blobs = self.blob_client.list_blobs(container_name)
            
            # Get all document records from database
            db_documents = set(Document.objects.values_list('file_path', flat=True))
            
            for blob in blobs:
                blob_name = blob.name
                blob_props = blob.properties
                
                # Check if blob is older than threshold
                if blob_props.last_modified and blob_props.last_modified.replace(tzinfo=None) < self.cutoff_date:
                    # Check if blob has no corresponding database record
                    if blob_name not in db_documents:
                        orphaned_blob = {
                            'name': blob_name,
                            'size': blob_props.size,
                            'last_modified': blob_props.last_modified.isoformat() if blob_props.last_modified else None,
                            'content_type': blob_props.content_settings.content_type,
                            'reason': 'No database reference found'
                        }
                        orphaned_blobs.append(orphaned_blob)
                        
                        if self.verbose:
                            self.logger.debug(f"Found orphaned blob: {blob_name}")
            
            self.logger.info(f"Found {len(orphaned_blobs)} orphaned blobs")
            
        except Exception as e:
            self.logger.error(f"Error auditing blobs: {e}")
        
        return orphaned_blobs
    
    def audit_orphaned_documents(self) -> List[Dict[str, Any]]:
        """Audit orphaned document records in database."""
        orphaned_documents = []
        
        try:
            # Find documents that reference non-existent blobs
            documents = Document.objects.all()
            
            for doc in documents:
                if not self.blob_client:
                    # Without blob client, we can only check for very old documents
                    if doc.date and doc.date < self.cutoff_date:
                        orphaned_doc = {
                            'id': doc.id,
                            'title': doc.title,
                            'file_path': str(doc.file) if doc.file else None,
                            'date': doc.date.isoformat() if doc.date else None,
                            'reason': 'Document older than threshold (blob client unavailable)'
                        }
                        orphaned_documents.append(orphaned_doc)
                else:
                    # Check if the referenced blob actually exists
                    container_name = getattr(settings, 'AZURE_STORAGE_CONTAINER_NAME', 'documents')
                    file_path = str(doc.file) if doc.file else None
                    if file_path and not self.blob_client.blob_exists(container_name, file_path):
                        orphaned_doc = {
                            'id': doc.id,
                            'title': doc.title,
                            'file_path': file_path,
                            'date': doc.date.isoformat() if doc.date else None,
                            'reason': 'Referenced blob does not exist'
                        }
                        orphaned_documents.append(orphaned_doc)
                        
                        if self.verbose:
                            self.logger.debug(f"Found orphaned document: {doc.title} (ID: {doc.id})")
            
            self.logger.info(f"Found {len(orphaned_documents)} orphaned documents")
            
        except Exception as e:
            self.logger.error(f"Error auditing documents: {e}")
        
        return orphaned_documents
    
    def audit_orphaned_contacts(self) -> List[Dict[str, Any]]:
        """Audit orphaned contact records in database."""
        orphaned_contacts = []
        
        try:
            # Find contacts that are very old and have no recent activity
            # This is a simplified check - in a real scenario, you might want to check
            # for contacts that have no associated documents, events, etc.
            old_contacts = Contact.objects.filter(
                created_at__lt=self.cutoff_date
            )
            
            for contact in old_contacts:
                orphaned_contact = {
                    'id': contact.id,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'role': contact.role,
                    'ministry': contact.ministry,
                    'contact': contact.contact,
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'reason': 'Contact older than threshold with no recent updates'
                }
                orphaned_contacts.append(orphaned_contact)
                
                if self.verbose:
                    contact_name = f"{contact.first_name} {contact.last_name}".strip()
                    self.logger.debug(f"Found orphaned contact: {contact_name} (ID: {contact.id})")
            
            self.logger.info(f"Found {len(orphaned_contacts)} orphaned contacts")
            
        except Exception as e:
            self.logger.error(f"Error auditing contacts: {e}")
        
        return orphaned_contacts
    
    def audit_orphaned_redis_keys(self) -> List[Dict[str, Any]]:
        """Audit orphaned Redis cache keys."""
        orphaned_keys = []
        
        if not self.redis_client:
            self.logger.warning("Redis client not available - skipping Redis audit")
            return orphaned_keys
        
        try:
            # Look for keys with specific patterns that might be orphaned
            patterns = [
                'vea:emb:*',  # Embedding cache keys
                'vea:ans:*',  # Answer cache keys
                'vea:sas:*',  # SAS token cache keys
                'cache:*',    # General cache keys
                'session:*'   # Session keys
            ]
            
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                
                for key in keys:
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    
                    # Check TTL - if it's very long or no TTL, it might be orphaned
                    ttl = self.redis_client.ttl(key)
                    
                    if ttl == -1:  # No expiration set
                        orphaned_key = {
                            'key': key_str,
                            'pattern': pattern,
                            'ttl': ttl,
                            'reason': 'No expiration set (potentially orphaned)'
                        }
                        orphaned_keys.append(orphaned_key)
                        
                        if self.verbose:
                            self.logger.debug(f"Found orphaned Redis key: {key_str}")
            
            self.logger.info(f"Found {len(orphaned_keys)} potentially orphaned Redis keys")
            
        except Exception as e:
            self.logger.error(f"Error auditing Redis keys: {e}")
        
        return orphaned_keys
    
    def audit_orphaned_search_documents(self) -> List[Dict[str, Any]]:
        """Audit orphaned documents in Azure AI Search index."""
        orphaned_search_docs = []
        
        try:
            # This would require Azure Search client
            # For now, we'll just log that this audit is not implemented
            self.logger.info("Search document audit not implemented (requires Azure Search client)")
            
        except Exception as e:
            self.logger.error(f"Error auditing search documents: {e}")
        
        return orphaned_search_docs
    
    def perform_cleanup(self, data_type: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform actual cleanup of orphaned items."""
        cleanup_results = {
            'data_type': data_type,
            'total_items': len(items),
            'successful_deletions': 0,
            'failed_deletions': 0,
            'errors': []
        }
        
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would delete {len(items)} {data_type}")
            return cleanup_results
        
        self.logger.warning(f"PERFORMING ACTUAL CLEANUP: Deleting {len(items)} {data_type}")
        
        for item in items:
            try:
                if data_type == 'blobs':
                    success = self._delete_blob(item['name'])
                elif data_type == 'documents':
                    success = self._delete_document(item['id'])
                elif data_type == 'contacts':
                    success = self._delete_contact(item['id'])
                elif data_type == 'redis_keys':
                    success = self._delete_redis_key(item['key'])
                else:
                    success = False
                
                if success:
                    cleanup_results['successful_deletions'] += 1
                else:
                    cleanup_results['failed_deletions'] += 1
                    
            except Exception as e:
                cleanup_results['failed_deletions'] += 1
                cleanup_results['errors'].append({
                    'item': item,
                    'error': str(e)
                })
                self.logger.error(f"Error deleting {data_type} item: {e}")
        
        return cleanup_results
    
    def _delete_blob(self, blob_name: str) -> bool:
        """Delete a blob from Azure Storage."""
        if not self.blob_client:
            return False
        
        try:
            container_name = getattr(settings, 'AZURE_STORAGE_CONTAINER_NAME', 'documents')
            self.blob_client.delete_blob(container_name, blob_name)
            self.logger.info(f"Deleted blob: {blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete blob {blob_name}: {e}")
            return False
    
    def _delete_document(self, doc_id: int) -> bool:
        """Delete a document record from database."""
        try:
            document = Document.objects.get(id=doc_id)
            document.delete()
            self.logger.info(f"Deleted document record: {doc_id}")
            return True
        except Document.DoesNotExist:
            self.logger.warning(f"Document {doc_id} already deleted")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    def _delete_contact(self, contact_id: int) -> bool:
        """Delete a contact record from database."""
        try:
            contact = Contact.objects.get(id=contact_id)
            contact.delete()
            self.logger.info(f"Deleted contact record: {contact_id}")
            return True
        except Contact.DoesNotExist:
            self.logger.warning(f"Contact {contact_id} already deleted")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete contact {contact_id}: {e}")
            return False
    
    def _delete_redis_key(self, key: str) -> bool:
        """Delete a Redis key."""
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            if result > 0:
                self.logger.info(f"Deleted Redis key: {key}")
                return True
            else:
                self.logger.warning(f"Redis key {key} already deleted or doesn't exist")
                return True
        except Exception as e:
            self.logger.error(f"Failed to delete Redis key {key}: {e}")
            return False
    
    def run_audit(self) -> Dict[str, Any]:
        """Run the complete orphaned data audit."""
        self.logger.info("Starting orphaned data audit...")
        self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'ACTUAL CLEANUP'}")
        self.logger.info(f"Days threshold: {self.days_threshold}")
        self.logger.info(f"Cutoff date: {self.cutoff_date}")
        
        # Run all audits
        self.audit_results['details']['orphaned_blobs'] = self.audit_orphaned_blobs()
        self.audit_results['details']['orphaned_documents'] = self.audit_orphaned_documents()
        self.audit_results['details']['orphaned_contacts'] = self.audit_orphaned_contacts()
        self.audit_results['details']['orphaned_redis_keys'] = self.audit_orphaned_redis_keys()
        self.audit_results['details']['orphaned_search_documents'] = self.audit_orphaned_search_documents()
        
        # Calculate summary
        total_orphaned = (
            len(self.audit_results['details']['orphaned_blobs']) +
            len(self.audit_results['details']['orphaned_documents']) +
            len(self.audit_results['details']['orphaned_contacts']) +
            len(self.audit_results['details']['orphaned_redis_keys']) +
            len(self.audit_results['details']['orphaned_search_documents'])
        )
        
        self.audit_results['summary'] = {
            'total_orphaned_items': total_orphaned,
            'orphaned_blobs': len(self.audit_results['details']['orphaned_blobs']),
            'orphaned_documents': len(self.audit_results['details']['orphaned_documents']),
            'orphaned_contacts': len(self.audit_results['details']['orphaned_contacts']),
            'orphaned_redis_keys': len(self.audit_results['details']['orphaned_redis_keys']),
            'orphaned_search_documents': len(self.audit_results['details']['orphaned_search_documents'])
        }
        
        self.logger.info("Audit completed!")
        self.logger.info(f"Total orphaned items found: {total_orphaned}")
        
        return self.audit_results
    
    def export_report(self, output_path: Optional[str] = None) -> str:
        """Export audit results to JSON file."""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"logs/cleanup_report_{timestamp}.json"
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.audit_results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Audit report exported to: {output_path}")
        return output_path


def main():
    """Main entry point for the orphaned data audit script."""
    parser = argparse.ArgumentParser(
        description="Audit orphaned data across storage systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run audit (default)
  python scripts/cleanup/orphans_audit.py
  
  # Dry run with custom threshold
  python scripts/cleanup/orphans_audit.py --days 60
  
  # Verbose dry run
  python scripts/cleanup/orphans_audit.py --verbose
  
  # ACTUAL CLEANUP (use with extreme caution!)
  python scripts/cleanup/orphans_audit.py --force
        """
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Perform actual deletion (default is dry-run)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Age threshold in days for considering items orphaned (default: 30)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Custom output path for the audit report'
    )
    
    args = parser.parse_args()
    
    # Safety check for force mode
    if args.force:
        print("\n" + "="*80)
        print("WARNING: FORCE MODE ENABLED")
        print("="*80)
        print("This will perform ACTUAL DELETION of orphaned data.")
        print("Make sure you have:")
        print("1. Reviewed the cleanup plan in docs/diagnostico/cleanup_plan.md")
        print("2. Verified the orphaned items in a dry-run first")
        print("3. Backed up any important data")
        print("4. Confirmed you want to proceed")
        print("="*80)
        
        response = input("\nType 'YES' to confirm deletion: ")
        if response != 'YES':
            print("Deletion cancelled.")
            sys.exit(0)
        
        print("Proceeding with deletion...")
    
    # Create and run auditor
    auditor = OrphanedDataAuditor(
        dry_run=not args.force,
        days_threshold=args.days,
        verbose=args.verbose
    )
    
    try:
        # Run audit
        results = auditor.run_audit()
        
        # Export report
        report_path = auditor.export_report(args.output)
        
        # Print summary
        print("\n" + "="*60)
        print("AUDIT SUMMARY")
        print("="*60)
        print(f"Mode: {'DRY RUN' if not args.force else 'ACTUAL CLEANUP'}")
        print(f"Days threshold: {args.days}")
        print(f"Total orphaned items: {results['summary']['total_orphaned_items']}")
        print(f"  - Blobs: {results['summary']['orphaned_blobs']}")
        print(f"  - Documents: {results['summary']['orphaned_documents']}")
        print(f"  - Contacts: {results['summary']['orphaned_contacts']}")
        print(f"  - Redis keys: {results['summary']['orphaned_redis_keys']}")
        print(f"  - Search documents: {results['summary']['orphaned_search_documents']}")
        print(f"Report saved to: {report_path}")
        print("="*60)
        
        if not args.force and results['summary']['total_orphaned_items'] > 0:
            print("\nTo perform actual cleanup, run with --force flag")
            print("IMPORTANT: Review the cleanup plan first!")
        
    except KeyboardInterrupt:
        print("\nAudit interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during audit: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
