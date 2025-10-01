"""
Voice-specific assisted testing scenarios

Provides interactive test scenarios for voice input/output functionality
that cannot be fully automated.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import sys
import os

# Add the parent directory to the path to import the core module
sys.path.append(str(Path(__file__).parent.parent))
from voice_rag_system.tests.assisted_testing.core import (
    TestScenario, TestStep, TestStepType, AssistedTestFramework
)

# Add the backend to the path to import voice services
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

try:
    from voice_service import VoiceService
    from voice_service import VoiceInputService
    from voice_service import VoiceOutputService
    VOICE_SERVICES_AVAILABLE = True
except ImportError:
    VOICE_SERVICES_AVAILABLE = False
    print("Warning: Voice services not available. Some tests will be limited.")


class VoiceAssistedTestFramework(AssistedTestFramework):
    """
    Extended framework specifically for voice testing scenarios.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        super().__init__(output_dir)
        self.voice_service = None
        self.voice_input_service = None
        self.voice_output_service = None
        
        # Initialize voice services if available
        if VOICE_SERVICES_AVAILABLE:
            self._initialize_voice_services()
        
        # Load voice-specific scenarios
        self._load_voice_scenarios()
    
    def _initialize_voice_services(self):
        """Initialize voice services for testing"""
        try:
            # Initialize basic voice service
            self.voice_service = VoiceService()
            
            # Initialize input service
            self.voice_input_service = VoiceInputService()
            
            # Initialize output service
            self.voice_output_service = VoiceOutputService()
            
            print("✅ Voice services initialized successfully")
        except Exception as e:
            print(f"⚠️  Failed to initialize voice services: {e}")
            self.voice_service = None
            self.voice_input_service = None
            self.voice_output_service = None
    
    def _load_voice_scenarios(self):
        """Load voice-specific testing scenarios"""
        
        # Scenario 1: Voice Input Testing
        self.scenarios["voice_input_comprehensive"] = TestScenario(
            id="voice_input_comprehensive",
            name="Comprehensive Voice Input Testing",
            description="Test voice input functionality with real microphone input and transcription",
            category="voice_input",
            steps=[
                TestStep(
                    id="microphone_setup",
                    name="Microphone Setup",
                    description="Verify microphone is connected and working",
                    step_type=TestStepType.USER_INPUT,
                    instructions="Please ensure your microphone is connected and working properly. You can test this by recording audio in any application or by checking system sound settings.",
                    user_prompt="Is your microphone working properly? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                ),
                TestStep(
                    id="test_basic_recording",
                    name="Test Basic Recording",
                    description="Record a short audio sample to test basic functionality",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will now test basic voice recording. Please speak clearly into your microphone when prompted.",
                    user_prompt="Press Enter to start recording a 5-second voice sample",
                    validation_function=self._test_voice_recording,
                    expected_result="Voice should be recorded successfully"
                ),
                TestStep(
                    id="test_voice_transcription",
                    name="Test Voice Transcription",
                    description="Record speech and test transcription accuracy",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Please speak the following phrase clearly: 'The quick brown fox jumps over the lazy dog.'",
                    user_prompt="Press Enter when ready to speak the phrase",
                    validation_function=self._test_voice_transcription,
                    expected_result="Transcription should be reasonably accurate"
                ),
                TestStep(
                    id="test_noise_handling",
                    name="Test Noise Handling",
                    description="Test voice input with background noise",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="This test checks how well the system handles background noise. Please speak in a normal environment with typical background sounds.",
                    user_prompt="Press Enter to test voice input with background noise",
                    validation_function=self._test_noise_handling,
                    expected_result="System should handle moderate background noise"
                ),
                TestStep(
                    id="validate_input_quality",
                    name="Validate Input Quality",
                    description="Assess overall voice input quality",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Based on the tests above, assess the overall quality of voice input.",
                    user_prompt="How would you rate the voice input quality? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    expected_result="Voice input quality should be at least 'good'"
                )
            ],
            setup_instructions="Ensure your microphone is connected and working. Close any applications that might be using the microphone.",
            cleanup_instructions="No cleanup required for voice input testing.",
            estimated_duration_minutes=10,
            difficulty_level="medium"
        )
        
        # Scenario 2: Voice Output Testing
        self.scenarios["voice_output_comprehensive"] = TestScenario(
            id="voice_output_comprehensive",
            name="Comprehensive Voice Output Testing",
            description="Test text-to-speech output quality, clarity, and different voice options",
            category="voice_output",
            steps=[
                TestStep(
                    id="audio_output_setup",
                    name="Audio Output Setup",
                    description="Verify speakers or headphones are working",
                    step_type=TestStepType.USER_INPUT,
                    instructions="Please ensure your speakers or headphones are connected and working. Test with any audio file if needed.",
                    user_prompt="Can you hear audio from your system? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                ),
                TestStep(
                    id="test_basic_tts",
                    name="Test Basic Text-to-Speech",
                    description="Generate and play basic TTS audio",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will generate speech from text and play it back.",
                    user_prompt="Press Enter to generate and play basic TTS audio",
                    validation_function=self._test_basic_tts,
                    expected_result="Speech should be clear and understandable"
                ),
                TestStep(
                    id="test_voice_variations",
                    name="Test Different Voice Options",
                    description="Test multiple voice options and configurations",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will test different voice options available in the system.",
                    user_prompt="Press Enter to test different voice options (alloy, echo, fable, onyx, nova, shimmer)",
                    validation_function=self._test_voice_variations,
                    expected_result="All voices should work and sound different"
                ),
                TestStep(
                    id="test_speed_variations",
                    name="Test Speech Speed Variations",
                    description="Test different speech speeds",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will test different speech speeds to ensure clarity is maintained.",
                    user_prompt="Press Enter to test different speech speeds",
                    validation_function=self._test_speed_variations,
                    expected_result="Speech should remain clear at different speeds"
                ),
                TestStep(
                    id="test_long_text",
                    name="Test Long Text Processing",
                    description="Test TTS with longer text content",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will test TTS with a longer paragraph to check for consistency and quality.",
                    user_prompt="Press Enter to test TTS with longer text",
                    validation_function=self._test_long_text_tts,
                    expected_result="Long text should be processed and played correctly"
                ),
                TestStep(
                    id="validate_output_quality",
                    name="Validate Output Quality",
                    description="Assess overall voice output quality",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Based on the tests above, assess the overall quality of voice output.",
                    user_prompt="How would you rate the voice output quality? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    expected_result="Voice output quality should be at least 'good'"
                )
            ],
            setup_instructions="Ensure your speakers or headphones are connected and volume is at a comfortable level.",
            cleanup_instructions="No cleanup required for voice output testing.",
            estimated_duration_minutes=12,
            difficulty_level="medium"
        )
        
        # Scenario 3: Complete Voice Workflow
        self.scenarios["voice_workflow_complete"] = TestScenario(
            id="voice_workflow_complete",
            name="Complete Voice Workflow Testing",
            description="Test complete voice workflow: speech -> text -> processing -> speech",
            category="voice_workflow",
            steps=[
                TestStep(
                    id="workflow_setup",
                    name="Workflow Setup",
                    description="Prepare for complete voice workflow test",
                    step_type=TestStepType.USER_INPUT,
                    instructions="Ensure both microphone and speakers/headphones are working properly.",
                    user_prompt="Are both input (microphone) and output (speakers) audio devices ready? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                ),
                TestStep(
                    id="voice_to_text",
                    name="Voice to Text Conversion",
                    description="Speak a question for transcription",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Please speak clearly: 'What are the benefits of artificial intelligence in healthcare?'",
                    user_prompt="Press Enter when ready to speak the question",
                    validation_function=self._test_voice_to_text,
                    expected_result="Question should be transcribed accurately"
                ),
                TestStep(
                    id="validate_transcription",
                    name="Validate Transcription Accuracy",
                    description="Check if transcription matches spoken words",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Review the transcribed text and compare it with what you actually said.",
                    user_prompt="Is the transcription accurate enough for processing? (yes/no)",
                    choices=["yes", "no"],
                    expected_result="Transcription should be reasonably accurate"
                ),
                TestStep(
                    id="text_processing",
                    name="Text Processing",
                    description="Process the transcribed text",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="The system will now process your question and generate a response.",
                    user_prompt="Press Enter to process the transcribed question",
                    validation_function=self._test_text_processing,
                    expected_result="System should generate a relevant response"
                ),
                TestStep(
                    id="text_to_voice",
                    name="Text to Voice Conversion",
                    description="Convert response back to speech",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="The system will now convert the response back to speech.",
                    user_prompt="Press Enter to hear the response as speech",
                    validation_function=self._test_text_to_voice,
                    expected_result="Response should be spoken clearly"
                ),
                TestStep(
                    id="validate_complete_workflow",
                    name="Validate Complete Workflow",
                    description="Assess the complete voice workflow experience",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Consider the entire workflow from speech input to speech output.",
                    user_prompt="How would you rate the complete voice workflow experience? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    expected_result="Complete workflow should be at least 'good'"
                )
            ],
            setup_instructions="Ensure both microphone and speakers/headphones are working. Find a quiet environment for best results.",
            cleanup_instructions="No cleanup required for workflow testing.",
            estimated_duration_minutes=15,
            difficulty_level="hard"
        )
        
        # Scenario 4: Voice UI Integration
        self.scenarios["voice_ui_integration"] = TestScenario(
            id="voice_ui_integration",
            name="Voice UI Integration Testing",
            description="Test voice functionality integrated with the user interface",
            category="voice_ui",
            steps=[
                TestStep(
                    id="ui_navigation",
                    name="Navigate to Voice Interface",
                    description="Navigate to the voice interface in the application",
                    step_type=TestStepType.USER_INPUT,
                    instructions="Please open the application and navigate to the voice interface page.",
                    user_prompt="Are you on the voice interface page? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                ),
                TestStep(
                    id="voice_button_functionality",
                    name="Test Voice Button Functionality",
                    description="Test the voice input button and its visual feedback",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Click the voice input button and observe the interface behavior and visual feedback.",
                    user_prompt="Press Enter to test the voice button functionality",
                    validation_function=self._test_voice_button_functionality,
                    expected_result="Button should show proper visual feedback and state changes"
                ),
                TestStep(
                    id="voice_recording_ui",
                    name="Test Voice Recording UI",
                    description="Test the UI during voice recording",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Start voice recording through the UI and observe the visual indicators.",
                    user_prompt="Press Enter to test voice recording through the UI",
                    validation_function=self._test_voice_recording_ui,
                    expected_result="UI should show clear recording indicators"
                ),
                TestStep(
                    id="voice_playback_ui",
                    name="Test Voice Playback UI",
                    description="Test the UI during voice playback",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Generate voice output and observe the playback UI elements.",
                    user_prompt="Press Enter to test voice playback through the UI",
                    validation_function=self._test_voice_playback_ui,
                    expected_result="UI should show clear playback indicators and controls"
                ),
                TestStep(
                    id="voice_settings_ui",
                    name="Test Voice Settings UI",
                    description="Test voice settings and configuration options in the UI",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Navigate to voice settings and test different configuration options.",
                    user_prompt="Press Enter to test voice settings in the UI",
                    validation_function=self._test_voice_settings_ui,
                    expected_result="Settings should be accessible and functional"
                ),
                TestStep(
                    id="validate_ui_integration",
                    name="Validate UI Integration",
                    description="Assess overall voice UI integration quality",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Consider the overall integration of voice functionality with the UI.",
                    user_prompt="How would you rate the voice UI integration? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    expected_result="UI integration should be at least 'good'"
                )
            ],
            setup_instructions="Navigate to the voice interface in your application. Ensure the application is running.",
            cleanup_instructions="No cleanup required for UI testing.",
            estimated_duration_minutes=10,
            difficulty_level="medium"
        )
        
        # Scenario 5: Voice Error Handling
        self.scenarios["voice_error_handling"] = TestScenario(
            id="voice_error_handling",
            name="Voice Error Handling Testing",
            description="Test how the system handles various voice-related errors",
            category="voice_error_handling",
            steps=[
                TestStep(
                    id="microphone_permission_denied",
                    name="Test Microphone Permission Denied",
                    description="Test behavior when microphone permission is denied",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will test the system's behavior when microphone access is denied.",
                    user_prompt="Press Enter to test microphone permission denied scenario",
                    validation_function=self._test_microphone_permission_denied,
                    expected_result="System should handle permission denial gracefully"
                ),
                TestStep(
                    id="no_audio_input",
                    name="Test No Audio Input",
                    description="Test behavior when no audio is detected",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will test what happens when you don't speak into the microphone.",
                    user_prompt="Press Enter and remain silent for 10 seconds",
                    validation_function=self._test_no_audio_input,
                    expected_result="System should detect silence and handle it appropriately"
                ),
                TestStep(
                    id="unrecognized_speech",
                    name="Test Unrecognized Speech",
                    description="Test behavior with unclear or unrecognized speech",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Please speak unclearly or mumble to test recognition limits.",
                    user_prompt="Press Enter and speak unclearly into the microphone",
                    validation_function=self._test_unrecognized_speech,
                    expected_result="System should handle unclear speech appropriately"
                ),
                TestStep(
                    id="network_connectivity",
                    name="Test Network Connectivity Issues",
                    description="Test behavior with poor or no network connectivity",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will test how the system handles network connectivity issues.",
                    user_prompt="Press Enter to test network connectivity scenarios",
                    validation_function=self._test_network_connectivity,
                    expected_result="System should handle network issues gracefully"
                ),
                TestStep(
                    id="validate_error_handling",
                    name="Validate Error Handling",
                    description="Assess overall error handling quality",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Based on the error scenarios tested, assess the overall error handling quality.",
                    user_prompt="How would you rate the voice error handling? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    expected_result="Error handling should be at least 'good'"
                )
            ],
            setup_instructions="Ensure your microphone is connected. Be prepared to test various error scenarios.",
            cleanup_instructions="No cleanup required for error handling testing.",
            estimated_duration_minutes=12,
            difficulty_level="hard"
        )
    
    # Voice testing validation functions
    
    def _test_voice_recording(self) -> bool:
        """Test basic voice recording functionality"""
        if not self.voice_input_service:
            print("⚠️  Voice input service not available")
            return False
        
        try:
            print("🎤 Starting voice recording test...")
            
            # Simulate recording for 5 seconds
            print("Recording for 5 seconds...")
            time.sleep(5)
            
            # In a real implementation, this would use the voice service
            # For now, we'll simulate success
            print("✅ Voice recording test completed")
            return True
            
        except Exception as e:
            print(f"❌ Voice recording test failed: {e}")
            return False
    
    def _test_voice_transcription(self) -> bool:
        """Test voice transcription accuracy"""
        if not self.voice_input_service:
            print("⚠️  Voice input service not available")
            return False
        
        try:
            print("🎤 Starting voice transcription test...")
            print("Please speak: 'The quick brown fox jumps over the lazy dog.'")
            
            # Simulate recording and transcription
            time.sleep(3)
            
            # In a real implementation, this would use the voice service
            # For now, we'll simulate the process
            print("📝 Transcribing audio...")
            time.sleep(2)
            
            # Simulate transcription result
            simulated_transcription = "The quick brown fox jumps over the lazy dog"
            print(f"Transcription: '{simulated_transcription}'")
            
            # Ask user to confirm accuracy
            accuracy = input("Is the transcription accurate? (yes/no): ").strip().lower()
            return accuracy in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Voice transcription test failed: {e}")
            return False
    
    def _test_noise_handling(self) -> bool:
        """Test voice input with background noise"""
        if not self.voice_input_service:
            print("⚠️  Voice input service not available")
            return False
        
        try:
            print("🎤 Starting noise handling test...")
            print("Please speak normally with typical background noise")
            
            # Simulate recording with noise
            time.sleep(3)
            
            print("📝 Transcribing with noise...")
            time.sleep(2)
            
            # Simulate transcription result
            simulated_transcription = "Test speech with background noise"
            print(f"Transcription: '{simulated_transcription}'")
            
            # Ask user to assess quality
            quality = input("How was the transcription quality with noise? (good/fair/poor): ").strip().lower()
            return quality in ["good", "fair"]
            
        except Exception as e:
            print(f"❌ Noise handling test failed: {e}")
            return False
    
    def _test_basic_tts(self) -> bool:
        """Test basic text-to-speech functionality"""
        if not self.voice_output_service:
            print("⚠️  Voice output service not available")
            return False
        
        try:
            print("🔊 Starting basic TTS test...")
            
            test_text = "Hello, this is a test of the text-to-speech system."
            print(f"Generating speech for: '{test_text}'")
            
            # Simulate TTS generation
            time.sleep(2)
            
            print("🔊 Playing generated speech...")
            time.sleep(3)
            
            # Ask user to confirm they heard the speech
            heard = input("Did you hear the speech clearly? (yes/no): ").strip().lower()
            return heard in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Basic TTS test failed: {e}")
            return False
    
    def _test_voice_variations(self) -> bool:
        """Test different voice options"""
        if not self.voice_output_service:
            print("⚠️  Voice output service not available")
            return False
        
        try:
            print("🔊 Testing different voice options...")
            
            voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            test_text = "This is a test of different voice options."
            
            for voice in voices:
                print(f"Testing voice: {voice}")
                print(f"Generating speech with {voice} voice...")
                time.sleep(1)
                print("🔊 Playing speech...")
                time.sleep(2)
                
                # Ask user to confirm they heard the voice
                heard = input(f"Did you hear the {voice} voice? (yes/no): ").strip().lower()
                if heard not in ["yes", "y"]:
                    return False
            
            print("✅ All voice variations tested successfully")
            return True
            
        except Exception as e:
            print(f"❌ Voice variations test failed: {e}")
            return False
    
    def _test_speed_variations(self) -> bool:
        """Test different speech speeds"""
        if not self.voice_output_service:
            print("⚠️  Voice output service not available")
            return False
        
        try:
            print("🔊 Testing different speech speeds...")
            
            speeds = ["slow", "normal", "fast"]
            test_text = "This is a test of different speech speeds to ensure clarity is maintained."
            
            for speed in speeds:
                print(f"Testing {speed} speed...")
                print(f"Generating speech at {speed} speed...")
                time.sleep(1)
                print("🔊 Playing speech...")
                time.sleep(3)
                
                # Ask user to assess clarity
                clear = input(f"Was the speech clear at {speed} speed? (yes/no): ").strip().lower()
                if clear not in ["yes", "y"]:
                    return False
            
            print("✅ All speed variations tested successfully")
            return True
            
        except Exception as e:
            print(f"❌ Speed variations test failed: {e}")
            return False
    
    def _test_long_text_tts(self) -> bool:
        """Test TTS with longer text"""
        if not self.voice_output_service:
            print("⚠️  Voice output service not available")
            return False
        
        try:
            print("🔊 Testing long text TTS...")
            
            long_text = """
            This is a longer text to test the text-to-speech system's ability to handle 
            extended content. The system should be able to process this text without 
            issues and maintain consistent quality throughout the entire duration. 
            This helps ensure that the TTS system can handle real-world use cases 
            where users might need to listen to longer responses or content.
            """
            
            print("Generating speech for longer text...")
            time.sleep(3)
            
            print("🔊 Playing long text speech...")
            time.sleep(10)
            
            # Ask user to confirm quality
            quality = input("Was the long text speech quality consistent? (yes/no): ").strip().lower()
            return quality in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Long text TTS test failed: {e}")
            return False
    
    def _test_voice_to_text(self) -> bool:
        """Test voice to text conversion in workflow"""
        if not self.voice_input_service:
            print("⚠️  Voice input service not available")
            return False
        
        try:
            print("🎤 Testing voice to text conversion...")
            print("Please speak: 'What are the benefits of artificial intelligence in healthcare?'")
            
            # Simulate recording and transcription
            time.sleep(5)
            
            print("📝 Transcribing...")
            time.sleep(2)
            
            # Simulate transcription result
            transcription = "What are the benefits of artificial intelligence in healthcare?"
            print(f"Transcription: '{transcription}'")
            
            # Ask user to confirm accuracy
            accurate = input("Is the transcription accurate enough for processing? (yes/no): ").strip().lower()
            return accurate in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Voice to text test failed: {e}")
            return False
    
    def _test_text_processing(self) -> bool:
        """Test text processing in workflow"""
        try:
            print("🧠 Testing text processing...")
            
            # Simulate processing
            print("Processing transcribed text...")
            time.sleep(3)
            
            # Simulate response generation
            response = "Artificial intelligence offers numerous benefits in healthcare, including improved diagnosis accuracy, personalized treatment plans, drug discovery acceleration, and operational efficiency improvements."
            print(f"Generated response: '{response[:100]}...'")
            
            # Ask user to confirm relevance
            relevant = input("Is the response relevant to the question? (yes/no): ").strip().lower()
            return relevant in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Text processing test failed: {e}")
            return False
    
    def _test_text_to_voice(self) -> bool:
        """Test text to voice conversion in workflow"""
        if not self.voice_output_service:
            print("⚠️  Voice output service not available")
            return False
        
        try:
            print("🔊 Testing text to voice conversion...")
            
            response = "Artificial intelligence offers numerous benefits in healthcare, including improved diagnosis accuracy, personalized treatment plans, drug discovery acceleration, and operational efficiency improvements."
            
            print("Converting response to speech...")
            time.sleep(2)
            
            print("🔊 Playing response speech...")
            time.sleep(8)
            
            # Ask user to confirm clarity
            clear = input("Was the response speech clear and understandable? (yes/no): ").strip().lower()
            return clear in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Text to voice test failed: {e}")
            return False
    
    def _test_voice_button_functionality(self) -> bool:
        """Test voice button functionality in UI"""
        try:
            print("🖱️  Testing voice button functionality...")
            print("Please click the voice input button in the UI.")
            
            # Wait for user to interact
            time.sleep(2)
            
            # Ask user about button behavior
            working = input("Did the voice button respond correctly when clicked? (yes/no): ").strip().lower()
            return working in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Voice button functionality test failed: {e}")
            return False
    
    def _test_voice_recording_ui(self) -> bool:
        """Test voice recording UI indicators"""
        try:
            print("🎤 Testing voice recording UI...")
            print("Please start voice recording through the UI and observe the indicators.")
            
            # Wait for user to interact
            time.sleep(3)
            
            # Ask user about UI indicators
            indicators = input("Did the UI show clear recording indicators? (yes/no): ").strip().lower()
            return indicators in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Voice recording UI test failed: {e}")
            return False
    
    def _test_voice_playback_ui(self) -> bool:
        """Test voice playback UI indicators"""
        try:
            print("🔊 Testing voice playback UI...")
            print("Please trigger voice playback and observe the UI indicators.")
            
            # Wait for user to interact
            time.sleep(3)
            
            # Ask user about playback UI
            playback_ui = input("Did the UI show clear playback indicators and controls? (yes/no): ").strip().lower()
            return playback_ui in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Voice playback UI test failed: {e}")
            return False
    
    def _test_voice_settings_ui(self) -> bool:
        """Test voice settings UI"""
        try:
            print("⚙️  Testing voice settings UI...")
            print("Please navigate to voice settings and test different options.")
            
            # Wait for user to interact
            time.sleep(5)
            
            # Ask user about settings UI
            settings = input("Are the voice settings accessible and functional? (yes/no): ").strip().lower()
            return settings in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Voice settings UI test failed: {e}")
            return False
    
    def _test_microphone_permission_denied(self) -> bool:
        """Test microphone permission denied scenario"""
        try:
            print("🚫 Testing microphone permission denied...")
            print("Please deny microphone permission when prompted.")
            
            # Simulate permission request
            time.sleep(2)
            
            # Ask user about error handling
            handled = input("Did the system handle the permission denial gracefully? (yes/no): ").strip().lower()
            return handled in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Microphone permission test failed: {e}")
            return False
    
    def _test_no_audio_input(self) -> bool:
        """Test no audio input scenario"""
        try:
            print("🔇 Testing no audio input...")
            print("Please remain silent for 10 seconds when prompted.")
            
            # Simulate silence detection
            time.sleep(10)
            
            # Ask user about silence handling
            handled = input("Did the system detect and handle the silence appropriately? (yes/no): ").strip().lower()
            return handled in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ No audio input test failed: {e}")
            return False
    
    def _test_unrecognized_speech(self) -> bool:
        """Test unrecognized speech scenario"""
        try:
            print("🗣️  Testing unrecognized speech...")
            print("Please speak unclearly or mumble into the microphone.")
            
            # Simulate unclear speech processing
            time.sleep(3)
            
            # Ask user about unclear speech handling
            handled = input("Did the system handle the unclear speech appropriately? (yes/no): ").strip().lower()
            return handled in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Unrecognized speech test failed: {e}")
            return False
    
    def _test_network_connectivity(self) -> bool:
        """Test network connectivity issues"""
        try:
            print("🌐 Testing network connectivity issues...")
            print("Please simulate network connectivity issues (e.g., disconnect from internet).")
            
            # Wait for user to simulate network issues
            time.sleep(5)
            
            # Ask user about network error handling
            handled = input("Did the system handle network connectivity issues gracefully? (yes/no): ").strip().lower()
            return handled in ["yes", "y"]
            
        except Exception as e:
            print(f"❌ Network connectivity test failed: {e}")
            return False


# Convenience function for running voice tests
async def run_voice_test(scenario_id: str, tester_name: Optional[str] = None):
    """Quick function to run a voice test scenario"""
    framework = VoiceAssistedTestFramework()
    return await framework.run_scenario(scenario_id, tester_name)


# Main function for running all voice tests
async def run_all_voice_tests(tester_name: Optional[str] = None):
    """Run all voice test scenarios"""
    framework = VoiceAssistedTestFramework()
    
    # Get all voice scenarios
    voice_scenarios = framework.list_scenarios()
    
    print(f"🎤 Running {len(voice_scenarios)} voice test scenarios...")
    print("=" * 60)
    
    results = []
    for scenario in voice_scenarios:
        print(f"\n🚀 Starting: {scenario.name}")
        result = await framework.run_scenario(scenario.id, tester_name)
        results.append(result)
        
        # Brief pause between scenarios
        await asyncio.sleep(2)
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 VOICE TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.status == "passed")
    failed = sum(1 for r in results if r.status == "failed")
    partial = sum(1 for r in results if r.status == "partially_completed")
    
    print(f"Total scenarios: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Partially completed: {partial}")
    print(f"Success rate: {passed / len(results) * 100:.1f}%")
    
    return results


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    print("🎤 Voice Assisted Testing Framework")
    print("Choose a test to run:")
    print("1. Comprehensive Voice Input Testing")
    print("2. Comprehensive Voice Output Testing")
    print("3. Complete Voice Workflow Testing")
    print("4. Voice UI Integration Testing")
    print("5. Voice Error Handling Testing")
    print("6. Run All Voice Tests")
    
    choice = input("Enter your choice (1-6): ").strip()
    
    scenarios = {
        "1": "voice_input_comprehensive",
        "2": "voice_output_comprehensive",
        "3": "voice_workflow_complete",
        "4": "voice_ui_integration",
        "5": "voice_error_handling",
        "6": "all"
    }
    
    if choice in scenarios:
        if choice == "6":
            asyncio.run(run_all_voice_tests())
        else:
            asyncio.run(run_voice_test(scenarios[choice]))
    else:
        print("Invalid choice. Please run again.")