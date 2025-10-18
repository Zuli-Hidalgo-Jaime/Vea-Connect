"""
Azure Storage Configuration for Django.

This module provides custom storage backends for Azure Blob Storage
with proper fallback mechanisms and configuration management.
"""

import os
from storages.backends.azure_storage import AzureStorage
from django.conf import settings


def get_azure_account_name():
    """Get Azure account name with fallback support."""
    return (
        os.getenv("AZURE_ACCOUNT_NAME") or 
        os.getenv("AZURE_STORAGE_ACCOUNT_NAME") or 
        os.getenv("BLOB_ACCOUNT_NAME")
    )


def get_azure_account_key():
    """Get Azure account key with fallback support."""
    return (
        os.getenv("AZURE_ACCOUNT_KEY") or 
        os.getenv("AZURE_STORAGE_ACCOUNT_KEY") or 
        os.getenv("BLOB_ACCOUNT_KEY")
    )


def get_azure_container():
    """Get Azure container name with fallback support."""
    return (
        os.getenv("AZURE_CONTAINER") or 
        os.getenv("AZURE_STORAGE_CONTAINER_NAME") or 
        os.getenv("BLOB_CONTAINER_NAME") or 
        "documents"
    )


class AzureStaticStorage(AzureStorage):
    """
    Custom Azure Storage backend for static files.
    
    Uses the 'static' container by default and provides
    proper fallback to environment variables.
    """
    account_name = get_azure_account_name()
    account_key = get_azure_account_key()
    container_name = os.getenv("AZURE_STATIC_CONTAINER", "static")
    expiration_secs = None
    overwrite_files = False
    azure_ssl = True


class AzureMediaStorage(AzureStorage):
    """
    Custom Azure Storage backend for media files.
    
    Uses the 'documents' container by default and provides
    proper fallback to environment variables.
    """
    account_name = get_azure_account_name()
    account_key = get_azure_account_key()
    container_name = get_azure_container()
    expiration_secs = 259200  # 72 hours
    overwrite_files = False
    azure_ssl = True


def is_azure_storage_configured():
    """
    Check if Azure Storage is properly configured.
    
    Returns True if all required variables are available.
    """
    account_name = get_azure_account_name()
    account_key = get_azure_account_key()
    container_name = get_azure_container()
    
    return all([account_name, account_key, container_name])


def get_azure_storage_url():
    """
    Get the base URL for Azure Storage.
    
    Returns the URL format for accessing files in Azure Blob Storage.
    """
    account_name = get_azure_account_name()
    container_name = get_azure_container()
    
    if account_name and container_name:
        return f"https://{account_name}.blob.core.windows.net/{container_name}/"
    
    return None

