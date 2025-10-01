"""
Security module for Real API Test Framework

Provides secure API key management, credential storage, and validation.
"""

import os
import json
import hashlib
import secrets
from typing import Dict, Optional, List, Any
from pathlib import Path
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from loguru import logger


@dataclass
class APIKeyInfo:
    """Information about an API key"""
    provider: str
    key_id: str
    encrypted_key: str
    created_at: str
    last_used: Optional[str] = None
    usage_count: int = 0
    is_active: bool = True
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []


class SecureCredentialsStore:
    """
    Secure storage for API credentials using encryption.
    """
    
    def __init__(self, store_path: Optional[str] = None):
        self.store_path = Path(store_path or "./tests/real_api_data/credentials")
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Encryption setup
        self._encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self._encryption_key)
        
        # Load existing credentials
        self.credentials_file = self.store_path / "encrypted_credentials.json"
        self.credentials: Dict[str, APIKeyInfo] = {}
        self._load_credentials()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for credential storage"""
        key_file = self.store_path / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Securely store the key
        key_file.write_bytes(key)
        
        # Set appropriate permissions (only owner can read/write)
        try:
            os.chmod(key_file, 0o600)
        except OSError:
            logger.warning("Could not set secure permissions on encryption key file")
        
        logger.info("Generated new encryption key for credential store")
        return key
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a value"""
        return self.cipher_suite.encrypt(value.encode()).decode()
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        return self.cipher_suite.decrypt(encrypted_value.encode()).decode()
    
    def _hash_key_id(self, provider: str, key_suffix: str = "") -> str:
        """Generate a unique ID for an API key"""
        content = f"{provider}:{key_suffix}:{secrets.token_hex(8)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def store_credential(self, 
                       provider: str, 
                       api_key: str, 
                       permissions: Optional[List[str]] = None) -> str:
        """
        Store an API credential securely.
        
        Args:
            provider: API provider name (e.g., 'openai', 'requesty')
            api_key: The API key to store
            permissions: List of permissions for this key
            
        Returns:
            Key ID for the stored credential
        """
        from datetime import datetime
        
        key_id = self._hash_key_id(provider, api_key[:8] if len(api_key) > 8 else api_key)
        
        # Validate the API key format
        if not self._validate_key_format(provider, api_key):
            raise ValueError(f"Invalid API key format for provider: {provider}")
        
        credential_info = APIKeyInfo(
            provider=provider,
            key_id=key_id,
            encrypted_key=self._encrypt_value(api_key),
            created_at=datetime.now().isoformat(),
            permissions=permissions or []
        )
        
        self.credentials[key_id] = credential_info
        self._save_credentials()
        
        logger.info(f"Stored credential for provider: {provider} (ID: {key_id})")
        return key_id
    
    def retrieve_credential(self, key_id: str) -> Optional[str]:
        """
        Retrieve an API credential by ID.
        
        Args:
            key_id: The key ID to retrieve
            
        Returns:
            The API key if found and active, None otherwise
        """
        from datetime import datetime
        
        credential_info = self.credentials.get(key_id)
        if not credential_info:
            return None
        
        if not credential_info.is_active:
            logger.warning(f"Attempted to retrieve inactive credential: {key_id}")
            return None
        
        # Update usage tracking
        credential_info.last_used = datetime.now().isoformat()
        credential_info.usage_count += 1
        self._save_credentials()
        
        return self._decrypt_value(credential_info.encrypted_key)
    
    def get_active_credentials(self, provider: Optional[str] = None) -> List[APIKeyInfo]:
        """Get all active credentials, optionally filtered by provider"""
        credentials = []
        for cred in self.credentials.values():
            if cred.is_active and (provider is None or cred.provider == provider):
                credentials.append(cred)
        return credentials
    
    def deactivate_credential(self, key_id: str) -> bool:
        """Deactivate a credential"""
        if key_id in self.credentials:
            self.credentials[key_id].is_active = False
            self._save_credentials()
            logger.info(f"Deactivated credential: {key_id}")
            return True
        return False
    
    def delete_credential(self, key_id: str) -> bool:
        """Delete a credential completely"""
        if key_id in self.credentials:
            del self.credentials[key_id]
            self._save_credentials()
            logger.info(f"Deleted credential: {key_id}")
            return True
        return False
    
    def _validate_key_format(self, provider: str, api_key: str) -> bool:
        """Validate API key format for different providers"""
        if not api_key or not isinstance(api_key, str):
            return False
        
        api_key = api_key.strip()
        
        if provider.lower() == "openai":
            # OpenAI keys start with 'sk-'
            return api_key.startswith("sk-") and len(api_key) >= 20
        
        elif provider.lower() in ["requesty", "router"]:
            # Requesty keys - less strict format check
            return len(api_key) >= 10 and not api_key.lower() in ["", "none", "null", "placeholder"]
        
        # Generic validation for other providers
        return len(api_key) >= 10
    
    def _load_credentials(self):
        """Load credentials from encrypted storage"""
        if not self.credentials_file.exists():
            return
        
        try:
            with open(self.credentials_file, 'r') as f:
                data = json.load(f)
            
            for key_id, cred_data in data.items():
                self.credentials[key_id] = APIKeyInfo(**cred_data)
            
            logger.info(f"Loaded {len(self.credentials)} credentials from secure store")
            
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            self.credentials = {}
    
    def _save_credentials(self):
        """Save credentials to encrypted storage"""
        try:
            data = {}
            for key_id, cred_info in self.credentials.items():
                data[key_id] = {
                    "provider": cred_info.provider,
                    "key_id": cred_info.key_id,
                    "encrypted_key": cred_info.encrypted_key,
                    "created_at": cred_info.created_at,
                    "last_used": cred_info.last_used,
                    "usage_count": cred_info.usage_count,
                    "is_active": cred_info.is_active,
                    "permissions": cred_info.permissions
                }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set secure permissions
            try:
                os.chmod(self.credentials_file, 0o600)
            except OSError:
                logger.warning("Could not set secure permissions on credentials file")
                
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise
    
    def get_store_summary(self) -> Dict[str, Any]:
        """Get summary of stored credentials"""
        total = len(self.credentials)
        active = len([c for c in self.credentials.values() if c.is_active])
        
        provider_counts = {}
        for cred in self.credentials.values():
            provider_counts[cred.provider] = provider_counts.get(cred.provider, 0) + 1
        
        return {
            "total_credentials": total,
            "active_credentials": active,
            "inactive_credentials": total - active,
            "provider_breakdown": provider_counts,
            "store_path": str(self.store_path)
        }


