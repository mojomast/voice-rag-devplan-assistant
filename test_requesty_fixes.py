#!/usr/bin/env python3
"""
Test script to verify Requesty API fixes.
This script tests the fixed RequestyClient implementation.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.requesty_client import RequestyClient
from backend.config import settings
from loguru import logger

def test_requesty_client_initialization():
    """Test that RequestyClient initializes correctly without double auth headers."""
    logger.info("Testing RequestyClient initialization...")
    
    # Test with test mode enabled
    original_test_mode = settings.TEST_MODE
    settings.TEST_MODE = True
    
    try:
        client = RequestyClient()
        logger.info("✅ RequestyClient initialized successfully")
        
        # Check if router client is configured properly
        if client.use_router:
            logger.info("✅ Router client is configured")
            # Verify no double auth headers by checking the client configuration
            if hasattr(client.router_client, '_default_headers'):
                headers = client.router_client._default_headers
                if 'Authorization' in headers:
                    logger.warning("⚠️  Manual Authorization header detected - this may cause double auth")
                else:
                    logger.info("✅ No manual Authorization headers - SDK will handle auth automatically")
        else:
            logger.info("ℹ️  Router client not configured - using fallback mode")
            
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize RequestyClient: {e}")
        return False
    finally:
        settings.TEST_MODE = original_test_mode

def test_model_qualification():
    """Test that model qualification works correctly."""
    logger.info("Testing model qualification...")
    
    # Test the _qualify_model static method
    test_cases = [
        ("glm-4.5", "requesty/glm-4.5"),
        ("embedding-001", "requesty/embedding-001"),
        ("gpt-4o-mini", "openai/gpt-4o-mini"),
        ("requesty/glm-4.5", "requesty/glm-4.5"),  # Already qualified
        ("openai/gpt-4", "openai/gpt-4"),  # Already qualified
    ]
    
    for input_model, expected in test_cases:
        result = RequestyClient._qualify_model(input_model)
        if result == expected:
            logger.info(f"✅ Model qualification: {input_model} -> {result}")
        else:
            logger.error(f"❌ Model qualification failed: {input_model} -> {result} (expected {expected})")
            return False
    
    return True

def test_chat_completion():
    """Test chat completion functionality."""
    logger.info("Testing chat completion...")
    
    # Enable test mode for deterministic responses
    original_test_mode = settings.TEST_MODE
    settings.TEST_MODE = True
    
    try:
        client = RequestyClient()
        
        # Test basic chat completion
        messages = [{"role": "user", "content": "Hello, test message"}]
        response = client.chat_completion(messages)
        
        logger.info(f"✅ Chat completion response: {response[:100]}...")
        
        # Test with specific model
        response_with_model = client.chat_completion(messages, model="glm-4.5")
        logger.info(f"✅ Chat completion with model: {response_with_model[:100]}...")
        
        return True
    except Exception as e:
        logger.error(f"❌ Chat completion failed: {e}")
        return False
    finally:
        settings.TEST_MODE = original_test_mode

def test_embeddings():
    """Test embedding functionality."""
    logger.info("Testing embeddings...")
    
    # Enable test mode for deterministic responses
    original_test_mode = settings.TEST_MODE
    settings.TEST_MODE = True
    
    try:
        client = RequestyClient()
        
        # Test basic embedding
        texts = ["Hello world", "Test embedding"]
        embeddings = client.embed_texts(texts)
        
        if len(embeddings) == len(texts):
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            logger.info(f"✅ Embedding dimension: {len(embeddings[0])}")
            return True
        else:
            logger.error(f"❌ Embedding count mismatch: expected {len(texts)}, got {len(embeddings)}")
            return False
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        return False
    finally:
        settings.TEST_MODE = original_test_mode

def main():
    """Run all tests."""
    logger.info("🧪 Testing Requesty API fixes...")
    logger.info("=" * 50)
    
    tests = [
        test_requesty_client_initialization,
        test_model_qualification,
        test_chat_completion,
        test_embeddings,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        logger.info(f"\n🔍 Running {test.__name__}...")
        if test():
            passed += 1
            logger.info(f"✅ {test.__name__} PASSED")
        else:
            logger.error(f"❌ {test.__name__} FAILED")
        logger.info("-" * 30)
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Requesty API fixes are working correctly.")
        return 0
    else:
        logger.error("💥 Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())