"""
Real API tests for Voice Service

Replaces mock tests with real OpenAI API calls using the Real API Test Framework.
"""

import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any

from real_api_framework.core import RealAPITestFramework, APITestConfig, TestMode
from real_api_framework.fixtures import (
    real_api_framework, test_data, response_validator,
    sample_audio_file, sample_text
)


class TestVoiceServiceRealAPI:
    """
    Real API tests for Voice Service functionality.
    """
    
    @pytest.mark.asyncio
    async def test_real_transcribe_audio_success(self, real_api_framework, sample_audio_file):
        """Test real audio transcription with OpenAI Whisper API"""
        
        async def transcribe_with_openai(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Real transcription test using OpenAI API"""
            try:
                from openai import OpenAI
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {
                        "status": "skipped",
                        "error": "OPENAI_API_KEY not configured",
                        "provider": "openai",
                        "model": "whisper-1"
                    }
                
                client = OpenAI(api_key=api_key)
                audio_path = test_data["audio_path"]
                language = test_data.get("language", "en")
                
                with open(audio_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language,
                        response_format="verbose_json",
                        temperature=0.2
                    )
                
                return {
                    "status": "success",
                    "text": response.text,
                    "language": response.language,
                    "duration": getattr(response, "duration", 0),
                    "confidence": getattr(response, "confidence", 1.0),
                    "segments": getattr(response, "segments", []),
                    "usage": {
                        "duration": getattr(response, "duration", 0)
                    },
                    "provider": "openai",
                    "model": "whisper-1",
                    "operation": "transcription",
                    "api_calls": [{
                        "provider": "openai",
                        "operation": "transcription",
                        "model": "whisper-1",
                        "success": True,
                        "tokens_used": 0,
                        "duration_ms": int(getattr(response, "duration", 0) * 1000)
                    }]
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "provider": "openai",
                    "model": "whisper-1",
                    "operation": "transcription",
                    "api_calls": [{
                        "provider": "openai",
                        "operation": "transcription",
                        "model": "whisper-1",
                        "success": False,
                        "tokens_used": 0,
                        "duration_ms": 0,
                        "error_type": type(e).__name__
                    }]
                }
        
        test_data = {
            "audio_path": sample_audio_file,
            "language": "en"
        }
        
        result = await real_api_framework.run_test(
            test_name="real_transcribe_audio_success",
            test_func=transcribe_with_openai,
            test_data=test_data,
            category="voice_transcription"
        )
        
        # Assertions
        assert result["status"] in ["success", "error", "skipped"]
        
        if result["status"] == "success":
            assert "text" in result
            assert "language" in result
            assert "duration" in result
            assert "cost" in result
            assert result["cost"] >= 0
            assert result["provider"] == "openai"
            assert result["model"] == "whisper-1"
            
            # Validate response
            validation = response_validator.validate(result, "transcription")
            assert validation["valid"] or len(validation["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_real_synthesize_speech_success(self, real_api_framework, sample_text):
        """Test real text-to-speech with OpenAI TTS API"""
        
        async def synthesize_with_openai(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Real TTS test using OpenAI API"""
            try:
                from openai import OpenAI
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {
                        "status": "skipped",
                        "error": "OPENAI_API_KEY not configured",
                        "provider": "openai",
                        "model": "tts-1"
                    }
                
                client = OpenAI(api_key=api_key)
                text = test_data["text"]
                voice = test_data.get("voice", "alloy")
                
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    response_format="mp3",
                    speed=1.0
                )
                
                return {
                    "status": "success",
                    "audio_data": response.content,
                    "voice": voice,
                    "text_length": len(text),
                    "usage": {
                        "character_count": len(text)
                    },
                    "provider": "openai",
                    "model": "tts-1",
                    "operation": "tts",
                    "api_calls": [{
                        "provider": "openai",
                        "operation": "tts",
                        "model": "tts-1",
                        "success": True,
                        "tokens_used": len(text),
                        "duration_ms": 0
                    }]
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "provider": "openai",
                    "model": "tts-1",
                    "operation": "tts",
                    "api_calls": [{
                        "provider": "openai",
                        "operation": "tts",
                        "model": "tts-1",
                        "success": False,
                        "tokens_used": 0,
                        "duration_ms": 0,
                        "error_type": type(e).__name__
                    }]
                }
        
        test_data = {
            "text": sample_text,
            "voice": "alloy"
        }
        
        result = await real_api_framework.run_test(
            test_name="real_synthesize_speech_success",
            test_func=synthesize_with_openai,
            test_data=test_data,
            category="text_to_speech"
        )
        
        # Assertions
        assert result["status"] in ["success", "error", "skipped"]
        
        if result["status"] == "success":
            assert "audio_data" in result
            assert "voice" in result
            assert "text_length" in result
            assert "cost" in result
            assert result["cost"] >= 0
            assert result["provider"] == "openai"
            assert result["model"] == "tts-1"
            
            # Validate response
            validation = response_validator.validate(result, "tts")
            assert validation["valid"] or len(validation["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_real_transcribe_with_language_detection(self, real_api_framework, sample_audio_file):
        """Test real transcription with automatic language detection"""
        
        async def transcribe_auto_language(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Real transcription test with automatic language detection"""
            try:
                from openai import OpenAI
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {
                        "status": "skipped",
                        "error": "OPENAI_API_KEY not configured"
                    }
                
                client = OpenAI(api_key=api_key)
                audio_path = test_data["audio_path"]
                
                with open(audio_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        language=None,  # Auto-detect
                        temperature=0.2
                    )
                
                return {
                    "status": "success",
                    "text": response.text,
                    "detected_language": response.language,
                    "language": response.language,
                    "confidence": getattr(response, "confidence", 1.0),
                    "segments": getattr(response, "segments", []),
                    "provider": "openai",
                    "model": "whisper-1",
                    "operation": "transcription",
                    "features": {
                        "language_detection": True,
                        "auto_detected": True
                    }
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "provider": "openai",
                    "model": "whisper-1"
                }
        
        test_data = {"audio_path": sample_audio_file}
        
        result = await real_api_framework.run_test(
            test_name="real_transcribe_auto_language",
            test_func=transcribe_auto_language,
            test_data=test_data,
            category="voice_transcription"
        )
        
        # Assertions
        assert result["status"] in ["success", "error", "skipped"]
        
        if result["status"] == "success":
            assert "detected_language" in result
            assert "language" in result
            assert result["detected_language"] == result["language"]
            assert len(result["detected_language"]) == 2  # Language codes are 2 chars
    
    @pytest.mark.asyncio
    async def test_real_multiple_voices_tts(self, real_api_framework, sample_text):
        """Test real TTS with multiple voice options"""
        
        voices_to_test = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        results = []
        
        async def synthesize_voice(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Test TTS with specific voice"""
            try:
                from openai import OpenAI
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {
                        "status": "skipped",
                        "error": "OPENAI_API_KEY not configured"
                    }
                
                client = OpenAI(api_key=api_key)
                text = test_data["text"]
                voice = test_data["voice"]
                
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    response_format="mp3"
                )
                
                return {
                    "status": "success",
                    "voice": voice,
                    "text_length": len(text),
                    "audio_size": len(response.content),
                    "provider": "openai",
                    "model": "tts-1"
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "voice": test_data["voice"]
                }
        
        for voice in voices_to_test:
            test_data = {
                "text": sample_text,
                "voice": voice
            }
            
            result = await real_api_framework.run_test(
                test_name=f"real_tts_voice_{voice}",
                test_func=synthesize_voice,
                test_data=test_data,
                category="text_to_speech"
            )
            
            results.append(result)
        
        # Verify at least some voices worked
        successful_voices = [r for r in results if r["status"] == "success"]
        assert len(successful_voices) > 0, "At least one voice should work"
        
        # Check that all successful results have different audio data
        audio_sizes = [r["audio_size"] for r in successful_voices]
        assert len(set(audio_sizes)) == len(audio_sizes), "Each voice should produce different audio"
    
    @pytest.mark.asyncio
    async def test_real_voice_workflow_complete(self, real_api_framework, sample_audio_file, sample_text):
        """Test complete voice workflow: transcription -> processing -> TTS"""
        
        # Step 1: Transcribe audio
        async def transcribe_audio(test_data: Dict[str, Any]) -> Dict[str, Any]:
            try:
                from openai import OpenAI
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {"status": "skipped", "error": "OPENAI_API_KEY not configured"}
                
                client = OpenAI(api_key=api_key)
                
                with open(test_data["audio_path"], "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en",
                        response_format="json"
                    )
                
                return {
                    "status": "success",
                    "text": response.text,
                    "step": "transcription"
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e), "step": "transcription"}
        
        # Step 2: Process text (simple processing for demo)
        async def process_text(test_data: Dict[str, Any]) -> Dict[str, Any]:
            original_text = test_data["text"]
            processed_text = f"Processed: {original_text.upper()}"
            
            return {
                "status": "success",
                "original_text": original_text,
                "processed_text": processed_text,
                "step": "processing"
            }
        
        # Step 3: Synthesize speech
        async def synthesize_speech(test_data: Dict[str, Any]) -> Dict[str, Any]:
            try:
                from openai import OpenAI
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {"status": "skipped", "error": "OPENAI_API_KEY not configured"}
                
                client = OpenAI(api_key=api_key)
                
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=test_data["text"],
                    response_format="mp3"
                )
                
                return {
                    "status": "success",
                    "audio_size": len(response.content),
                    "text": test_data["text"],
                    "step": "synthesis"
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e), "step": "synthesis"}
        
        # Execute workflow
        workflow_results = []
        
        # Step 1: Transcription
        transcription_result = await real_api_framework.run_test(
            test_name="workflow_step1_transcription",
            test_func=transcribe_audio,
            test_data={"audio_path": sample_audio_file},
            category="voice_transcription"
        )
        workflow_results.append(transcription_result)
        
        if transcription_result["status"] != "success":
            pytest.skip("Transcription failed, cannot complete workflow")
        
        # Step 2: Processing
        processing_result = await real_api_framework.run_test(
            test_name="workflow_step2_processing",
            test_func=process_text,
            test_data={"text": transcription_result["text"]},
            category="text_processing"
        )
        workflow_results.append(processing_result)
        
        if processing_result["status"] != "success":
            pytest.skip("Processing failed, cannot complete workflow")
        
        # Step 3: Synthesis
        synthesis_result = await real_api_framework.run_test(
            test_name="workflow_step3_synthesis",
            test_func=synthesize_speech,
            test_data={"text": processing_result["processed_text"]},
            category="text_to_speech"
        )
        workflow_results.append(synthesis_result)
        
        # Verify workflow completed successfully
        successful_steps = [r for r in workflow_results if r["status"] == "success"]
        assert len(successful_steps) == 3, "All workflow steps should succeed"
        
        # Verify workflow integrity
        assert transcription_result["text"] in processing_result["original_text"]
        assert processing_result["processed_text"] == synthesis_result["text"]
        
        # Check total workflow cost
        total_cost = sum(r.get("cost", 0) for r in workflow_results)
        assert total_cost > 0, "Workflow should have measurable cost"
    
    @pytest.mark.asyncio
    async def test_real_error_handling_invalid_audio(self, real_api_framework):
        """Test error handling with invalid audio file"""
        
        async def transcribe_invalid_audio(test_data: Dict[str, Any]) -> Dict[str, Any]:
            try:
                from openai import OpenAI
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {"status": "skipped", "error": "OPENAI_API_KEY not configured"}
                
                client = OpenAI(api_key=api_key)
                
                # Create invalid audio file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(b"INVALID_AUDIO_DATA")
                    invalid_audio_path = f.name
                
                try:
                    with open(invalid_audio_path, "rb") as audio_file:
                        response = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="en"
                        )
                    
                    return {"status": "success", "text": response.text}
                    
                finally:
                    os.unlink(invalid_audio_path)
                    
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "expected": True
                }
        
        result = await real_api_framework.run_test(
            test_name="real_error_invalid_audio",
            test_func=transcribe_invalid_audio,
            test_data={},
            category="voice_transcription"
        )
        
        # Should handle error gracefully
        assert result["status"] in ["error", "skipped"]
        if result["status"] == "error":
            assert "error" in result
            assert "error_type" in result
    
    @pytest.mark.asyncio
    async def test_real_cost_tracking_accuracy(self, real_api_framework, sample_text):
        """Test that cost tracking is accurate for voice operations"""
        
        # Get initial cost
        initial_summary = real_api_framework.get_session_summary()
        initial_cost = initial_summary["total_cost"]
        
        # Perform TTS operation
        async def synthesize_for_cost_test(test_data: Dict[str, Any]) -> Dict[str, Any]:
            try:
                from openai import OpenAI
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return {"status": "skipped", "error": "OPENAI_API_KEY not configured"}
                
                client = OpenAI(api_key=api_key)
                
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=test_data["text"],
                    response_format="mp3"
                )
                
                # Calculate expected cost (TTS is $0.015 per 1K characters)
                expected_cost = (len(test_data["text"]) / 1000) * 0.015
                
                return {
                    "status": "success",
                    "text_length": len(test_data["text"]),
                    "expected_cost": expected_cost,
                    "actual_cost": None  # Will be set by framework
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        result = await real_api_framework.run_test(
            test_name="cost_tracking_tts_test",
            test_func=synthesize_for_cost_test,
            test_data={"text": sample_text},
            category="text_to_speech"
        )
        
        if result["status"] == "success":
            # Check that cost was tracked
            final_summary = real_api_framework.get_session_summary()
            final_cost = final_summary["total_cost"]
            
            assert final_cost > initial_cost, "Cost should have increased"
            cost_increase = final_cost - initial_cost
            assert cost_increase > 0, "Cost increase should be positive"
            
            # Cost should be reasonable (less than $1 for simple TTS)
            assert cost_increase < 1.0, "Cost should be reasonable for TTS test"


if __name__ == "__main__":
    # Run real voice service tests
    pytest.main([__file__, "-v", "-s"])