class APIKeyManager:
    """
    Manages API keys for different providers with validation and rotation support.
    """
    
    def __init__(self, credentials_store: SecureCredentialsStore):
        self.credentials_store = credentials_store
        self.provider_configs = self._load_provider_configs()
        self._load_keys_from_environment()
    
    def _load_provider_configs(self) -> Dict[str, Dict]:
        """Load provider-specific configurations"""
        return {
            "openai": {
                "key_prefix": "sk-",
                "min_length": 20,
                "validation_endpoint": "https://api.openai.com/v1/models",
                "rate_limits": {
                    "gpt-4": {"requests_per_minute": 150, "tokens_per_minute": 40000},
                    "gpt-3.5-turbo": {"requests_per_minute": 3500, "tokens_per_minute": 160000},
                    "whisper": {"requests_per_minute": 50},
                    "tts": {"requests_per_minute": 50}
                }
            },
            "requesty": {
                "key_prefix": "",
                "min_length": 10,
                "validation_endpoint": "https://router.requesty.ai/v1/models",
                "rate_limits": {
                    "default": {"requests_per_minute": 60}
                }
            },
            "router": {
                "key_prefix": "",
                "min_length": 10,
                "validation_endpoint": "https://router.requesty.ai/v1/usage",
                "rate_limits": {
                    "default": {"requests_per_minute": 60}
                }
            }
        }
    
    def _load_keys_from_environment(self):
        """Load API keys from environment variables"""
        env_mappings = {
            "OPENAI_API_KEY": "openai",
            "REQUESTY_API_KEY": "requesty", 
            "ROUTER_API_KEY": "router"
        }
        
        for env_var, provider in env_mappings.items():
            api_key = os.getenv(env_var)
            if api_key and self._is_valid_key(provider, api_key):
                try:
                    self.store_key(provider, api_key, ["environment-loaded"])
                    logger.info(f"Loaded {provider} API key from environment")
                except Exception as e:
                    logger.error(f"Failed to store {provider} key from environment: {e}")
    
    def store_key(self, provider: str, api_key: str, permissions: Optional[List[str]] = None) -> str:
        """Store an API key with validation"""
        if not self._is_valid_key(provider, api_key):
            raise ValueError(f"Invalid API key for provider: {provider}")
        
        return self.credentials_store.store_credential(provider, api_key, permissions)
    
    def get_key(self, provider: str) -> Optional[str]:
        """Get the best available API key for a provider"""
        active_keys = self.credentials_store.get_active_credentials(provider)
        
        if not active_keys:
            return None
        
        # Return the most recently used key
        best_key = max(active_keys, key=lambda k: k.last_used or k.created_at)
        return self.credentials_store.retrieve_credential(best_key.key_id)
    
    def has_valid_key(self, provider: str) -> bool:
        """Check if a valid key exists for the provider"""
        return self.get_key(provider) is not None
    
    def validate_key(self, provider: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate an API key by making a test request to the provider.
        
        Args:
            provider: The provider to validate against
            api_key: Optional API key to validate (uses stored key if not provided)
            
        Returns:
            Validation result with status and details
        """
        if api_key is None:
            api_key = self.get_key(provider)
        
        if not api_key:
            return {
                "valid": False,
                "error": "No API key available",
                "provider": provider
            }
        
        try:
            import aiohttp
            import asyncio
            
            config = self.provider_configs.get(provider.lower())
            if not config:
                return {
                    "valid": False,
                    "error": f"Unknown provider: {provider}",
                    "provider": provider
                }
            
            # Make validation request
            async def _validate():
                headers = {"Authorization": f"Bearer {api_key}"}
                timeout = aiohttp.ClientTimeout(total=10)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(config["validation_endpoint"], headers=headers) as response:
                        if response.status == 200:
                            return {"valid": True, "provider": provider}
                        else:
                            return {
                                "valid": False,
                                "error": f"HTTP {response.status}: {await response.text()}",
                                "provider": provider
                            }
            
            # Run the validation
            return asyncio.run(_validate())
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}",
                "provider": provider
            }
    
    def _is_valid_key(self, provider: str, api_key: str) -> bool:
        """Check if an API key has valid format for the provider"""
        config = self.provider_configs.get(provider.lower())
        if not config:
            return len(api_key) >= 10  # Generic validation
        
        # Check format requirements
        if config.get("key_prefix") and not api_key.startswith(config["key_prefix"]):
            return False
        
        if len(api_key) < config.get("min_length", 10):
            return False
        
        # Check for common placeholder values
        placeholders = ["", "none", "null", "placeholder", "your_key_here", "test-key"]
        if api_key.lower() in placeholders:
            return False
        
        return True
    
    def rotate_key(self, provider: str, new_api_key: str) -> str:
        """
        Rotate API key for a provider by adding new key and deactivating old ones.
        
        Args:
            provider: The provider to rotate key for
            new_api_key: The new API key
            
        Returns:
            Key ID for the new credential
        """
        # Deactivate existing keys for this provider
        existing_keys = self.credentials_store.get_active_credentials(provider)
        for key_info in existing_keys:
            self.credentials_store.deactivate_credential(key_info.key_id)
        
        # Store new key
        new_key_id = self.store_key(provider, new_api_key, ["rotated"])
        
        logger.info(f"Rotated {provider} API key - new ID: {new_key_id}")
        return new_key_id
    
    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get information about a provider's configuration and keys"""
        config = self.provider_configs.get(provider.lower(), {})
        active_keys = self.credentials_store.get_active_credentials(provider)
        
        return {
            "provider": provider,
            "config": config,
            "active_keys": len(active_keys),
            "has_valid_key": len(active_keys) > 0,
            "key_details": [
                {
                    "key_id": key.key_id,
                    "created_at": key.created_at,
                    "last_used": key.last_used,
                    "usage_count": key.usage_count,
                    "permissions": key.permissions
                }
                for key in active_keys
            ]
        }
    
    def get_all_providers_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured providers"""
        status = {}
        for provider in self.provider_configs.keys():
            status[provider] = self.get_provider_info(provider)
        return status
    
    def cleanup_expired_keys(self, days_inactive: int = 30):
        """Clean up keys that haven't been used recently"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_inactive)
        cleaned_count = 0
        
        for key_id, key_info in list(self.credentials_store.credentials.items()):
            if key_info.last_used:
                last_used = datetime.fromisoformat(key_info.last_used)
                if last_used < cutoff_date:
                    self.credentials_store.deactivate_credential(key_id)
                    cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} inactive API keys")
        return cleaned_count