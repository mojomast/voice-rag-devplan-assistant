#!/usr/bin/env python3
"""
API Key Setup Script

Interactive script for setting up API keys required for real API testing.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add the tests directory to the path
sys.path.append(str(Path(__file__).parent / "tests"))

try:
    from api_key_manager import APIKeyManager
except ImportError:
    print("❌ Error: Could not import APIKeyManager")
    print("Make sure you're running this from the voice-rag-system directory")
    sys.exit(1)


def print_banner():
    """Print setup banner"""
    print("🔑 API Key Setup for Voice RAG System")
    print("=" * 60)
    print("This script will help you configure API keys for real API testing.")
    print("Your keys will be encrypted and stored securely.")
    print()
    print("📋 Required API Keys:")
    print("  • OpenAI API Key - For GPT models and embeddings")
    print("  • Requesty.ai API Key - For enhanced voice services")
    print("  • ElevenLabs API Key - For advanced text-to-speech (optional)")
    print("  • Azure Speech Key - For Azure speech services (optional)")
    print("  • Google Speech Key - For Google speech services (optional)")
    print("  • AWS Polly Credentials - For AWS text-to-speech (optional)")
    print()


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    missing_deps = []
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import cryptography
    except ImportError:
        missing_deps.append("cryptography")
    
    try:
        import loguru
    except ImportError:
        missing_deps.append("loguru")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  • {dep}")
        print("\n📦 Install missing dependencies:")
        print("  pip install requests cryptography loguru")
        return False
    
    print("✅ All dependencies installed")
    return True


def validate_environment():
    """Validate the environment setup"""
    print("\n🔍 Validating environment...")
    
    # Check if we're in the right directory
    if not Path("voice-rag-system").exists():
        print("⚠️  Warning: voice-rag-system directory not found")
        print("Make sure you're running this from the project root directory")
    
    # Check .env template
    env_template = Path("voice-rag-system/.env.template")
    if env_template.exists():
        print("✅ .env.template found")
    else:
        print("⚠️  .env.template not found")
    
    # Check tests directory
    tests_dir = Path("voice-rag-system/tests")
    if tests_dir.exists():
        print("✅ tests directory found")
    else:
        print("❌ tests directory not found")
        return False
    
    return True


def setup_minimal_keys():
    """Setup only the essential API keys"""
    print("\n🚀 Minimal Setup (Essential Keys Only)")
    print("=" * 50)
    print("This option sets up only the essential API keys needed for basic functionality.")
    print("Essential keys: OpenAI and Requesty.ai")
    print()
    
    manager = APIKeyManager()
    
    # Setup OpenAI key
    print("📋 OpenAI API Key")
    print("   Required for: GPT models, embeddings, basic voice services")
    print("   Get your key at: https://platform.openai.com/api-keys")
    
    openai_configured = False
    if manager.api_configs["openai"].is_configured:
        print("   ✅ Already configured")
        choice = input("   Reconfigure? (y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            openai_configured = True
    
    if not openai_configured:
        try:
            import getpass
            openai_key = getpass.getpass("   Enter OpenAI API key: ").strip()
            if openai_key:
                print("   Validating key...")
                is_valid, message = manager.validate_api_key("openai", openai_key)
                if is_valid:
                    print("   ✅ Key is valid")
                    manager.add_api_key("openai", openai_key, skip_validation=True)
                    openai_configured = True
                else:
                    print(f"   ❌ Key validation failed: {message}")
                    retry = input("   Save anyway? (y/N): ").strip().lower()
                    if retry in ['y', 'yes']:
                        manager.add_api_key("openai", openai_key, skip_validation=True)
                        openai_configured = True
        except KeyboardInterrupt:
            print("\n   ⚠️  Skipped")
    
    # Setup Requesty.ai key
    print("\n📋 Requesty.ai API Key")
    print("   Required for: Enhanced voice services")
    print("   Get your key at: https://requesty.ai")
    
    requesty_configured = False
    if manager.api_configs["requesty"].is_configured:
        print("   ✅ Already configured")
        choice = input("   Reconfigure? (y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            requesty_configured = True
    
    if not requesty_configured:
        try:
            requesty_key = getpass.getpass("   Enter Requesty.ai API key: ").strip()
            if requesty_key:
                print("   Validating key...")
                is_valid, message = manager.validate_api_key("requesty", requesty_key)
                if is_valid:
                    print("   ✅ Key is valid")
                    manager.add_api_key("requesty", requesty_key, skip_validation=True)
                    requesty_configured = True
                else:
                    print(f"   ❌ Key validation failed: {message}")
                    retry = input("   Save anyway? (y/N): ").strip().lower()
                    if retry in ['y', 'yes']:
                        manager.add_api_key("requesty", requesty_key, skip_validation=True)
                        requesty_configured = True
        except KeyboardInterrupt:
            print("\n   ⚠️  Skipped")
    
    return openai_configured and requesty_configured


def setup_all_keys():
    """Setup all available API keys"""
    print("\n🚀 Complete Setup (All API Keys)")
    print("=" * 50)
    print("This option sets up all available API keys for full functionality.")
    print()
    
    manager = APIKeyManager()
    results = manager.setup_interactive()
    
    configured_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    return configured_count >= 2  # At least OpenAI and Requesty.ai


def create_env_file():
    """Create .env file from configured keys"""
    print("\n📝 Creating .env file...")
    
    manager = APIKeyManager()
    env_vars = manager.export_keys_for_env()
    
    if not env_vars:
        print("⚠️  No API keys configured")
        return False
    
    env_file = Path("voice-rag-system/.env")
    
    # Read existing .env file if it exists
    existing_env = {}
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_env[key] = value
        except Exception as e:
            print(f"⚠️  Warning: Could not read existing .env file: {e}")
    
    # Merge with new keys
    existing_env.update(env_vars)
    
    # Write .env file
    try:
        with open(env_file, 'w') as f:
            f.write("# API Keys for Voice RAG System\n")
            f.write("# Generated by setup_api_keys.py\n")
            f.write("# DO NOT commit to version control\n\n")
            
            for key, value in existing_env.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ .env file created at {env_file}")
        
        # Add to .gitignore if not already there
        gitignore_file = Path("voice-rag-system/.gitignore")
        if gitignore_file.exists():
            gitignore_content = gitignore_file.read_text()
            if ".env" not in gitignore_content:
                with open(gitignore_file, 'a') as f:
                    f.write("\n# Environment variables\n.env\n")
                print("✅ Added .env to .gitignore")
        
        return True
    
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def test_configuration():
    """Test the API key configuration"""
    print("\n🧪 Testing Configuration...")
    
    manager = APIKeyManager()
    
    # Test essential keys
    essential_keys = ["openai", "requesty"]
    all_valid = True
    
    for key_name in essential_keys:
        if manager.api_configs[key_name].is_configured:
            key = manager.get_api_key(key_name)
            if key:
                print(f"   Testing {key_name}...")
                is_valid, message = manager.validate_api_key(key_name, key)
                if is_valid:
                    print(f"   ✅ {key_name}: Valid")
                else:
                    print(f"   ❌ {key_name}: {message}")
                    all_valid = False
            else:
                print(f"   ❌ {key_name}: Key not found")
                all_valid = False
        else:
            print(f"   ⚠️  {key_name}: Not configured")
            all_valid = False
    
    return all_valid


def show_summary():
    """Show configuration summary"""
    print("\n📊 Configuration Summary")
    print("=" * 40)
    
    manager = APIKeyManager()
    configs = manager.list_configs()
    
    configured_count = 0
    total_count = len(configs)
    
    for name, config in configs.items():
        if config["is_configured"]:
            configured_count += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} {name}: {config['service']}")
    
    print(f"\nConfigured: {configured_count}/{total_count} API keys")
    
    if configured_count >= 2:
        print("✅ Ready for real API testing!")
    else:
        print("⚠️  Configure at least OpenAI and Requesty.ai keys for basic functionality")


def main():
    """Main setup function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again")
        sys.exit(1)
    
    # Validate environment
    if not validate_environment():
        print("\n❌ Environment validation failed")
        sys.exit(1)
    
    # Ask user what to do
    print("\n🎯 What would you like to do?")
    print("1. Minimal setup (OpenAI + Requesty.ai only)")
    print("2. Complete setup (all API keys)")
    print("3. Test existing configuration")
    print("4. Show configuration summary")
    print("5. Exit")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            success = setup_minimal_keys()
            if success:
                create_env_file()
                test_configuration()
                show_summary()
            else:
                print("\n❌ Minimal setup failed")
        
        elif choice == "2":
            success = setup_all_keys()
            if success:
                create_env_file()
                test_configuration()
                show_summary()
            else:
                print("\n❌ Complete setup failed")
        
        elif choice == "3":
            if test_configuration():
                print("\n✅ All configured keys are valid!")
            else:
                print("\n❌ Some keys are invalid or missing")
        
        elif choice == "4":
            show_summary()
        
        elif choice == "5":
            print("👋 Goodbye!")
        
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()