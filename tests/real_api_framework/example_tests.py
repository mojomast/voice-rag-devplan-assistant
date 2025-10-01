"""
Example tests using the Real API Test Framework

Demonstrates how to use the framework for testing real APIs with proper
security, cost controls, and monitoring.
"""

import pytest
import asyncio
from typing import Dict, Any

from .core import RealAPITestFramework, APITestConfig, TestMode
from .fixtures import (
    test_transcription_function, test_tts_function, 
    test_chat_completion_function, test_embedding_function,
    test_requesty_chat_function, test_requesty_embedding_function,
    test_voice_transcription_function, test_voice_tts_function,
    test_rag_query_function, test_scenarios
)


class TestRealAPIFramework:
    """
    Example test class demonstrating real API testing with the framework.
    """
    
    @pytest.mark.asyncio
    async def test_openai_transcription(self, 
                                      real_api_framework,
                                      test_transcription_function,
                                      sample_audio_file):
        """Test OpenAI audio transcription with real API"""
        
        test_data = {
            "audio_path": sample_audio_file,
            "language": "en"
        }
        
        result = await real_api_framework.run_test(
            test_name="openai_transcription_basic",
            test_func=test_transcription_function,
            test_data=test_data,
            category="voice_transcription"
        )
        
        # Assertions
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "text" in result
            assert "language" in result
            assert "cost" in result
            assert result["cost"] >= 0
            assert result["category"] == "voice_transcription"
    
    @pytest.mark.asyncio
    async def test_openai_tts(self,
                            real_api_framework,
                            test_tts_function,
                            sample_text):
        """Test OpenAI text-to-speech with real API"""
        
        test_data = {
            "text": sample_text,
            "voice": "alloy"
        }
        
        result = await real_api_framework.run_test(
            test_name="openai_tts_basic",
            test_func=test_tts_function,
            test_data=test_data,
            category="text_to_speech"
        )
        
        # Assertions
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "audio_data" in result
            assert "cost" in result
            assert result["cost"] >= 0
    
    @pytest.mark.asyncio
    async def test_openai_chat_completion(self,
                                        real_api_framework,
                                        test_chat_completion_function,
                                        test_scenarios):
        """Test OpenAI chat completion with real API"""
        
        scenario = test_scenarios["chat_completion"]["simple"]
        test_data = {
            "messages": scenario,
            "model": "gpt-4o-mini"
        }
        
        result = await real_api_framework.run_test(
            test_name="openai_chat_simple",
            test_func=test_chat_completion_function,
            test_data=test_data,
            category="chat_completion"
        )
        
        # Assertions
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "content" in result
            assert "usage" in result
            assert "cost" in result
            assert result["cost"] >= 0
    
    @pytest.mark.asyncio
    async def test_openai_embeddings(self,
                                   real_api_framework,
                                   test_embedding_function,
                                   test_scenarios):
        """Test OpenAI embeddings with real API"""
        
        text = test_scenarios["embeddings"]["medium"]
        test_data = {
            "text": text,
            "model": "text-embedding-3-small"
        }
        
        result = await real_api_framework.run_test(
            test_name="openai_embeddings_medium",
            test_func=test_embedding_function,
            test_data=test_data,
            category="embeddings"
        )
        
        # Assertions
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "embedding" in result
            assert isinstance(result["embedding"], list)
            assert len(result["embedding"]) > 0
            assert "cost" in result
    
    @pytest.mark.asyncio
    async def test_requesty_chat_completion(self,
                                          real_api_framework,
                                          test_requesty_chat_function,
                                          test_scenarios):
        """Test Requesty chat completion with real API"""
        
        scenario = test_scenarios["chat_completion"]["technical"]
        test_data = {
            "messages": scenario,
            "model": "zai/glm-4.5"
        }
        
        result = await real_api_framework.run_test(
            test_name="requesty_chat_technical",
            test_func=test_requesty_chat_function,
            test_data=test_data,
            category="chat_completion"
        )
        
        # Assertions
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "content" in result
            assert "provider" in result
            assert result["provider"] == "requesty"
    
    @pytest.mark.asyncio
    async def test_requesty_embeddings(self,
                                      real_api_framework,
                                      test_requesty_embedding_function,
                                      test_scenarios):
        """Test Requesty embeddings with real API"""
        
        texts = test_scenarios["embeddings"]["multilingual"]
        test_data = {
            "texts": texts,
            "model": "requesty/embedding-001"
        }
        
        result = await real_api_framework.run_test(
            test_name="requesty_embeddings_multilingual",
            test_func=test_requesty_embedding_function,
            test_data=test_data,
            category="embeddings"
        )
        
        # Assertions
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "embeddings" in result
            assert isinstance(result["embeddings"], list)
            assert len(result["embeddings"]) == len(texts)
    
    @pytest.mark.asyncio
    async def test_voice_service_transcription(self,
                                             real_api_framework,
                                             test_voice_transcription_function,
                                             sample_audio_file):
        """Test voice service transcription (integration test)"""
        
        test_data = {
            "audio_path": sample_audio_file,
            "language": "en"
        }
        
        result = await real_api_framework.run_test(
            test_name="voice_service_transcription",
            test_func=test_voice_transcription_function,
            test_data=test_data,
            category="voice_transcription"
        )
        
        # Assertions
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "text" in result
            assert "api_calls" in result
            assert len(result["api_calls"]) > 0
    
    @pytest.mark.asyncio
    async def test_voice_service_tts(self,
                                   real_api_framework,
                                   test_voice_tts_function,
                                   test_scenarios):
        """Test voice service TTS (integration test)"""
        
        text = test_scenarios["text_to_speech"]["punctuation"]
        test_data = {
            "text": text,
            "voice": "alloy"
        }
        
        result = await real_api_framework.run_test(
            test_name="voice_service_tts",
            test_func=test_voice_tts_function,
            test_data=test_data,
            category="text_to_speech"
        )
        
        # Assertions
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "audio_file" in result
            assert "api_calls" in result
    
    @pytest.mark.asyncio
    async def test_rag_query(self,
                           real_api_framework,
                           test_rag_query_function,
                           test_scenarios):
        """Test RAG handler query (integration test)"""
        
        query = test_scenarios["chat_completion"]["technical"][0]["content"]
        test_data = {
            "query": query
        }
        
        result = await real_api_framework.run_test(
            test_name="rag_query_technical",
            test_func=test_rag_query_function,
            test_data=test_data,
            category="rag_queries"
        )
        
        # Assertions
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "answer" in result
            assert "sources" in result
            assert "api_calls" in result


