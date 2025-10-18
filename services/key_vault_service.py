"""
Azure Key Vault Service for secure credential management
"""
import os
import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)

class KeyVaultService:
    """Service for managing secrets in Azure Key Vault"""
    
    def __init__(self):
        self.vault_url = os.environ.get('AZURE_KEYVAULT_RESOURCEENDPOINT')
        self.client = None
        
        if self.vault_url:
            try:
                credential = DefaultAzureCredential()
                self.client = SecretClient(
                    vault_url=self.vault_url,
                    credential=credential
                )
                logger.info("Azure Key Vault client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Key Vault client: {e}")
                self.client = None
        else:
            logger.warning("AZURE_KEYVAULT_RESOURCEENDPOINT not configured, using environment variables")
    
    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Get a secret from Key Vault or fallback to environment variable
        
        Args:
            secret_name: Name of the secret in Key Vault
            fallback_env_var: Environment variable name to use as fallback
            
        Returns:
            Secret value or None if not found
        """
        if self.client:
            try:
                secret = self.client.get_secret(secret_name)
                logger.debug(f"Retrieved secret '{secret_name}' from Key Vault")
                return secret.value
            except Exception as e:
                logger.warning(f"Failed to get secret '{secret_name}' from Key Vault: {e}")
        
        # Fallback to environment variable
        if fallback_env_var:
            value = os.environ.get(fallback_env_var)
            if value:
                logger.debug(f"Using environment variable '{fallback_env_var}' as fallback")
                return value
        
        logger.error(f"Secret '{secret_name}' not found in Key Vault or environment variables")
        return None
    
    def set_secret(self, secret_name: str, value: str) -> bool:
        """
        Set a secret in Key Vault
        
        Args:
            secret_name: Name of the secret
            value: Secret value
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Key Vault client not available")
            return False
        
        try:
            self.client.set_secret(secret_name, value)
            logger.info(f"Secret '{secret_name}' set successfully in Key Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret '{secret_name}' in Key Vault: {e}")
            return False
    
    def delete_secret(self, secret_name: str) -> bool:
        """
        Delete a secret from Key Vault
        
        Args:
            secret_name: Name of the secret to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Key Vault client not available")
            return False
        
        try:
            self.client.begin_delete_secret(secret_name)
            logger.info(f"Secret '{secret_name}' deleted successfully from Key Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret '{secret_name}' from Key Vault: {e}")
            return False

# Global instance
key_vault_service = KeyVaultService()

def get_secret(secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a secret
    
    Args:
        secret_name: Name of the secret in Key Vault
        fallback_env_var: Environment variable name to use as fallback
        
    Returns:
        Secret value or None if not found
    """
    return key_vault_service.get_secret(secret_name, fallback_env_var)
