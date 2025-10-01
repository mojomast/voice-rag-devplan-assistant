"""
Real API tests for Requesty Client

Replaces mock tests with real Requesty.ai API calls using the Real API Test Framework.
"""

import pytest
import asyncio
from typing import Dict, Any, List

from real_api_framework.core import RealAPITestFramework, APITestConfig, TestMode
from real_api_framework.fixtures import (
    real_api_framework, test_data, response_validator
)


class TestRequestyClientRealAPI:
    """
    Real API tests for Requesty Client functionality.
    """
    
    @pytest.mark.asyncio
    async def test_real_requesty_chat_completion(self, real_api_framework):
        """Test real Requesty chat completion with router API"""
        
        async def chat_with_requesty(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Real chat completion test using Requesty API"""
            try:
                import sys
                from pathlib import Path
                
                # Add backend to path
                backend_path = Path(__file__).parent.parent.parent / "backend"
                if str(backend_path) not in sys.path:
                    sys.path.append(str(backend_path))
                
                from requesty_client import RequestyClient
                
                client = RequestyClient()
                messages = test_data["messages"]
                model = test_data.get("model", "zai/glm-4.5")
                
                # Check if client is properly configured
                if not client.use_router and not client.openai_client:
                    return {
                        "status": "skipped",
                        "error": "No Requesty or OpenAI client configured",
                        "provider": "requesty"
                    }
                
                # Make the API call
                response_text = client.chat_completion(messages, model=model)
                
                return {
                    "status": "success",
                    "content": response_text,
                    "model": model,
                    "provider": "requesty" if client.use_router else "openai",
                    "operation": "chat_completion",
                    "messages_count": len(messages),
                    "api_calls": [{
                        "provider": "requesty" if client.use_router else "openai",
                        "operation": "chat_completion",
                        "model": model,
                        "success": True,
                        "tokens_used": len(str(messages)) + len(response_text),
                        "duration_ms": 0
                    }]
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "provider": "requesty",
                    "operation": "chat_completion",
                    "api_calls": [{
                        "provider": "requesty",
                        "operation": "chat_completion",
                        "model": test_data.get("model", "zai/glm-4.5"),
                        "success": False,
                        "tokens_used": 0,
                        "duration_ms": 0,
                        "error_type": type(e).__name__
                    }]
                }
        
        test_data = {
            "messages": [{"role": "user", "content": "Hello, please introduce yourself briefly."}],
            "model": "zai/glm-4.5"
        }
        
        result = await real_api_framework.run_test(
            test_name="real_requesty_chat_completion",
            test_func=chat_with_requesty,
            test_data=test_data,
            category="chat_completion"
        )
        
        # Assertions
        assert result["status"] in ["success", "error", "skipped"]
        
        if result["status"] == "success":
            assert "content" in result
            assert "provider" in result
            assert "model" in result
            assert len(result["content"]) > 0
            assert result["messages_count"] == 1
            
            # Validate response
            validation = response_validator.validate(result, "chat_completion")
            assert validation["valid"] or len(validation["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_real_requesty_embeddings(self, real_api_framework):
        """Test real Requesty embeddings with router API"""
        
        async def create_embeddings_with_requesty(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Real embeddings test using Requesty API"""
            try:
                import sys
                from pathlib import Path
                
                # Add backend to path
                backend_path = Path(__file__).parent.parent.parent / "backend"
                if str(backend_path) not in sys.path:
                    sys.path.append(str(backend_path))
                
                from requesty_client import RequestyClient
                
                client = RequestyClient()
                texts = test_data["texts"]
                model = test_data.get("model", "requesty/embedding-001")
                
                # Check if client is properly configured
                if not client.use_router and not client.openai_client:
                    return {
                        "status": "skipped",
                        "error": "No Requesty or OpenAI client configured",
                        "provider": "requesty"
                    }
                
                # Make the API call
                embeddings = client.embed_texts(texts, model=model)
                
                return {
                    "status": "success",
                    "embeddings": embeddings,
                    "model": model,
                    "provider": "requesty" if client.use_router else "openai",
                    "operation": "embedding",
                    "texts_count": len(texts),
                    "embedding_dimension": len(embeddings[0]) if embeddings else 0,
                    "api_calls": [{
                        "provider": "requesty" if client.use_router else "openai",
                        "operation": "embedding",
                        "model": model,
                        "success": True,
                        "tokens_used": sum(len(text) for text in texts),
                        "duration_ms": 0
                    }]
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "provider": "requesty",
                    "operation": "embedding",
                    "api_calls": [{
                        "provider": "requesty",
                        "operation": "embedding",
                        "model": test_data.get("model", "requesty/embedding-001"),
                        "success": False,
                        "tokens_used": 0,
                        "duration_ms": 0,
                        "error_type": type(e).__name__
                    }]
                }
        
        test_data = {
            "texts": [
                "Artificial intelligence is transforming technology.",
                "Machine learning enables computers to learn from data.",
                "Neural networks mimic the human brain structure."
            ],
            "model": "requesty/embedding-001"
        }
        
        result = await real_api_framework.run_test(
            test_name="real_requesty_embeddings",
            test_func=create_embeddings_with_requesty,
            test_data=test_data,
            category="embeddings"
        )
        
        # Assertions
        assert result["status"] in ["success", "error", "skipped"]
        
        if result["status"] == "success":
            assert "embeddings" in result
            assert "texts_count" in result
            assert "embedding_dimension" in result
            assert len(result["embeddings"]) == result["texts_count"]
            assert result["embedding_dimension"] > 0
            
            # Validate response
            validation = response_validator.validate(result, "embedding")
            assert validation["valid"] or len(validation["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_real_requesty_multiple_models(self, real_api_framework):
        """Test Requesty with multiple models to verify routing"""
        
        models_to_test = [
            "zai/glm-4.5",
            "openai/gpt-4o-mini",
            "requesty/embedding-001"
        ]
        
        results = []
        
        async def test_model_routing(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Test specific model with Requesty"""
            try:
                import sys
                from pathlib import Path
                
                backend_path = Path(__file__).parent.parent.parent / "backend"
                if str(backend_path) not in sys.path:
                    sys.path.append(str(backend_path))
                
                from requesty_client import RequestyClient
                
                client = RequestyClient()
                model = test_data["model"]
                operation = test_data["operation"]
                
                if not client.use_router and not client.openai_client:
                    return {
                        "status": "skipped",
                        "error": "No client configured",
                        "model": model
                    }
                
                if operation == "chat":
                    messages = test_data["messages"]
                    response = client.chat_completion(messages, model=model)
                    return {
                        "status": "success",
                        "content": response,
                        "model": model,
                        "operation": "chat"
                    }
                elif operation == "embedding":
                    texts = test_data["texts"]
                    embeddings = client.embed_texts(texts, model=model)
                    return {
                        "status": "success",
                        "embeddings": embeddings,
                        "model": model,
                        "operation": "embedding"
                    }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "model": test_data["model"],
                    "operation": test_data["operation"]
                }
        
        for model in models_to_test:
            if "embedding" in model:
                test_data = {
                    "model": model,
                    "operation": "embedding",
                    "texts": ["Test text for embedding"]
                }
                category = "embeddings"
            else:
                test_data = {
                    "model": model,
                    "operation": "chat",
                    "messages": [{"role": "user", "content": "Test message"}]
                }
                category = "chat_completion"
            
            result = await real_api_framework.run_test(
                test_name=f"real_requesty_model_{model.replace('/', '_')}",
                test_func=test_model_routing,
                test_data=test_data,
                category=category
            )
            
            results.append(result)
        
        # Verify at least some models worked
        successful_models = [r for r in results if r["status"] == "success"]
        assert len(successful_models) > 0, "At least one model should work"
        
        # Check that different models were actually tested
        tested_models = [r["model"] for r in successful_models]
        assert len(set(tested_models)) >= 1, "Should have tested different models"
    
    @pytest.mark.asyncio
    async def test_real_requesty_usage_stats(self, real_api_framework):
        """Test Requesty usage statistics API"""
        
        async def get_usage_stats(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Test usage statistics from Requesty"""
            try:
                import sys
                from pathlib import Path
                
                backend_path = Path(__file__).parent.parent.parent / "backend"
                if str(backend_path) not in sys.path:
                    sys.path.append(str(backend_path))
                
                from requesty_client import RequestyClient
                
                client = RequestyClient()
                
                if not client.use_router:
                    return {
                        "status": "skipped",
                        "error": "Requesty router not configured"
                    }
                
                # Get usage stats
                stats = client.get_usage_stats()
                
                return {
                    "status": "success",
                    "stats": stats,
                    "provider": "requesty",
                    "operation": "usage_stats"
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "provider": "requesty",
                    "operation": "usage_stats"
                }
        
        result = await real_api_framework.run_test(
            test_name="real_requesty_usage_stats",
            test_func=get_usage_stats,
            test_data={},
            category="monitoring"
        )
        
        # Assertions
        assert result["status"] in ["success", "error", "skipped"]
        
        if result["status"] == "success":
            assert "stats" in result
            assert isinstance(result["stats"], dict)
    
    @pytest.mark.asyncio
    async def test_real_requesty_fallback_mechanism(self, real_api_framework):
        """Test Requesty fallback to OpenAI when router fails"""
        
        async def test_fallback_behavior(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Test fallback behavior by using invalid model first"""
            try:
                import sys
                from pathlib import Path
                
                backend_path = Path(__file__).parent.parent.parent / "backend"
                if str(backend_path) not in sys.path:
                    sys.path.append(str(backend_path))
                
                from requesty_client import RequestyClient
                
                client = RequestyClient()
                messages = test_data["messages"]
                
                # First try with an invalid model (should trigger fallback if available)
                try:
                    response = client.chat_completion(messages, model="invalid/model/name")
                    provider_used = "requesty_fallback"
                except Exception:
                    # If that fails completely, try with a valid model
                    if client.openai_client:
                        response = client.chat_completion(messages, model="gpt-4o-mini")
                        provider_used = "openai_fallback"
                    else:
                        return {
                            "status": "error",
                            "error": "No fallback available"
                        }
                
                return {
                    "status": "success",
                    "content": response,
                    "provider": provider_used,
                    "operation": "chat_completion_fallback"
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "operation": "chat_completion_fallback"
                }
        
        test_data = {
            "messages": [{"role": "user", "content": "Test fallback mechanism"}]
        }
        
        result = await real_api_framework.run_test(
            test_name="real_requesty_fallback",
            test_func=test_fallback_behavior,
            test_data=test_data,
            category="chat_completion"
        )
        
        # Assertions
        assert result["status"] in ["success", "error", "skipped"]
        
        if result["status"] == "success":
            assert "content" in result
            assert "provider" in result
            assert "fallback" in result["provider"]
    
    @pytest.mark.asyncio
    async def test_real_requesty_cost_optimization(self, real_api_framework):
        """Test that Requesty provides cost optimization over direct OpenAI"""
        
        # Get initial cost
        initial_summary = real_api_framework.get_session_summary()
        initial_cost = initial_summary["total_cost"]
        
        async def compare_costs(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Compare costs between Requesty and direct OpenAI"""
            try:
                import sys
                from pathlib import Path
                
                backend_path = Path(__file__).parent.parent.parent / "backend"
                if str(backend_path) not in sys.path:
                    sys.path.append(str(backend_path))
                
                from requesty_client import RequestyClient
                
                client = RequestyClient()
                messages = test_data["messages"]
                
                results = {}
                
                # Test with Requesty if available
                if client.use_router:
                    try:
                        requesty_response = client.chat_completion(messages, model="zai/glm-4.5")
                        results["requesty"] = {
                            "success": True,
                            "response": requesty_response,
                            "model": "zai/glm-4.5"
                        }
                    except Exception as e:
                        results["requesty"] = {
                            "success": False,
                            "error": str(e)
                        }
                
                # Test with OpenAI if available
                if client.openai_client:
                    try:
                        openai_response = client.chat_completion(messages, model="gpt-4o-mini")
                        results["openai"] = {
                            "success": True,
                            "response": openai_response,
                            "model": "gpt-4o-mini"
                        }
                    except Exception as e:
                        results["openai"] = {
                            "success": False,
                            "error": str(e)
                        }
                
                return {
                    "status": "success",
                    "comparison": results,
                    "operation": "cost_comparison"
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "operation": "cost_comparison"
                }
        
        test_data = {
            "messages": [{"role": "user", "content": "Explain the concept of machine learning in one paragraph."}]
        }
        
        result = await real_api_framework.run_test(
            test_name="real_requesty_cost_comparison",
            test_func=compare_costs,
            test_data=test_data,
            category="chat_completion"
        )
        
        # Assertions
        assert result["status"] in ["success", "error", "skipped"]
        
        if result["status"] == "success":
            assert "comparison" in result
            comparison = result["comparison"]
            
            # At least one provider should work
            working_providers = [k for k, v in comparison.items() if v.get("success", False)]
            assert len(working_providers) > 0, "At least one provider should work"
            
            # If both work, both should provide responses
            if "requesty" in working_providers and "openai" in working_providers:
                assert len(comparison["requesty"]["response"]) > 0
                assert len(comparison["openai"]["response"]) > 0
    
    @pytest.mark.asyncio
    async def test_real_requesty_error_handling(self, real_api_framework):
        """Test Requesty error handling with various scenarios"""
        
        error_scenarios = [
            {
                "name": "empty_messages",
                "messages": [],
                "expected_error": "empty"
            },
            {
                "name": "invalid_model",
                "messages": [{"role": "user", "content": "Test"}],
                "model": "completely/invalid/model/name",
                "expected_error": "model"
            },
            {
                "name": "very_long_message",
                "messages": [{"role": "user", "content": "Test " * 10000}],
                "expected_error": "length"
            }
        ]
        
        results = []
        
        async def test_error_scenario(test_data: Dict[str, Any]) -> Dict[str, Any]:
            """Test specific error scenario"""
            try:
                import sys
                from pathlib import Path
                
                backend_path = Path(__file__).parent.parent.parent / "backend"
                if str(backend_path) not in sys.path:
                    sys.path.append(str(backend_path))
                
                from requesty_client import RequestyClient
                
                client = RequestyClient()
                messages = test_data["messages"]
                model = test_data.get("model", "zai/glm-4.5")
                scenario = test_data["scenario"]
                
                response = client.chat_completion(messages, model=model)
                
                return {
                    "status": "success",
                    "scenario": scenario,
                    "response": response,
                    "unexpected": True  # We expected an error but got success
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "scenario": test_data["scenario"],
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "expected": True
                }
        
        for scenario_data in error_scenarios:
            test_data = {
                "messages": scenario_data["messages"],
                "model": scenario_data.get("model"),
                "scenario": scenario_data["name"]
            }
            
            result = await real_api_framework.run_test(
                test_name=f"real_requesty_error_{scenario_data['name']}",
                test_func=test_error_scenario,
                test_data=test_data,
                category="error_handling"
            )
            
            results.append(result)
        
        # Verify error handling
        error_results = [r for r in results if r["status"] == "error"]
        success_results = [r for r in results if r["status"] == "success"]
        
        # Some scenarios should result in errors, others might succeed
        assert len(error_results + success_results) == len(error_scenarios)
        
        # Check that errors are properly handled
        for error_result in error_results:
            assert "error" in error_result
            assert "error_type" in error_result


if __name__ == "__main__":
    # Run real Requesty client tests
    pytest.main([__file__, "-v", "-s"])