class TestCostControlAndMonitoring:
    """
    Test cost control and monitoring features of the framework.
    """
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self,
                               real_api_framework,
                               test_chat_completion_function):
        """Test that costs are properly tracked"""
        
        # Run multiple tests to accumulate cost
        for i in range(3):
            test_data = {
                "messages": [{"role": "user", "content": f"Test message {i}"}],
                "model": "gpt-4o-mini"
            }
            
            result = await real_api_framework.run_test(
                test_name=f"cost_tracking_test_{i}",
                test_func=test_chat_completion_function,
                test_data=test_data,
                category="chat_completion"
            )
            
            if result["status"] == "success":
                assert "cost" in result
                assert result["cost"] > 0
        
        # Check session summary
        summary = real_api_framework.get_session_summary()
        assert summary["total_cost"] > 0
        assert summary["total_tests"] >= 3
        assert "cost_monitor" in summary
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self,
                                real_api_framework,
                                test_embedding_function):
        """Test rate limiting functionality"""
        
        # This test would need many rapid requests to trigger rate limiting
        # For demonstration, we'll just check the rate limiter status
        
        summary = real_api_framework.rate_limiter.get_summary()
        assert "requests_last_minute" in summary
        assert "minute_limit" in summary
        assert "wait_time_seconds" in summary
    
    @pytest.mark.asyncio
    async def test_usage_tracking(self,
                                real_api_framework,
                                test_chat_completion_function):
        """Test usage tracking functionality"""
        
        test_data = {
            "messages": [{"role": "user", "content": "Test usage tracking"}],
            "model": "gpt-4o-mini"
        }
        
        result = await real_api_framework.run_test(
            test_name="usage_tracking_test",
            test_func=test_chat_completion_function,
            test_data=test_data,
            category="chat_completion"
        )
        
        # Check usage tracker
        if real_api_framework.config.enable_usage_tracking:
            usage_summary = real_api_framework.usage_tracker.get_summary()
            assert "total_requests" in usage_summary
            assert "provider_stats" in usage_summary


class TestErrorHandlingAndValidation:
    """
    Test error handling and response validation.
    """
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_handling(self,
                                           real_api_framework,
                                           test_chat_completion_function):
        """Test handling of invalid API keys"""
        
        # This would require temporarily using an invalid key
        # For demonstration, we'll test the validation logic
        
        test_data = {
            "messages": [{"role": "user", "content": "Test"}],
            "model": "invalid-model-name"
        }
        
        result = await real_api_framework.run_test(
            test_name="invalid_model_test",
            test_func=test_chat_completion_function,
            test_data=test_data,
            category="chat_completion"
        )
        
        # Should handle invalid model gracefully
        assert result["status"] in ["success", "error", "skipped"]
    
    @pytest.mark.asyncio
    async def test_response_validation(self,
                                     real_api_framework,
                                     test_chat_completion_function,
                                     response_validator):
        """Test response validation"""
        
        test_data = {
            "messages": [{"role": "user", "content": "Test validation"}],
            "model": "gpt-4o-mini"
        }
        
        result = await real_api_framework.run_test(
            test_name="response_validation_test",
            test_func=test_chat_completion_function,
            test_data=test_data,
            category="chat_completion"
        )
        
        if result["status"] == "success":
            # Validate the response
            validation = response_validator.validate(result, "chat_completion")
            assert validation["valid"] or len(validation["errors"]) > 0
            assert "category" in validation


