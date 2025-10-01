"""
API Key Management System

Provides secure API key configuration, validation, and management for real API testing.
"""

import os
import json
import sys
import getpass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from cryptography.fernet import Fernet
from loguru import logger
import hashlib
import base64


@dataclass
class APIKeyConfig:
    """Configuration for an API key"""
    name: str
    key: str
    service: str
    description: str
    required_for_tests: List[str]
    validation_endpoint: Optional[str] = None
    validation_method: str = "GET"  # GET, POST, etc.
    validation_headers: Optional[Dict[str, str]] = None
    validation_payload: Optional[Dict[str, Any]] = None
    is_configured: bool = False
    last_validated: Optional[str] = None
    validation_status: str = "unknown"  # valid, invalid, unknown, error


class APIKeyManager:
    """
    Manages API keys securely for real API testing.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or "./tests/config")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration files
        self.keys_file = self.config_dir / "api_keys.enc"
        self.config_file = self.config_dir / "api_config.json"
        self.template_file = self.config_dir / ".api_keys.template"
        
        # Encryption key
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # API configurations
        self.api_configs: Dict[str, APIKeyConfig] = {}
        self.encrypted_keys: Dict[str, str] = {}
        
        # Load existing configurations
        self._load_api_configs()
        self._load_encrypted_keys()
        
        logger.info(f"API Key Manager initialized - Config dir: {self.config_dir}")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for storing API keys"""
        key_file = self.config_dir / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def _load_api_configs(self):
        """Load API key configurations"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    configs_data = json.load(f)
                
                for name, config_data in configs_data.items():
                    self.api_configs[name] = APIKeyConfig(**config_data)
                
                logger.info(f"Loaded {len(self.api_configs)} API configurations")
            except Exception as e:
                logger.error(f"Failed to load API configurations: {e}")
        else:
            # Create default configurations
            self._create_default_configs()
    
    def _create_default_configs(self):
        """Create default API key configurations"""
        default_configs = {
            "openai": {
                "name": "openai",
                "service": "OpenAI",
                "description": "OpenAI API key for GPT models and embeddings",
                "required_for_tests": [
                    "test_openai_chat_real",
                    "test_openai_embeddings_real",
                    "test_voice_tts_real",
                    "test_voice_stt_real"
                ],
                "validation_endpoint": "https://api.openai.com/v1/models",
                "validation_method": "GET",
                "validation_headers": {"Authorization": "Bearer {key}"}
            },
            "requesty": {
                "name": "requesty",
                "service": "Requesty.ai",
                "description": "Requesty.ai API key for enhanced voice services",
                "required_for_tests": [
                    "test_requesty_router_real",
                    "test_requesty_embeddings_real",
                    "test_enhanced_voice_real"
                ],
                "validation_endpoint": "https://api.requesty.ai/v1/status",
                "validation_method": "GET",
                "validation_headers": {"Authorization": "Bearer {key}"}
            },
            "elevenlabs": {
                "name": "elevenlabs",
                "service": "ElevenLabs",
                "description": "ElevenLabs API key for advanced text-to-speech",
                "required_for_tests": [
                    "test_elevenlabs_tts_real",
                    "test_voice_cloning_real"
                ],
                "validation_endpoint": "https://api.elevenlabs.io/v1/user",
                "validation_method": "GET",
                "validation_headers": {"xi-api-key": "{key}"}
            },
            "azure_speech": {
                "name": "azure_speech",
                "service": "Azure Speech Services",
                "description": "Azure Speech Services key for speech-to-text and text-to-speech",
                "required_for_tests": [
                    "test_azure_stt_real",
                    "test_azure_tts_real",
                    "test_azure_pronunciation_real"
                ],
                "validation_endpoint": "https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken",
                "validation_method": "POST",
                "validation_headers": {
                    "Ocp-Apim-Subscription-Key": "{key}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                "validation_payload": ""
            },
            "google_speech": {
                "name": "google_speech",
                "service": "Google Cloud Speech",
                "description": "Google Cloud Speech API key for speech services",
                "required_for_tests": [
                    "test_google_stt_real",
                    "test_google_tts_real",
                    "test_google_speech_adaptation_real"
                ],
                "validation_endpoint": "https://speech.googleapis.com/v1/speech/recognize",
                "validation_method": "POST",
                "validation_headers": {"Authorization": "Bearer {key}"}
            },
            "aws_polly": {
                "name": "aws_polly",
                "service": "AWS Polly",
                "description": "AWS Polly credentials for text-to-speech",
                "required_for_tests": [
                    "test_aws_polly_real",
                    "test_aws_neural_voices_real"
                ],
                "validation_endpoint": "https://polly.{region}.amazonaws.com/v1/voices",
                "validation_method": "GET",
                "validation_headers": {}
            }
        }
        
        # Convert to APIKeyConfig objects
        for name, config_data in default_configs.items():
            self.api_configs[name] = APIKeyConfig(**config_data)
        
        # Save configurations
        self._save_api_configs()
        logger.info(f"Created {len(self.api_configs)} default API configurations")
    
    def _save_api_configs(self):
        """Save API key configurations"""
        configs_data = {}
        for name, config in self.api_configs.items():
            configs_data[name] = {
                "name": config.name,
                "service": config.service,
                "description": config.description,
                "required_for_tests": config.required_for_tests,
                "validation_endpoint": config.validation_endpoint,
                "validation_method": config.validation_method,
                "validation_headers": config.validation_headers,
                "validation_payload": config.validation_payload,
                "is_configured": config.is_configured,
                "last_validated": config.last_validated,
                "validation_status": config.validation_status
            }
        
        with open(self.config_file, 'w') as f:
            json.dump(configs_data, f, indent=2)
        
        logger.info("Saved API configurations")
    
    def _load_encrypted_keys(self):
        """Load encrypted API keys"""
        if self.keys_file.exists():
            try:
                with open(self.keys_file, 'rb') as f:
                    encrypted_data = f.read()
                
                if encrypted_data:
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    self.encrypted_keys = json.loads(decrypted_data.decode())
                    
                    # Update configuration status
                    for name in self.encrypted_keys:
                        if name in self.api_configs:
                            self.api_configs[name].is_configured = True
                    
                    logger.info(f"Loaded {len(self.encrypted_keys)} encrypted API keys")
            except Exception as e:
                logger.error(f"Failed to load encrypted keys: {e}")
                self.encrypted_keys = {}
    
    def _save_encrypted_keys(self):
        """Save encrypted API keys"""
        if self.encrypted_keys:
            encrypted_data = self.cipher.encrypt(json.dumps(self.encrypted_keys).encode())
            with open(self.keys_file, 'wb') as f:
                f.write(encrypted_data)
            # Set restrictive permissions
            os.chmod(self.keys_file, 0o600)
            logger.info("Saved encrypted API keys")
    
    def add_api_key(self, name: str, key: str, skip_validation: bool = False) -> bool:
        """Add or update an API key"""
        if name not in self.api_configs:
            logger.error(f"Unknown API configuration: {name}")
            return False
        
        config = self.api_configs[name]
        
        # Validate the key if requested
        if not skip_validation:
            is_valid, error_msg = self.validate_api_key(name, key)
            if not is_valid:
                logger.error(f"API key validation failed for {name}: {error_msg}")
                return False
            config.validation_status = "valid"
            config.last_validated = "now"
        else:
            config.validation_status = "unknown"
        
        # Store the encrypted key
        self.encrypted_keys[name] = key
        config.is_configured = True
        
        # Save to files
        self._save_encrypted_keys()
        self._save_api_configs()
        
        logger.info(f"Added API key for {name}")
        return True
    
    def get_api_key(self, name: str) -> Optional[str]:
        """Get an API key by name"""
        return self.encrypted_keys.get(name)
    
    def remove_api_key(self, name: str) -> bool:
        """Remove an API key"""
        if name in self.encrypted_keys:
            del self.encrypted_keys[name]
            if name in self.api_configs:
                self.api_configs[name].is_configured = False
                self.api_configs[name].validation_status = "unknown"
                self.api_configs[name].last_validated = None
            
            self._save_encrypted_keys()
            self._save_api_configs()
            logger.info(f"Removed API key for {name}")
            return True
        return False
    
    def validate_api_key(self, name: str, key: str) -> Tuple[bool, str]:
        """Validate an API key by making a test request"""
        if name not in self.api_configs:
            return False, f"Unknown API configuration: {name}"
        
        config = self.api_configs[name]
        
        if not config.validation_endpoint:
            return True, "No validation endpoint configured"
        
        try:
            import requests
            
            # Prepare headers
            headers = config.validation_headers.copy() if config.validation_headers else {}
            for key_name, value in headers.items():
                if "{key}" in value:
                    headers[key_name] = value.replace("{key}", key)
            
            # Make validation request
            if config.validation_method.upper() == "GET":
                response = requests.get(config.validation_endpoint, headers=headers, timeout=10)
            elif config.validation_method.upper() == "POST":
                payload = config.validation_payload or {}
                response = requests.post(config.validation_endpoint, headers=headers, json=payload, timeout=10)
            else:
                return False, f"Unsupported validation method: {config.validation_method}"
            
            if response.status_code in [200, 201, 204]:
                return True, "API key is valid"
            else:
                return False, f"API key validation failed: HTTP {response.status_code}"
        
        except requests.exceptions.RequestException as e:
            return False, f"API key validation failed: {str(e)}"
        except Exception as e:
            return False, f"API key validation error: {str(e)}"
    
    def validate_all_keys(self) -> Dict[str, Tuple[bool, str]]:
        """Validate all configured API keys"""
        results = {}
        
        for name, key in self.encrypted_keys.items():
            is_valid, message = self.validate_api_key(name, key)
            results[name] = (is_valid, message)
            
            # Update configuration
            if name in self.api_configs:
                self.api_configs[name].validation_status = "valid" if is_valid else "invalid"
                self.api_configs[name].last_validated = "now"
        
        self._save_api_configs()
        return results
    
    def get_required_keys_for_test(self, test_name: str) -> List[str]:
        """Get API keys required for a specific test"""
        required_keys = []
        
        for name, config in self.api_configs.items():
            if test_name in config.required_for_tests:
                required_keys.append(name)
        
        return required_keys
    
    def check_test_requirements(self, test_name: str) -> Tuple[bool, List[str]]:
        """Check if all required API keys are configured for a test"""
        required_keys = self.get_required_keys_for_test(test_name)
        missing_keys = [key for key in required_keys if not self.api_configs[key].is_configured]
        
        return len(missing_keys) == 0, missing_keys
    
    def list_configs(self) -> Dict[str, Dict[str, Any]]:
        """List all API configurations"""
        result = {}
        
        for name, config in self.api_configs.items():
            result[name] = {
                "service": config.service,
                "description": config.description,
                "is_configured": config.is_configured,
                "validation_status": config.validation_status,
                "last_validated": config.last_validated,
                "required_for_tests": config.required_for_tests
            }
        
        return result
    
    def generate_env_template(self) -> str:
        """Generate .env template file"""
        template_lines = ["# API Keys for Real Testing"]
        template_lines.append("# Generated by API Key Manager")
        template_lines.append("# DO NOT commit actual keys to version control")
        template_lines.append("")
        
        for name, config in self.api_configs.items():
            env_var = name.upper()
            template_lines.append(f"# {config.description}")
            template_lines.append(f"# Required for: {', '.join(config.required_for_tests)}")
            template_lines.append(f"{env_var}_API_KEY=your_{name}_api_key_here")
            template_lines.append("")
        
        return "\n".join(template_lines)
    
    def export_keys_for_env(self) -> Dict[str, str]:
        """Export keys for environment variables"""
        env_vars = {}
        
        for name, key in self.encrypted_keys.items():
            env_var = f"{name.upper()}_API_KEY"
            env_vars[env_var] = key
        
        return env_vars
    
    def setup_interactive(self) -> Dict[str, bool]:
        """Interactive setup for API keys"""
        print("🔑 API Key Setup")
        print("=" * 50)
        print("This wizard will help you configure API keys for real testing.")
        print("Your keys will be encrypted and stored securely.")
        print()
        
        results = {}
        
        for name, config in self.api_configs.items():
            print(f"\n📋 {config.service}")
            print(f"   {config.description}")
            print(f"   Required for: {', '.join(config.required_for_tests)}")
            
            if config.is_configured:
                status = f"✅ Configured ({config.validation_status})"
                if config.validation_status == "valid":
                    print(f"   Status: {status}")
                    choice = input("   Reconfigure? (y/N): ").strip().lower()
                    if choice not in ['y', 'yes']:
                        results[name] = True
                        continue
                else:
                    print(f"   Status: ⚠️  {status}")
                    choice = input("   Reconfigure? (Y/n): ").strip().lower()
                    if choice in ['n', 'no']:
                        results[name] = False
                        continue
            else:
                print("   Status: ❌ Not configured")
                choice = input("   Configure now? (Y/n): ").strip().lower()
                if choice in ['n', 'no']:
                    results[name] = False
                    continue
            
            # Get API key
            try:
                key = getpass.getpass(f"   Enter {config.service} API key: ").strip()
                if not key:
                    print("   ⚠️  No key provided - skipping")
                    results[name] = False
                    continue
                
                # Validate key
                print("   Validating key...")
                is_valid, message = self.validate_api_key(name, key)
                
                if is_valid:
                    print("   ✅ Key is valid")
                    self.add_api_key(name, key, skip_validation=True)  # Already validated
                    results[name] = True
                else:
                    print(f"   ❌ Key validation failed: {message}")
                    retry = input("   Try again? (y/N): ").strip().lower()
                    if retry in ['y', 'yes']:
                        # Retry once
                        key = getpass.getpass(f"   Enter {config.service} API key: ").strip()
                        if key:
                            is_valid, message = self.validate_api_key(name, key)
                            if is_valid:
                                print("   ✅ Key is valid")
                                self.add_api_key(name, key, skip_validation=True)
                                results[name] = True
                            else:
                                print(f"   ❌ Key validation failed: {message}")
                                results[name] = False
                        else:
                            results[name] = False
                    else:
                        # Save anyway but mark as unvalidated
                        save_anyway = input("   Save anyway? (y/N): ").strip().lower()
                        if save_anyway in ['y', 'yes']:
                            self.add_api_key(name, key, skip_validation=True)
                            results[name] = True
                        else:
                            results[name] = False
                
            except KeyboardInterrupt:
                print("\n   ⚠️  Setup interrupted")
                results[name] = False
                break
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[name] = False
        
        print(f"\n📊 Setup Summary")
        print("=" * 30)
        configured = sum(1 for success in results.values() if success)
        total = len(results)
        print(f"Configured: {configured}/{total} API keys")
        
        if configured > 0:
            print(f"\n✅ Setup complete! {configured} API keys configured.")
            print("You can now run real API tests.")
        else:
            print(f"\n⚠️  No API keys configured.")
            print("You won't be able to run real API tests without API keys.")
        
        return results


def main():
    """Command-line interface for API key management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API Key Manager")
    parser.add_argument("--setup", action="store_true", help="Interactive setup")
    parser.add_argument("--list", action="store_true", help="List configurations")
    parser.add_argument("--validate", action="store_true", help="Validate all keys")
    parser.add_argument("--add", help="Add API key")
    parser.add_argument("--remove", help="Remove API key")
    parser.add_argument("--test", help="Check requirements for a test")
    parser.add_argument("--env-template", action="store_true", help="Generate .env template")
    parser.add_argument("--config-dir", help="Configuration directory")
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = APIKeyManager(args.config_dir)
    
    try:
        if args.setup:
            manager.setup_interactive()
        
        elif args.list:
            configs = manager.list_configs()
            print("🔑 API Key Configurations")
            print("=" * 50)
            
            for name, config in configs.items():
                status = "✅ Configured" if config["is_configured"] else "❌ Not configured"
                validation = config["validation_status"]
                print(f"\n{name}:")
                print(f"  Service: {config['service']}")
                print(f"  Description: {config['description']}")
                print(f"  Status: {status} ({validation})")
                print(f"  Required for: {', '.join(config['required_for_tests'])}")
        
        elif args.validate:
            print("🔍 Validating API Keys...")
            results = manager.validate_all_keys()
            
            for name, (is_valid, message) in results.items():
                status = "✅ Valid" if is_valid else "❌ Invalid"
                print(f"{name}: {status} - {message}")
        
        elif args.add:
            key = getpass.getpass(f"Enter API key for {args.add}: ")
            if key:
                success = manager.add_api_key(args.add, key)
                if success:
                    print(f"✅ API key for {args.add} added successfully")
                else:
                    print(f"❌ Failed to add API key for {args.add}")
        
        elif args.remove:
            success = manager.remove_api_key(args.remove)
            if success:
                print(f"✅ API key for {args.remove} removed successfully")
            else:
                print(f"❌ Failed to remove API key for {args.remove}")
        
        elif args.test:
            can_run, missing = manager.check_test_requirements(args.test)
            if can_run:
                print(f"✅ All required API keys are configured for {args.test}")
            else:
                print(f"❌ Missing API keys for {args.test}: {', '.join(missing)}")
        
        elif args.env_template:
            template = manager.generate_env_template()
            print(template)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()