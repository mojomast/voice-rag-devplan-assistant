#!/usr/bin/env python3
"""
Voice System API Key Setup Script
Helps configure API keys for voice system testing and validates the setup.
"""

import os
import sys
from pathlib import Path

def setup_api_keys():
    """Interactive setup for API keys."""
    print("🔑 Voice RAG System - API Key Setup")
    print("=" * 50)
    
    # Change to voice-rag-system directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    env_file = Path(".env")
    
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"📄 Environment file: {env_file.absolute()}")
    
    if not env_file.exists():
        print("❌ .env file not found. Creating from template...")
        if Path(".env.template").exists():
            import shutil
            shutil.copy(".env.template", ".env")
            print("✅ Created .env from template")
        else:
            print("❌ .env.template not found. Please create .env file manually.")
            return False
    
    # Read current .env file
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    print("\n🔧 Current API Key Configuration:")
    print("-" * 30)
    
    # Check current API keys
    api_keys = {
        "OPENAI_API_KEY": "OpenAI API Key (Required for TTS/STT)",
        "REQUESTY_API_KEY": "Requesty API Key (Optional - cost optimization)",
        "ROUTER_API_KEY": "Router API Key (Optional - Requesty router)"
    }
    
    current_keys = {}
    for key, description in api_keys.items():
        # Extract current value from env content
        for line in env_content.split('\n'):
            if line.startswith(f"{key}="):
                current_value = line.split('=', 1)[1].strip('"')
                current_keys[key] = current_value
                if current_value and "your_" not in current_value and "placeholder" not in current_value.lower():
                    print(f"✅ {description}: {'*' * 8}{current_value[-4:] if len(current_value) > 8 else 'SET'}")
                else:
                    print(f"⚠️  {description}: NOT CONFIGURED")
                break
        else:
            print(f"❌ {description}: NOT FOUND")
            current_keys[key] = ""
    
    print("\n📝 API Key Setup Options:")
    print("1. Configure OpenAI API Key (Required for voice functionality)")
    print("2. Configure Requesty API Key (Optional)")
    print("3. Configure Router API Key (Optional)")
    print("4. Test current configuration")
    print("5. Skip (use test mode)")
    print("6. Exit")
    
    while True:
        try:
            choice = input("\nSelect an option (1-6): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6']:
                break
            print("Invalid choice. Please select 1-6.")
        except KeyboardInterrupt:
            print("\n\nExiting setup...")
            return False
    
    if choice == '1':
        return configure_openai_key(env_file, env_content)
    elif choice == '2':
        return configure_requesty_key(env_file, env_content)
    elif choice == '3':
        return configure_router_key(env_file, env_content)
    elif choice == '4':
        return test_configuration()
    elif choice == '5':
        print("⚠️  Skipping API key configuration - system will run in test mode")
        return True
    elif choice == '6':
        print("👋 Exiting setup...")
        return False

def configure_openai_key(env_file, env_content):
    """Configure OpenAI API key."""
    print("\n🔧 Configure OpenAI API Key")
    print("-" * 30)
    print("Get your API key from: https://platform.openai.com/api-keys")
    print("You'll need an OpenAI account with billing enabled for TTS and STT.")
    
    api_key = input("Enter your OpenAI API key (or press Enter to cancel): ").strip()
    
    if not api_key:
        print("❌ No API key provided. Skipping...")
        return False
    
    # Validate API key format
    if not api_key.startswith('sk-') or len(api_key) < 20:
        print("⚠️  Warning: API key format looks incorrect. OpenAI keys typically start with 'sk-'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return False
    
    # Update .env file
    updated_content = []
    for line in env_content.split('\n'):
        if line.startswith('OPENAI_API_KEY='):
            updated_content.append(f'OPENAI_API_KEY="{api_key}"')
        else:
            updated_content.append(line)
    
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_content))
    
    print("✅ OpenAI API key configured successfully!")
    
    # Test the configuration
    print("\n🧪 Testing OpenAI API connection...")
    return test_openai_connection(api_key)

