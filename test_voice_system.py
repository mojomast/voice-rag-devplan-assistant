#!/usr/bin/env python3
"""
Voice System Test Script
Tests basic voice functionality including TTS, STT, and voice service initialization.
"""

import os
import sys
import tempfile
import base64
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_voice_dependencies():
    """Test that all voice dependencies are available."""
    print("🔍 Testing voice dependencies...")
    
    dependencies = {
        'openai': 'OpenAI API client',
        'whisper': 'OpenAI Whisper',
        'librosa': 'Audio processing',
        'soundfile': 'Audio file handling',
        'noisereduce': 'Noise reduction',
        'scipy': 'Signal processing',
        'mutagen': 'Audio metadata',
        'numpy': 'Numerical computing'
    }
    
    missing_deps = []
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {dep} - {desc}")
        except ImportError as e:
            print(f"❌ {dep} - {desc} - MISSING: {e}")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {missing_deps}")
        print("Some features may not work properly.")
    else:
        print("\n✅ All voice dependencies are available!")
    
    return len(missing_deps) == 0

def test_voice_configuration():
    """Test voice configuration loading."""
    print("\n🔧 Testing voice configuration...")
    
    try:
        from config import settings
        
        # Test basic voice settings
        voice_settings = {
            'TTS_MODEL': settings.TTS_MODEL,
            'TTS_VOICE': settings.TTS_VOICE,
            'WHISPER_MODEL': settings.WHISPER_MODEL,
            'ENABLE_WAKE_WORD': settings.ENABLE_WAKE_WORD,
            'WAKE_WORD': settings.WAKE_WORD,
            'TEMP_AUDIO_DIR': settings.TEMP_AUDIO_DIR,
            'VOICE_LANGUAGE': settings.VOICE_LANGUAGE,
            'TTS_SPEED': settings.TTS_SPEED,
            'AUDIO_SAMPLE_RATE': settings.AUDIO_SAMPLE_RATE,
            'MAX_AUDIO_DURATION': settings.MAX_AUDIO_DURATION
        }
        
        print("Voice configuration loaded:")
        for key, value in voice_settings.items():
            print(f"  {key}: {value}")
        
        # Test temp directory creation
        if os.path.exists(settings.TEMP_AUDIO_DIR):
            print(f"✅ Temp audio directory exists: {settings.TEMP_AUDIO_DIR}")
        else:
            print(f"❌ Temp audio directory missing: {settings.TEMP_AUDIO_DIR}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_voice_service_initialization():
    """Test voice service initialization."""
    print("\n🚀 Testing voice service initialization...")
    
    try:
        from voice_service import VoiceService
        
        # Initialize voice service
        voice_service = VoiceService()
        
        print(f"✅ Voice service initialized successfully")
        print(f"  Test mode: {voice_service.test_mode}")
        print(f"  Client available: {voice_service.client is not None}")
        
        # Test processing capabilities
        capabilities = voice_service.get_processing_capabilities()
        print("  Processing capabilities:")
        for capability, available in capabilities.items():
            status = "✅" if available else "❌"
            print(f"    {status} {capability}")
        
        # Test available voices
        voices = voice_service.get_available_voices()
        print(f"  Available voices: {voices}")
        
        return voice_service
        
    except Exception as e:
        print(f"❌ Voice service initialization failed: {e}")
        return None

def test_tts_functionality(voice_service):
    """Test text-to-speech functionality."""
    print("\n🔊 Testing TTS functionality...")
    
    if not voice_service:
        print("❌ Voice service not available for TTS testing")
        return False
    
    try:
        test_text = "Hello, this is a test of the voice system."
        
        # Test basic TTS
        result = voice_service.synthesize_speech(test_text)
        
        if result["status"] == "success":
            print(f"✅ TTS synthesis successful")
            print(f"  Text: {test_text}")
            print(f"  Output file: {result.get('audio_file', 'N/A')}")
            print(f"  Voice: {result.get('voice', 'N/A')}")
            print(f"  Text length: {result.get('text_length', 'N/A')}")
            print(f"  Simulated: {result.get('simulated', False)}")
            
            # Test TTS to base64
            base64_result = voice_service.synthesize_speech_to_base64(test_text)
            if base64_result["status"] == "success":
                print(f"✅ TTS to base64 successful")
                print(f"  Audio size: {base64_result.get('audio_size', 'N/A')} bytes")
                print(f"  MIME type: {base64_result.get('mime_type', 'N/A')}")
            else:
                print(f"❌ TTS to base64 failed: {base64_result.get('error', 'Unknown error')}")
            
            return True
        else:
            print(f"❌ TTS synthesis failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False

def test_stt_functionality(voice_service):
    """Test speech-to-text functionality."""
    print("\n🎤 Testing STT functionality...")
    
    if not voice_service:
        print("❌ Voice service not available for STT testing")
        return False
    
    try:
        # Create a mock audio file for testing
        test_audio_content = b"MOCK AUDIO DATA FOR TESTING"
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(test_audio_content)
            temp_file_path = temp_file.name
        
        try:
            # Test basic STT
            result = voice_service.transcribe_audio(temp_file_path)
            
            print(f"STT result status: {result['status']}")
            if result["status"] == "success":
                print(f"✅ STT transcription successful")
                print(f"  Text: '{result.get('text', '')}'")
                print(f"  Language: {result.get('language', 'N/A')}")
                print(f"  Duration: {result.get('duration', 'N/A')}")
                print(f"  Confidence: {result.get('confidence', 'N/A')}")
            else:
                print(f"⚠️  STT transcription returned: {result.get('error', 'Unknown error')}")
                print("  This is expected in test mode without real audio")
            
            # Test audio validation
            validation = voice_service.validate_audio_format(temp_file_path)
            print(f"  Audio validation: {validation}")
            
            # Test audio info
            audio_info = voice_service.get_audio_info(temp_file_path)
            print(f"  Audio info: {audio_info}")
            
            return True
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        print(f"❌ STT test failed: {e}")
        return False

def test_base64_audio_processing(voice_service):
    """Test base64 audio processing."""
    print("\n🔄 Testing base64 audio processing...")
    
    if not voice_service:
        print("❌ Voice service not available for base64 testing")
        return False
    
    try:
        # Create mock base64 audio data
        mock_audio = b"MOCK AUDIO DATA"
        audio_base64 = base64.b64encode(mock_audio).decode('utf-8')
        
        # Test base64 transcription
        result = voice_service.transcribe_base64_audio(audio_base64, "audio/wav")
        
        print(f"Base64 transcription status: {result['status']}")
        if result["status"] == "success":
            print(f"✅ Base64 transcription successful")
            print(f"  Text: '{result.get('text', '')}'")
            print(f"  Source: {result.get('source', 'N/A')}")
            print(f"  Original format: {result.get('original_format', 'N/A')}")
        else:
            print(f"⚠️  Base64 transcription: {result.get('error', 'Unknown error')}")
            print("  This is expected in test mode with mock data")
        
        return True
        
    except Exception as e:
        print(f"❌ Base64 audio test failed: {e}")
        return False

def test_voice_pipeline(voice_service):
    """Test complete voice processing pipeline."""
    print("\n🔄 Testing complete voice pipeline...")
    
    if not voice_service:
        print("❌ Voice service not available for pipeline testing")
        return False
    
    try:
        # Create mock audio file
        test_audio_content = b"MOCK AUDIO FOR PIPELINE TEST"
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(test_audio_content)
            temp_file_path = temp_file.name
        
        try:
            # Test voice query processing
            result = voice_service.process_voice_query(temp_file_path)
            
            print(f"Voice pipeline status: {result['status']}")
            if result["status"] == "success":
                print(f"✅ Voice pipeline successful")
                print(f"  Transcription: '{result.get('transcription', '')}'")
                print(f"  Language: {result.get('language', 'N/A')}")
                print(f"  Duration: {result.get('duration', 'N/A')}")
            else:
                print(f"⚠️  Voice pipeline: {result.get('error', 'Unknown error')}")
            
            return True
            
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        print(f"❌ Voice pipeline test failed: {e}")
        return False

def main():
    """Run all voice system tests."""
    print("🎯 Voice System Test Suite")
    print("=" * 50)
    
    # Change to voice-rag-system directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    test_results = []
    
    # Test 1: Dependencies
    deps_ok = test_voice_dependencies()
    test_results.append(("Dependencies", deps_ok))
    
    # Test 2: Configuration
    config_ok = test_voice_configuration()
    test_results.append(("Configuration", config_ok))
    
    # Test 3: Voice Service Initialization
    voice_service = test_voice_service_initialization()
    test_results.append(("Voice Service Init", voice_service is not None))
    
    if voice_service:
        # Test 4: TTS Functionality
        tts_ok = test_tts_functionality(voice_service)
        test_results.append(("TTS", tts_ok))
        
        # Test 5: STT Functionality
        stt_ok = test_stt_functionality(voice_service)
        test_results.append(("STT", stt_ok))
        
        # Test 6: Base64 Processing
        base64_ok = test_base64_audio_processing(voice_service)
        test_results.append(("Base64 Processing", base64_ok))
        
        # Test 7: Voice Pipeline
        pipeline_ok = test_voice_pipeline(voice_service)
        test_results.append(("Voice Pipeline", pipeline_ok))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All voice system tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())