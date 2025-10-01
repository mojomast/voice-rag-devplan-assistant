#!/usr/bin/env python3
"""
Test script to verify that all critical dependencies are installed and working.
This script tests the imports that were identified as missing for Phase 4 testing and voice functionality.
"""

import sys
import traceback

def test_import(module_name, description=""):
    """Test if a module can be imported successfully."""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - OK {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - FAILED: {e} {description}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name} - WARNING: {e} {description}")
        return False

def main():
    """Test all critical dependencies."""
    print("=" * 60)
    print("DEPENDENCY VERIFICATION TEST")
    print("=" * 60)
    print("Testing imports for Phase 4 testing and voice functionality...\n")
    
    results = []
    
    # Phase 4 Testing Dependencies
    print("🔍 PHASE 4 TESTING DEPENDENCIES:")
    results.append(test_import("langchain_community", "(Required for Phase 4 testing)"))
    
    print("\n🎤 VOICE PROCESSING DEPENDENCIES:")
    # Core voice dependencies
    results.append(test_import("openai", "(OpenAI API client)"))
    results.append(test_import("whisper", "(OpenAI Whisper STT)"))
    
    # Advanced audio processing
    results.append(test_import("librosa", "(Audio analysis and processing)"))
    results.append(test_import("soundfile", "(Audio file processing)"))
    results.append(test_import("noisereduce", "(Noise reduction)"))
    results.append(test_import("scipy", "(Scientific computing - signal processing)"))
    results.append(test_import("mutagen", "(Audio metadata extraction)"))
    
    # Basic voice processing (should already be installed)
    print("\n🔧 BASIC VOICE PROCESSING:")
    results.append(test_import("pyaudio", "(Audio recording)"))
    results.append(test_import("pydub", "(Audio manipulation)"))
    results.append(test_import("pyttsx3", "(Text-to-speech)"))
    
    # Optional dependencies
    print("\n🎯 OPTIONAL DEPENDENCIES:")
    results.append(test_import("openwakeword", "(Wake word detection)"))
    
    # Test speaker identification (optional)
    try:
        from pyannote.audio import Pipeline
        print("✅ pyannote.audio - OK (Speaker identification)")
        results.append(True)
    except ImportError:
        print("⚠️  pyannote.audio - NOT AVAILABLE (Speaker identification - optional)")
        results.append(True)  # Don't fail for optional dependencies
    
    try:
        import torchaudio
        print("✅ torchaudio - OK (Audio processing for speaker ID)")
        results.append(True)
    except ImportError:
        print("⚠️  torchaudio - NOT AVAILABLE (Audio processing for speaker ID - optional)")
        results.append(True)  # Don't fail for optional dependencies
    
    # Test core voice service import
    print("\n🔧 CORE VOICE SERVICE:")
    try:
        from backend.voice_service import VoiceService
        print("✅ backend.voice_service - OK (Voice service module)")
        
        # Test voice service capabilities
        voice_service = VoiceService()
        capabilities = voice_service.get_processing_capabilities()
        
        print(f"   📊 Processing Capabilities:")
        for capability, available in capabilities.items():
            status = "✅" if available else "❌"
            print(f"      {status} {capability}")
        
        results.append(True)
    except ImportError as e:
        print(f"❌ backend.voice_service - FAILED: {e}")
        results.append(False)
    except Exception as e:
        print(f"⚠️  backend.voice_service - WARNING: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 ALL CRITICAL DEPENDENCIES ARE WORKING!")
        print("✅ Phase 4 testing dependencies are available")
        print("✅ Voice functionality dependencies are available")
        print("✅ Ready for Phase 4 testing and voice functionality")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} dependency test(s) failed")
        print("❌ Some critical dependencies are missing")
        print("❌ Phase 4 testing or voice functionality may be affected")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)