def configure_requesty_key(env_file, env_content):
    """Configure Requesty API key."""
    print("\n🔧 Configure Requesty API Key")
    print("-" * 30)
    print("Get your API key from: https://requesty.ai")
    print("This is optional and provides cost optimization for API calls.")
    
    api_key = input("Enter your Requesty API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⚠️  No Requesty API key provided. Skipping...")
        return True
    
    # Update .env file
    updated_content = []
    for line in env_content.split('\n'):
        if line.startswith('REQUESTY_API_KEY='):
            updated_content.append(f'REQUESTY_API_KEY="{api_key}"')
        else:
            updated_content.append(line)
    
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_content))
    
    print("✅ Requesty API key configured successfully!")
    return True

def configure_router_key(env_file, env_content):
    """Configure Router API key."""
    print("\n🔧 Configure Router API Key")
    print("-" * 30)
    print("This is optional and used with Requesty for advanced routing.")
    
    api_key = input("Enter your Router API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⚠️  No Router API key provided. Skipping...")
        return True
    
    # Update .env file
    updated_content = []
    for line in env_content.split('\n'):
        if line.startswith('ROUTER_API_KEY='):
            updated_content.append(f'ROUTER_API_KEY="{api_key}"')
        else:
            updated_content.append(line)
    
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_content))
    
    print("✅ Router API key configured successfully!")
    return True

def test_openai_connection(api_key):
    """Test OpenAI API connection."""
    try:
        import openai
        from openai import OpenAI
        
        # Test client initialization
        client = OpenAI(api_key=api_key)
        
        # Test a simple API call (list models)
        print("🔍 Testing API access...")
        models = client.models.list()
        
        print("✅ OpenAI API connection successful!")
        print(f"📊 Found {len(list(models))} available models")
        
        # Check for voice-specific models
        model_names = [model.id for model in models]
        voice_models = [name for name in model_names if 'tts' in name or 'whisper' in name]
        
        if voice_models:
            print(f"🎤 Voice models available: {', '.join(voice_models)}")
        else:
            print("⚠️  No voice models found (this might be expected)")
        
        return True
        
    except ImportError:
        print("❌ OpenAI package not installed. Run: pip install openai")
        return False
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        print("Please check your API key and account status.")
        return False

def test_configuration():
    """Test current configuration."""
    print("\n🧪 Testing Voice System Configuration")
    print("=" * 40)
    
    # Add backend to path
    sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
    
    try:
        from config import settings
        from voice_service import VoiceService
        
        print("✅ Configuration loaded successfully")
        print(f"📁 Temp audio dir: {settings.TEMP_AUDIO_DIR}")
        print(f"🎤 TTS Model: {settings.TTS_MODEL}")
        print(f"🔊 TTS Voice: {settings.TTS_VOICE}")
        print(f"👂 Whisper Model: {settings.WHISPER_MODEL}")
        print(f"🔧 Test Mode: {settings.TEST_MODE}")
        print(f"🔑 OpenAI Key Configured: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
        
        # Test voice service initialization
        print("\n🚀 Initializing Voice Service...")
        voice_service = VoiceService()
        
        print(f"✅ Voice Service initialized ({'test' if voice_service.test_mode else 'production'} mode)")
        
        # Test capabilities
        capabilities = voice_service.get_processing_capabilities()
        print("\n📊 Processing Capabilities:")
        for capability, available in capabilities.items():
            status = "✅" if available else "❌"
            print(f"  {status} {capability}")
        
        # Run basic tests
        if not voice_service.test_mode:
            print("\n🎯 Running basic voice tests...")
            
            # Test TTS
            tts_result = voice_service.synthesize_speech("Hello, this is a test.")
            if tts_result["status"] == "success":
                print(f"✅ TTS test passed: {tts_result['audio_file']}")
            else:
                print(f"❌ TTS test failed: {tts_result.get('error', 'Unknown error')}")
        else:
            print("\n⚠️  Running in test mode - no API calls will be made")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🎯 Voice RAG System - Setup Assistant")
    print("This script will help you configure API keys for voice functionality.")
    print()
    
    success = setup_api_keys()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Run: python test_voice_system.py")
        print("2. Start the backend: python -m backend.main")
        print("3. Test voice functionality through the web interface")
    else:
        print("\n❌ Setup was not completed.")
        print("You can run this script again anytime: python setup_voice_keys.py")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())