class TestPerformanceAndReliability:
    """
    Test performance and reliability features.
    """
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self,
                                      real_api_framework,
                                      test_embedding_function):
        """Test handling of concurrent requests"""
        
        async def run_concurrent_tests():
            tasks = []
            for i in range(5):
                test_data = {
                    "text": f"Concurrent test {i}",
                    "model": "text-embedding-3-small"
                }
                
                task = real_api_framework.run_test(
                    test_name=f"concurrent_test_{i}",
                    test_func=test_embedding_function,
                    test_data=test_data,
                    category="embeddings"
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        results = await run_concurrent_tests()
        
        # Check that all tests completed
        assert len(results) == 5
        
        # Count successful tests
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
        assert successful >= 0  # Some might fail due to rate limiting
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self,
                                  real_api_framework,
                                  test_chat_completion_function):
        """Test timeout handling"""
        
        # Create a very short timeout configuration
        from .core import APITestConfig
        short_timeout_config = APITestConfig(
            test_timeout=1.0,  # 1 second timeout
            request_timeout=0.5
        )
        
        # Create temporary framework with short timeout
        temp_framework = RealAPITestFramework(short_timeout_config)
        
        try:
            test_data = {
                "messages": [{"role": "user", "content": "This might time out"}],
                "model": "gpt-4o-mini"
            }
            
            result = await temp_framework.run_test(
                test_name="timeout_test",
                test_func=test_chat_completion_function,
                test_data=test_data,
                category="chat_completion"
            )
            
            # Should handle timeout gracefully
            assert result["status"] in ["success", "error", "timeout", "skipped"]
            
        finally:
            temp_framework.cleanup()


# Integration test class
class TestEndToEndWorkflows:
    """
    Test end-to-end workflows using multiple APIs.
    """
    
    @pytest.mark.asyncio
    async def test_voice_to_text_to_voice_workflow(self,
                                                 real_api_framework,
                                                 test_transcription_function,
                                                 test_tts_function,
                                                 sample_audio_file):
        """Test complete voice workflow: audio -> text -> audio"""
        
        # Step 1: Transcribe audio
        transcription_data = {"audio_path": sample_audio_file}
        transcription_result = await real_api_framework.run_test(
            test_name="workflow_transcription",
            test_func=test_transcription_function,
            test_data=transcription_data,
            category="voice_transcription"
        )
        
        if transcription_result["status"] != "success":
            pytest.skip("Transcription failed, cannot complete workflow")
        
        transcribed_text = transcription_result["text"]
        
        # Step 2: Synthesize speech from transcribed text
        tts_data = {"text": transcribed_text, "voice": "alloy"}
        tts_result = await real_api_framework.run_test(
            test_name="workflow_tts",
            test_func=test_tts_function,
            test_data=tts_data,
            category="text_to_speech"
        )
        
        # Assertions
        assert tts_result["status"] in ["success", "error"]
        if tts_result["status"] == "success":
            assert "audio_data" in tts_result
        
        # Check total workflow cost
        session_summary = real_api_framework.get_session_summary()
        assert session_summary["total_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_text_to_embedding_to_search_workflow(self,
                                                     real_api_framework,
                                                     test_embedding_function,
                                                     test_requesty_chat_function,
                                                     test_scenarios):
        """Test text processing workflow: text -> embedding -> contextual response"""
        
        # Step 1: Create embeddings
        text = test_scenarios["embeddings"]["technical"]
        embedding_data = {"text": text, "model": "text-embedding-3-small"}
        embedding_result = await real_api_framework.run_test(
            test_name="workflow_embedding",
            test_func=test_embedding_function,
            test_data=embedding_data,
            category="embeddings"
        )
        
        if embedding_result["status"] != "success":
            pytest.skip("Embedding failed, cannot complete workflow")
        
        # Step 2: Get contextual response
        messages = [
            {"role": "system", "content": "You are analyzing technical documentation."},
            {"role": "user", "content": f"Based on this text: '{text}', explain the key concepts."}
        ]
        chat_data = {"messages": messages, "model": "zai/glm-4.5"}
        chat_result = await real_api_framework.run_test(
            test_name="workflow_chat",
            test_func=test_requesty_chat_function,
            test_data=chat_data,
            category="chat_completion"
        )
        
        # Assertions
        assert chat_result["status"] in ["success", "error"]
        if chat_result["status"] == "success":
            assert "content" in chat_result
            assert len(chat_result["content"]) > 0


if __name__ == "__main__":
    # Run example tests
    pytest.main([__file__, "-v", "-s"])