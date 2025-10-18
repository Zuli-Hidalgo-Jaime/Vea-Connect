"""
Azure Storage Service for file operations.

This service provides a unified interface for Azure Blob Storage operations
with proper error handling and fallback mechanisms.
"""

import os
import logging
import hashlib
import json
import re
import unicodedata
from typing import Dict, Any, Optional, Union, List, Tuple
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from django.conf import settings

logger = logging.getLogger(__name__)


class AzureStorageService:
    """
    Service for Azure Blob Storage operations.
    
    Provides methods for uploading, downloading, and managing files
    with proper error handling and retry logic.
    """
    
    def __init__(self):
        """Initialize the Azure Storage service."""
        self.connection_string = self._get_setting('AZURE_STORAGE_CONNECTION_STRING')
        self.account_name = self._get_setting('AZURE_STORAGE_ACCOUNT_NAME')
        self.account_key = self._get_setting('AZURE_STORAGE_ACCOUNT_KEY')
        self.container_name = self._get_setting('AZURE_STORAGE_CONTAINER_NAME', 'vea-connect-files')
        
        # Initialize Azure SDK client if credentials are available
        self.client = None
        if self.connection_string or (self.account_name and self.account_key):
            try:
                from azure.storage.blob import BlobServiceClient
                
                if self.connection_string:
                    self.client = BlobServiceClient.from_connection_string(self.connection_string)
                else:
                    from azure.storage.blob import BlobServiceClient
                    account_url = f"https://{self.account_name}.blob.core.windows.net"
                    self.client = BlobServiceClient(account_url=account_url, credential=self.account_key)
                
                logger.info("Azure Storage service initialized successfully")
            except ImportError:
                logger.warning("Azure Storage SDK not available")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Storage client: {e}")
        else:
            logger.warning("Azure Storage credentials not configured")

    def _ensure_client(self) -> bool:
        """Ensure the Azure Blob client is initialized (lazy init for background threads)."""
        if self.client is not None:
            return True
        try:
            # Re-read settings/env in case the process/thread missed initial load
            self.connection_string = self._get_setting('AZURE_STORAGE_CONNECTION_STRING')
            self.account_name = self._get_setting('AZURE_STORAGE_ACCOUNT_NAME')
            self.account_key = self._get_setting('AZURE_STORAGE_ACCOUNT_KEY')
            self.container_name = self._get_setting('AZURE_STORAGE_CONTAINER_NAME', 'vea-connect-files')

            if not (self.connection_string or (self.account_name and self.account_key)):
                logger.error("Azure Storage credentials not available for lazy init")
                return False

            from azure.storage.blob import BlobServiceClient
            if self.connection_string:
                self.client = BlobServiceClient.from_connection_string(self.connection_string)
            else:
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                self.client = BlobServiceClient(account_url=account_url, credential=self.account_key)
            logger.info("Azure Storage client lazily initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to lazily initialize Azure Storage client: {e}")
            return False
    
    def _get_setting(self, setting_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get setting value with fallback to environment variables."""
        try:
            # Try Django settings first
            value = getattr(settings, setting_name, None)
            if value:
                return value
        except Exception:
            pass
        
        # Fallback to environment variables
        return os.environ.get(setting_name, default)
    
    def canonicalize_blob_name(self, original: str, *, category: Optional[str] = None) -> str:
        """
        Canonicalize blob name for consistent storage.
        
        Args:
            original: Original filename
            category: Optional category prefix (e.g., 'documents', 'contacts')
            
        Returns:
            Canonicalized blob name
        """
        # Normalize unicode characters
        normalized = unicodedata.normalize('NFD', original)
        
        # Convert to ASCII and lowercase
        ascii_name = normalized.encode('ascii', 'ignore').decode('ascii').lower()
        
        # Replace spaces and unsafe characters
        safe_name = re.sub(r'[^a-z0-9._-]', '_', ascii_name)
        
        # Remove multiple consecutive underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # Remove leading/trailing underscores
        safe_name = safe_name.strip('_')
        
        # Preserve file extension
        name_parts = safe_name.rsplit('.', 1)
        if len(name_parts) > 1 and len(name_parts[1]) <= 5:  # Likely extension
            base_name = name_parts[0]
            extension = name_parts[1]
        else:
            base_name = safe_name
            extension = ''
        
        # Add timestamp and hash for uniqueness
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')
        hash_suffix = hashlib.md5(original.encode()).hexdigest()[:6]
        
        canonical_name = f"{base_name}_{timestamp}_{hash_suffix}"
        if extension:
            canonical_name += f".{extension}"
        
        # Add category prefix if provided
        if category:
            # Evitar doble prefijo: si el nombre ya tiene el prefijo de la categoría, no agregarlo
            if not canonical_name.startswith(f"{category}/"):
                canonical_name = f"{category}/{canonical_name}"
        
        logger.debug(
            "canonicalize_blob_name: original='%s' category='%s' -> '%s'",
            original,
            category,
            canonical_name,
        )
        return canonical_name
    
    def ensure_container(self, container: str) -> bool:
        """
        Ensure container exists, create if it doesn't.
        
        Args:
            container: Container name
            
        Returns:
            True if container exists or was created successfully
        """
        try:
            if not self.client and not self._ensure_client():
                return False
            
            if not self.client:
                logger.error("Azure Storage client not available")
                return False
                
            container_client = self.client.get_container_client(container)
            container_client.get_container_properties()
            return True
        except Exception:
            try:
                container_client.create_container()
                logger.info(f"Created container: {container}")
                return True
            except Exception as e:
                logger.error(f"Failed to create container {container}: {e}")
                return False
    
    def resolve_blob_name(
        self, 
        name: str, 
        *, 
        categories: Tuple[str, ...] = ('documents', 'contacts', 'events', 'converted', 'conversations'),
        container: Optional[str] = None
    ) -> Optional[str]:
        """
        Resolve blob name using multiple strategies.
        
        Args:
            name: Original or canonical blob name
            categories: Categories to try as prefixes
            container: Container name (uses default if None)
            
        Returns:
            Resolved blob name or None if not found
        """
        if not self.client and not self._ensure_client():
            return None
        
        container = (container or self.container_name) or 'vea-connect-files'
        logger.debug(f"resolve_blob_name: input='{name}', container='{container}'")

        # Normalize duplicated category prefixes like "documents/documents/..."
        try:
            original_input_name = name
            for category in categories:
                double_prefix = f"{category}/{category}/"
                while name.startswith(double_prefix):
                    name = name[len(category)+1:]
            if original_input_name != name:
                # Quick check after normalization
                if self._blob_exists_direct(container, name):
                    logger.debug(f"resolve_blob_name: found after prefix normalization -> {name}")
                    return name
        except Exception:
            # Best-effort normalization; continue if anything goes wrong
            pass
        attempted_names = []
        
        # Strategy 1: Try exact match with retries (Azure eventual consistency)
        exists_result = False
        for attempt in range(3):  # 3 intentos con delay
            exists_result = self._blob_exists_direct(container, name)
            if exists_result:
                logger.debug(f"resolve_blob_name: exact match -> {name}")
                return name
            if attempt < 2:  # No delay en el último intento
                import time
                time.sleep(0.5)  # 500ms delay
        attempted_names.append(name)
        
        # Strategy 2: Try with/without category prefixes
        for category in categories:
            # Try adding prefix
            prefixed_name = f"{category}/{name}"
            if self._blob_exists_direct(container, prefixed_name):
                logger.debug(f"resolve_blob_name: with prefix -> {prefixed_name}")
                return prefixed_name
            attempted_names.append(prefixed_name)
            
            # Try removing prefix if name starts with category
            if name.startswith(f"{category}/"):
                unprefixed_name = name[len(f"{category}/"):]
                if self._blob_exists_direct(container, unprefixed_name):
                    logger.debug(f"resolve_blob_name: without prefix -> {unprefixed_name}")
                    return unprefixed_name
                attempted_names.append(unprefixed_name)
        
        # Strategy 3: Try URL-encoded version
        quoted_name = quote_plus(name)
        if quoted_name != name and self._blob_exists_direct(container, quoted_name):
            logger.debug(f"resolve_blob_name: URL-encoded -> {quoted_name}")
            return quoted_name
        attempted_names.append(quoted_name)
        
        # Strategy 4: Search by metadata
        resolved_by_metadata = self._resolve_by_metadata(container, name, categories)
        if resolved_by_metadata:
            logger.debug(f"resolve_blob_name: by metadata -> {resolved_by_metadata}")
            return resolved_by_metadata
        
        # Strategy 5: Check manifest
        resolved_by_manifest = self._resolve_by_manifest(container, name)
        if resolved_by_manifest:
            logger.debug(f"resolve_blob_name: by manifest -> {resolved_by_manifest}")
            return resolved_by_manifest

        # Strategy 6: Suffix match by basename within known categories (last resort)
        try:
            assert self.client is not None
            from os.path import basename
            base = basename(name)
            container_client = self.client.get_container_client(container)
            # Search under likely category prefixes to limit listing
            for cat in categories:
                for blob in container_client.list_blobs(name_starts_with=f"{cat}/"):
                    if str(blob.name).endswith(f"/{base}") or str(blob.name) == base:
                        logger.debug(f"resolve_blob_name: by suffix match -> {blob.name}")
                        return blob.name
        except Exception as e:
            logger.debug(f"resolve_blob_name: suffix match failed: {e}")
        
        logger.info(f"resolve_blob_name: NOT FOUND after {len(attempted_names)} tries. first_attempts={attempted_names[:5]}")
        return None
    
    def _blob_exists_direct(self, container: str, blob_name: str) -> bool:
        """Direct blob existence check without logging."""
        try:
            assert self.client is not None
            blob_client = self.client.get_blob_client(container=container, blob=blob_name)
            return blob_client.exists()
        except Exception:
            return False
    
    def _resolve_by_metadata(self, container: str, original_name: str, categories: Tuple[str, ...]) -> Optional[str]:
        """Resolve blob name by searching metadata."""
        try:
            assert self.client is not None
            container_client = self.client.get_container_client(container)
            original_name_lower = original_name.lower()
            
            for blob in container_client.list_blobs():
                if not blob.metadata:
                    continue
                
                # Check original_name metadata
                meta_original = blob.metadata.get('original_name', '').lower()
                if meta_original == original_name_lower:
                    # Check category if specified
                    meta_category = blob.metadata.get('category', '')
                    if not meta_category or meta_category in categories:
                        return blob.name
                
                # Check without category prefix
                if original_name_lower.startswith(f"{meta_category}/"):
                    unprefixed = original_name_lower[len(f"{meta_category}/"):]
                    if meta_original == unprefixed:
                        return blob.name
            
            return None
        except Exception as e:
            logger.debug(f"Metadata resolution failed: {e}")
            return None
    
    def _resolve_by_manifest(self, container: str, original_name: str) -> Optional[str]:
        """Resolve blob name using manifest file."""
        try:
            assert self.client is not None
            manifest_blob = self.client.get_blob_client(container=container, blob="__manifest/manifest.json")
            if not manifest_blob.exists():
                return None
            
            # Download and parse manifest
            manifest_data = manifest_blob.download_blob().readall()
            manifest = json.loads(manifest_data.decode('utf-8'))
            
            original_name_lower = original_name.lower()
            entry = manifest.get(original_name_lower)
            if entry:
                return entry.get('blob')
            
            return None
        except Exception as e:
            logger.debug(f"Manifest resolution failed: {e}")
            return None
    
    def _update_manifest(self, container: Optional[str], original_name: str, blob_name: str, category: Optional[str] = None):
        """Update manifest file with new blob entry."""
        try:
            assert self.client is not None
            container = (container or self.container_name) or 'vea-connect-files'
            manifest_blob = self.client.get_blob_client(container=container, blob="__manifest/manifest.json")
            
            # Load existing manifest or create new
            manifest = {}
            if manifest_blob.exists():
                try:
                    manifest_data = manifest_blob.download_blob().readall()
                    manifest = json.loads(manifest_data.decode('utf-8'))
                except Exception:
                    manifest = {}
            
            # Add new entry
            original_name_lower = original_name.lower()
            manifest[original_name_lower] = {
                'blob': blob_name,
                'category': self._sanitize_metadata_value(category or ''),
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
            # Keep manifest size manageable (last 1000 entries)
            if len(manifest) > 1000:
                # Sort by upload time and keep recent
                sorted_entries = sorted(manifest.items(), 
                                      key=lambda x: x[1].get('uploaded_at', ''), 
                                      reverse=True)
                manifest = dict(sorted_entries[:1000])
            
            # Upload updated manifest
            manifest_json = json.dumps(manifest, indent=2)
            manifest_blob.upload_blob(manifest_json.encode('utf-8'), overwrite=True)
            
        except Exception as e:
            logger.warning(f"Failed to update manifest: {e}")
    
    def upload_file(
        self, 
        file_path: str, 
        blob_name: str, 
        container_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Azure Blob Storage.
        
        Args:
            file_path: Local path to the file
            blob_name: Name for the blob in storage
            container_name: Container name (uses default if None)
            content_type: Content type of the file
            metadata: Custom metadata for the blob
            category: Category for the blob (e.g., 'documents', 'contacts')
            
        Returns:
            Dictionary with upload result
        """
        try:
            if not self.client and not self._ensure_client():
                return {
                    'success': False,
                    'error': 'Azure Storage client not initialized'
                }
            
            container = (container_name or self.container_name) or 'vea-connect-files'
            self.ensure_container(container)
            
            # Canonicalize blob name
            original_name = blob_name
            canonical_name = self.canonicalize_blob_name(original_name, category=category)
            
            # Prepare metadata
            upload_metadata = metadata or {}
            upload_metadata.update({
                'original_name': self._sanitize_metadata_value(original_name),
                'category': self._sanitize_metadata_value(category or ''),
                'uploaded_at_utc': datetime.utcnow().isoformat(),
                'content_type': self._sanitize_metadata_value(content_type or '')
            })
            
            assert self.client is not None
            blob_client = self.client.get_blob_client(container=container, blob=canonical_name)
            
            # Upload the file
            with open(file_path, 'rb') as data:
                # Prefer setting Content-Disposition at upload time to avoid SDK header quirks
                try:
                    from azure.storage.blob import ContentSettings as _BlobContentSettings
                    cs = _BlobContentSettings(
                        content_type=(content_type or None),
                        content_disposition=(f'attachment; filename="{original_name}"' if original_name != canonical_name else None)
                    )
                except Exception:
                    cs = None
                blob_client.upload_blob(
                    data,
                    overwrite=True,
                    content_settings=cs,
                    metadata=upload_metadata
                )
            
            # Set content disposition for original filename
            if original_name != canonical_name:
                try:
                    from azure.storage.blob import BlobHTTPHeaders
                    blob_client.set_http_headers(
                        blob_http_headers=BlobHTTPHeaders(content_disposition=f'attachment; filename="{original_name}"')
                    )
                except Exception as e:
                    # If setting headers post-upload fails, we've already attempted via ContentSettings.
                    logger.debug(f"Skipping set_http_headers fallback for {original_name}: {e}")
            
            # Get the blob URL
            blob_url = blob_client.url
            
            # Update manifest
            self._update_manifest(container, original_name, canonical_name, category)
            
            logger.info(f"File uploaded successfully: {original_name} -> {canonical_name} "
                       f"(category: {category}, content_type: {content_type})")
            
            return {
                'success': True,
                'original_name': self._sanitize_metadata_value(original_name),
                'blob_name': canonical_name,
                'blob_url': blob_url,
                'container': container,
                'size': os.path.getsize(file_path),
                'category': category
            }
            
        except Exception as e:
            logger.exception(f"Failed to upload file {file_path}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'blob_name': blob_name
            }
    
    def upload_data(
        self, 
        data: bytes, 
        blob_name: str, 
        container_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload data bytes to Azure Blob Storage.
        
        Args:
            data: Data bytes to upload
            blob_name: Name for the blob in storage
            container_name: Container name (uses default if None)
            content_type: Content type of the data
            metadata: Custom metadata for the blob
            category: Category for the blob (e.g., 'documents', 'contacts')
            
        Returns:
            Dictionary with upload result
        """
        try:
            if not self.client and not self._ensure_client():
                return {
                    'success': False,
                    'error': 'Azure Storage client not initialized'
                }
            
            container = (container_name or self.container_name) or 'vea-connect-files'
            self.ensure_container(container)
            
            # Canonicalize blob name
            original_name = blob_name
            canonical_name = self.canonicalize_blob_name(original_name, category=category)
            
            # Prepare metadata
            upload_metadata = metadata or {}
            upload_metadata.update({
                'original_name': self._sanitize_metadata_value(original_name),
                'category': self._sanitize_metadata_value(category or ''),
                'uploaded_at_utc': datetime.utcnow().isoformat(),
                'content_type': self._sanitize_metadata_value(content_type or '')
            })
            
            assert self.client is not None
            blob_client = self.client.get_blob_client(container=container, blob=canonical_name)
            
            # Debug: Log metadata before upload
            logger.info(f"Uploading blob '{canonical_name}' with metadata: {upload_metadata}")
            
            # Upload the data
            try:
                from azure.storage.blob import ContentSettings as _BlobContentSettings
                
                # Sanitize filename for content_disposition
                sanitized_filename = self._sanitize_metadata_value(original_name)
                
                cs = _BlobContentSettings(
                    content_type=(content_type or None),
                    content_disposition=(f'attachment; filename="{sanitized_filename}"' if original_name != canonical_name else None)
                )
            except Exception:
                cs = None
            
            # DEBUG: Mostrar información antes del upload
            logger.debug(
                "UPLOAD DEBUG: size_bytes=%s container=%s blob=%s url=%s",
                len(data),
                container,
                canonical_name,
                blob_client.url,
            )
            
            # TEMPORARY FIX: Upload without metadata to avoid InvalidMetadata error
            upload_result = blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=cs
                # metadata=upload_metadata  # Commented out temporarily
            )
            
            logger.debug("UPLOAD DEBUG: upload_blob() returned: %s", upload_result)
            logger.debug("UPLOAD DEBUG: Upload completed successfully")
            
            # VERIFICACIÓN REAL: Verificar que el blob específico existe
            try:
                exists_check = blob_client.exists()
                logger.debug("UPLOAD DEBUG: blob_client.exists() = %s", exists_check)
                
                # Verificación adicional: intentar descargar el blob
                try:
                    blob_properties = blob_client.get_blob_properties()
                    logger.debug(
                        "UPLOAD DEBUG: Blob properties: %s (%s bytes)",
                        getattr(blob_properties, 'name', canonical_name),
                        getattr(blob_properties, 'size', 'unknown'),
                    )
                    logger.debug("UPLOAD DEBUG: Blob confirmado en Azure: %s", canonical_name)
                except Exception as prop_e:
                    logger.debug("UPLOAD DEBUG: Error obteniendo propiedades del blob: %s", prop_e)
                    logger.debug("UPLOAD DEBUG: posible inexistencia real de blob: %s", canonical_name)
                
            except Exception as e:
                logger.debug("UPLOAD DEBUG: Error verificando blob exists: %s", e)
            
            # Set content disposition for original filename
            if original_name != canonical_name:
                try:
                    from azure.storage.blob import BlobHTTPHeaders
                    sanitized_filename = self._sanitize_metadata_value(original_name)
                    blob_client.set_http_headers(
                        blob_http_headers=BlobHTTPHeaders(content_disposition=f'attachment; filename="{sanitized_filename}"')
                    )
                except Exception as e:
                    logger.debug(f"Skipping set_http_headers fallback for {original_name}: {e}")
            
            # Get the blob URL
            blob_url = blob_client.url
            
            # Update manifest
            self._update_manifest(container, original_name, canonical_name, category)
            
            logger.info(
                "Data uploaded successfully: %s -> %s (category=%s, content_type=%s)",
                original_name,
                canonical_name,
                category,
                content_type,
            )
            
            return {
                'success': True,
                'original_name': self._sanitize_metadata_value(original_name),
                'blob_name': canonical_name,
                'blob_url': blob_url,
                'container': container,
                'size': len(data),
                'category': category
            }
            
        except Exception as e:
            logger.exception(f"Failed to upload data for blob {blob_name}")
            return {
                'success': False,
                'error': str(e),
                'blob_name': blob_name
            }
    
    def download_file(
        self, 
        blob_name: str, 
        local_path: str, 
        container_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download a file from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob to download
            local_path: Local path where to save the file
            container_name: Container name (uses default if None)
            
        Returns:
            Dictionary with download result
        """
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Azure Storage client not initialized'
                }
            
            container = (container_name or self.container_name) or 'vea-connect-files'
            
            # Resolve blob name
            resolved_name = self.resolve_blob_name(blob_name, container=container)
            if not resolved_name:
                logger.info(f"Blob not found: {blob_name}. "
                           f"Pruebe con categoría 'documents' o verifique el nombre exacto")
                return {
                    'success': False,
                    'error': 'Blob not found',
                    'blob_name': blob_name,
                    'suggestion': 'Pruebe con categoría "documents" o verifique el nombre exacto'
                }
            
            assert self.client is not None
            blob_client = self.client.get_blob_client(container=container, blob=resolved_name)
            
            # Download the blob
            with open(local_path, 'wb') as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            
            logger.info(f"File downloaded successfully: {resolved_name} -> {local_path}")
            
            return {
                'success': True,
                'original_name': blob_name,
                'resolved_name': resolved_name,
                'local_path': local_path,
                'size': os.path.getsize(local_path)
            }
            
        except Exception as e:
            logger.exception(f"Failed to download blob {blob_name}")
            return {
                'success': False,
                'error': str(e),
                'blob_name': blob_name,
                'local_path': local_path
            }
    
    def download_to_tempfile(
        self, 
        blob_name: str, 
        container_name: Optional[str] = None
    ) -> str:
        """
        Download a file from Azure Blob Storage to a temporary file.
        
        Args:
            blob_name: Name of the blob to download
            container_name: Container name (uses default if None)
            
        Returns:
            str: Path to the temporary file
        """
        try:
            if not self.client and not self._ensure_client():
                raise Exception('Azure Storage client not initialized')
            
            container = container_name or self.container_name
            if not container:
                raise Exception('Container name not configured')
            
            # Resolve blob name (with normalization attempt for duplicated prefixes)
            resolved_name = self.resolve_blob_name(blob_name, container=container)
            if not resolved_name and '/' in blob_name:
                # Soft normalize duplicated 'documents/' prefix
                if blob_name.startswith('documents/documents/'):
                    normalized = blob_name[len('documents/'):]
                    resolved_name = self.resolve_blob_name(normalized, container=container)
            if not resolved_name:
                raise Exception(f'Blob not found: {blob_name}')
            
            if not self.client:
                raise Exception('Azure Storage client not available')
                
            blob_client = self.client.get_blob_client(container=container, blob=resolved_name)
            
            # Create temporary file
            import tempfile
            from pathlib import Path
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(blob_name).suffix)
            temp_path = temp_file.name
            temp_file.close()
            
            # Download the blob
            with open(temp_path, 'wb') as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            
            logger.info(f"File downloaded to tempfile: {resolved_name} -> {temp_path}")
            
            return temp_path
            
        except Exception as e:
            logger.exception(f"Failed to download blob to tempfile {blob_name}")
            raise Exception(f"Failed to download blob to tempfile: {str(e)}")
    
    def get_blob_url(
        self, 
        blob_name: str, 
        container_name: Optional[str] = None,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Get a signed URL for a blob.
        
        Args:
            blob_name: Name of the blob
            container_name: Container name (uses default if None)
            expires_in: URL expiration time in seconds
            
        Returns:
            Dictionary with URL result
        """
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Azure Storage client not initialized'
                }
            
            container = container_name or self.container_name
            if not container:
                return {
                    'success': False,
                    'error': 'Container name not configured'
                }
            
            # Resolve blob name
            resolved_name = self.resolve_blob_name(blob_name, container=container)
            if not resolved_name:
                logger.info(f"Blob not found for URL generation: {blob_name}. "
                           f"Pruebe con categoría 'documents' o verifique el nombre exacto")
                return {
                    'success': False,
                    'error': 'Blob not found',
                    'blob_name': blob_name,
                    'suggestion': 'Pruebe con categoría "documents" o verifique el nombre exacto'
                }
            
            blob_client = self.client.get_blob_client(container=container, blob=resolved_name)
            
            # Generate signed URL using the correct method
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            if not self.account_name or not self.account_key:
                return {
                    'success': False,
                    'error': 'Azure Storage credentials not configured'
                }
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=container,
                blob_name=resolved_name,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expires_in)
            )
            
            # Create signed URL
            signed_url = f"{blob_client.url}?{sas_token}"
            
            logger.info(f"Signed URL generated for blob: {resolved_name}")
            
            return {
                'success': True,
                'original_name': blob_name,
                'resolved_name': resolved_name,
                'signed_url': signed_url,
                'expires_in': expires_in
            }
            
        except Exception as e:
            logger.exception(f"Failed to generate signed URL for blob {blob_name}")
            return {
                'success': False,
                'error': str(e),
                'blob_name': blob_name
            }
    
    def delete_blob(
        self, 
        blob_name: str, 
        container_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a blob from Azure Storage.
        
        Args:
            blob_name: Name of the blob to delete
            container_name: Container name (uses default if None)
            
        Returns:
            Dictionary with delete result
        """
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Azure Storage client not initialized'
                }
            
            container = container_name or self.container_name
            if not container:
                return {
                    'success': False,
                    'error': 'Container name not configured',
                    'blob_name': blob_name
                }
            
            # Resolve blob name
            resolved_name = self.resolve_blob_name(blob_name, container=container)
            if not resolved_name:
                logger.info(f"Blob not found for deletion: {blob_name}. "
                           f"Pruebe con categoría 'documents' o verifique el nombre exacto")
                return {
                    'success': False,
                    'error': 'Blob not found',
                    'blob_name': blob_name,
                    'suggestion': 'Pruebe con categoría "documents" o verifique el nombre exacto'
                }
            
            blob_client = self.client.get_blob_client(container=container, blob=resolved_name)
            
            # Delete the blob
            blob_client.delete_blob()
            
            logger.info(f"Blob deleted successfully: {resolved_name}")
            
            return {
                'success': True,
                'original_name': blob_name,
                'resolved_name': resolved_name,
                'container': container
            }
            
        except Exception as e:
            logger.exception(f"Failed to delete blob {blob_name}")
            return {
                'success': False,
                'error': str(e),
                'blob_name': blob_name
            }
    
    def list_blobs(
        self, 
        container_name: Optional[str] = None,
        name_starts_with: Optional[str] = None,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        List blobs in a container.
        
        Args:
            container_name: Container name (uses default if None)
            name_starts_with: Filter blobs by name prefix
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with list result
        """
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Azure Storage client not initialized'
                }
            
            container = container_name or self.container_name
            if not container:
                return {
                    'success': False,
                    'error': 'Container name not configured'
                }
            container_client = self.client.get_container_client(container)
            
            # List blobs
            blobs = []
            for blob in container_client.list_blobs(
                name_starts_with=name_starts_with
            ):
                blobs.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified.isoformat() if blob.last_modified else None,
                    'content_type': blob.content_settings.content_type if blob.content_settings else None
                })
            
            logger.info(f"Listed {len(blobs)} blobs in container {container}")
            
            return {
                'success': True,
                'container': container,
                'blobs': blobs,
                'count': len(blobs)
            }
            
        except Exception as e:
            logger.exception(f"Failed to list blobs in container {container_name}")
            return {
                'success': False,
                'error': str(e),
                'container': container_name
            }
    
    def blob_exists(
        self, 
        blob_name: str, 
        container_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if a blob exists.
        
        Args:
            blob_name: Name of the blob
            container_name: Container name (uses default if None)
            
        Returns:
            Dictionary with existence check result
        """
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Azure Storage client not initialized'
                }
            
            container = container_name or self.container_name
            if not container:
                return {
                    'success': False,
                    'error': 'Container name not configured'
                }

            # Resolver el nombre real del blob antes de checar existencia
            resolved_name = self.resolve_blob_name(blob_name, container=container)

            if not resolved_name:
                # No se pudo resolver; reportar exists=False con información útil
                return {
                    'success': True,
                    'blob_name': blob_name,
                    'exists': False,
                    'resolved_name': None
                }

            blob_client = self.client.get_blob_client(container=container, blob=resolved_name)
            exists = blob_client.exists()

            return {
                'success': True,
                'blob_name': blob_name,
                'resolved_name': resolved_name,
                'exists': exists
            }
            
        except Exception as e:
            logger.exception(f"Failed to check existence of blob {blob_name}")
            return {
                'success': False,
                'error': str(e),
                'blob_name': blob_name
            }
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get the configuration status of the service."""
        return {
            'connection_string_configured': bool(self.connection_string),
            'account_name_configured': bool(self.account_name),
            'account_key_configured': bool(self.account_key),
            'container_name': self.container_name,
            'client_initialized': bool(self.client)
        }
    
    def _sanitize_metadata_value(self, value: str) -> str:
        """
        Sanitize metadata value for Azure Storage compatibility.
        Azure metadata values can only contain ASCII characters.
        """
        if not value:
            return ''
        
        # Convert to ASCII, replacing non-ASCII characters
        import unicodedata
        ascii_value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
        
        # Remove any remaining invalid characters for Azure metadata
        # Azure metadata can only contain alphanumeric, hyphens, underscores, and periods
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9\-_\.]', '_', ascii_value)
        
        return sanitized


# Global instance for easy access
azure_storage = AzureStorageService()
