# Real API Test Framework

A comprehensive testing framework for the Voice-RAG-System that enables real API testing with proper security, cost controls, and monitoring.

## Overview

This framework replaces mock tests with real API calls while providing:
- **Secure API key management** with encryption
- **Cost tracking and controls** to prevent unexpected charges
- **Rate limiting** to respect API provider limits
- **Comprehensive monitoring** and reporting
- **Error handling** with retry logic
- **Response validation** for API calls
- **Assisted testing** for non-automatable components

## Features

### 🔐 Security
- Encrypted credential storage
- API key validation and rotation
- Environment variable integration
- Secure key lifecycle management

### 💰 Cost Control
- Real-time cost tracking
- Per-test and session cost limits
- Cost warnings and alerts
- Provider-specific pricing models

### 📊 Monitoring
- Usage statistics and analytics
- Performance metrics
- Error tracking and reporting
- Detailed session reports

### 🚀 Performance
- Rate limiting with exponential backoff
- Concurrent request handling
- Timeout management
- Retry logic for transient failures

### 🧪 Testing
- Comprehensive test fixtures
- Response validation
- Test data generation
- End-to-end workflow testing

## Installation

```bash
# Install framework dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Quick Start

### Basic Usage

```python
import asyncio
from real_api_framework import RealAPITestFramework, APITestConfig, TestMode

async def run_real_api_tests():
    # Configure framework
    config = APITestConfig(
        mode=TestMode.REAL_API,
        max_cost_per_test=0.5,
        max_cost_per_session=5.0,
        require_api_keys=True
    )
    
    # Initialize framework
    framework = RealAPITestFramework(config)
    
    try:
        # Define test function
        async def test_openai_chat(test_data):
            # Your real API test logic here
            return {"status": "success", "content": "Hello!"}
        
        # Run test with monitoring
        result = await framework.run_test(
            test_name="openai_chat_test",
            test_func=test_openai_chat,
            test_data={"messages": [{"role": "user", "content": "Hello"}]},
            category="chat_completion"
        )
        
        print(f"Test result: {result}")
        
        # Get session summary
        summary = framework.get_session_summary()
        print(f"Session cost: ${summary['total_cost']:.4f}")
        
    finally:
        framework.cleanup()

# Run tests
asyncio.run(run_real_api_tests())
```

### Using Pytest Fixtures

```python
import pytest
from real_api_framework.fixtures import *

@pytest.mark.asyncio
async def test_openai_transcription(real_api_framework, test_transcription_function, sample_audio_file):
    """Test OpenAI transcription with real API"""
    
    test_data = {"audio_path": sample_audio_file, "language": "en"}
    
    result = await real_api_framework.run_test(
        test_name="transcription_test",
        test_func=test_transcription_function,
        test_data=test_data,
        category="voice_transcription"
    )
    
    assert result["status"] == "success"
    assert "text" in result
    assert result["cost"] > 0
```

## Configuration

### Environment Variables

```bash
# Required API Keys
OPENAI_API_KEY=sk-your-openai-key-here
REQUESTY_API_KEY=your-requesty-key-here
ROUTER_API_KEY=your-router-key-here

# Optional Configuration
TEST_MODE=false
DEBUG=true
LOG_LEVEL=INFO

# Cost Controls
MAX_COST_PER_TEST=0.5
MAX_COST_PER_SESSION=5.0
COST_WARNING_THRESHOLD=0.8

# Rate Limits
REQUESTS_PER_MINUTE=60
REQUESTS_PER_HOUR=1000
```

### Framework Configuration

```python
from real_api_framework import APITestConfig, TestMode

config = APITestConfig(
    # Test mode
    mode=TestMode.REAL_API,
    
    # Cost controls
    max_cost_per_test=0.5,        # $0.50 per test max
    max_cost_per_session=5.0,     # $5.00 per session max
    cost_warning_threshold=0.8,   # Warn at 80% of limit
    
    # Rate limits
    requests_per_minute=60,
    requests_per_hour=1000,
    retry_attempts=3,
    retry_delay=1.0,
    
    # Timeouts
    request_timeout=30.0,         # 30 seconds per request
    test_timeout=300.0,           # 5 minutes per test
    
    # Security
    require_api_keys=True,
    validate_keys=True,
    encrypt_credentials=True,
    
    # Monitoring
    enable_cost_tracking=True,
    enable_usage_tracking=True,
    enable_rate_limiting=True,
    
    # Enabled providers and categories
    enabled_providers=["openai", "requesty"],
    enabled_categories=[
        "voice_transcription", "text_to_speech", 
        "chat_completion", "embeddings", "planning", "rag_queries"
    ]
)
```

## API Providers

### OpenAI
- **Models**: gpt-4o-mini, gpt-4, gpt-3.5-turbo, whisper-1, tts-1
- **Operations**: Chat completion, transcription, TTS, embeddings
- **Rate Limits**: Varies by model
- **Cost**: Per-token and per-minute pricing

### Requesty.ai
- **Models**: zai/glm-4.5, requesty/embedding-001
- **Operations**: Chat completion, embeddings
- **Rate Limits**: Configurable
- **Cost**: Optimized pricing vs direct OpenAI

## Test Categories

### Voice Transcription
- Tests speech-to-text functionality
- Supports multiple audio formats
- Language detection capabilities
- Cost: $0.006 per minute

### Text-to-Speech
- Tests text-to-audio synthesis
- Multiple voice options
- Different audio formats
- Cost: $0.015 per 1K characters

### Chat Completion
- Tests LLM response generation
- Context handling
- Model comparison
- Cost: Varies by model

### Embeddings
- Tests text vectorization
- Similarity search
- Multilingual support
- Cost: $0.00002 per 1K tokens

### Planning
- Tests development plan generation
- Structured output parsing
- Context integration
- Cost: Varies by model

### RAG Queries
- Tests retrieval-augmented generation
- Document search
- Context relevance
- Cost: Varies by model

## Security Features

### API Key Management
```python
from real_api_framework.security import APIKeyManager, SecureCredentialsStore

# Initialize secure store
store = SecureCredentialsStore()
manager = APIKeyManager(store)

# Store API key securely
key_id = manager.store_key("openai", "sk-your-key", ["testing"])

# Retrieve API key
api_key = manager.get_key("openai")

# Validate key
validation = manager.validate_key("openai")
```

### Credential Encryption
- AES-256 encryption for stored keys
- Secure key derivation with PBKDF2
- File permission controls
- Environment variable integration

## Cost Management

### Cost Tracking
```python
# Get cost summary
summary = framework.cost_monitor.get_summary()
print(f"Total cost: ${summary['total_session_cost']:.4f}")
print(f"Provider breakdown: {summary['provider_breakdown']}")

# Test-specific costs
test_costs = framework.test_costs["my_test"]
total_test_cost = sum(c.total_cost for c in test_costs)
```

### Cost Controls
- Per-test cost limits
- Session cost limits
- Warning thresholds
- Automatic test skipping

## Monitoring and Reporting

### Session Reports
```python
# Generate comprehensive report
summary = framework.get_session_summary()

# Save detailed report
report_path = framework.save_session_report()

# Report includes:
# - Test results and statistics
# - Cost breakdown by provider/model
# - Usage patterns and trends
# - Error analysis
# - Performance metrics
```

### Real-time Monitoring
- Request rate monitoring
- Cost accumulation tracking
- Error rate analysis
- Performance metrics

## Error Handling

### Retry Logic
```python
from real_api_framework.utils import RetryHandler

retry_handler = RetryHandler(max_attempts=3, base_delay=1.0)

# Retry async function
result = await retry_handler.retry_async(api_function, *args, **kwargs)

# Retry sync function
result = retry_handler.retry_sync(sync_function, *args, **kwargs)
```

### Error Categories
- Authentication errors (401)
- Rate limit errors (429)
- Model errors (400)
- Network errors
- Timeout errors

## Test Data Management

### Test Data Generation
```python
from real_api_framework.utils import TestDataGenerator

generator = TestDataGenerator()
test_data = generator.get_test_data()

# Includes:
# - Text samples for transcription
# - Audio files in various formats
# - Test documents for RAG
# - Sample queries and prompts
```

### Response Validation
```python
from real_api_framework.utils import APIResponseValidator

validator = APIResponseValidator()

# Validate API response
validation = validator.validate(response, "transcription")
if validation["valid"]:
    print("Response passed validation")
else:
    print(f"Validation errors: {validation['errors']}")
```

## Best Practices

### 1. Cost Management
- Set conservative cost limits for CI/CD
- Use cheaper models for testing (gpt-4o-mini vs gpt-4)
- Monitor costs regularly
- Implement cost alerts

### 2. Security
- Never commit API keys to version control
- Use environment variables for credentials
- Regular key rotation
- Limit API key permissions

### 3. Test Design
- Use descriptive test names
- Test both success and failure scenarios
- Validate responses thoroughly
- Handle edge cases gracefully

### 4. Performance
- Implement appropriate timeouts
- Use rate limiting
- Handle concurrent requests carefully
- Monitor test execution time

## Troubleshooting

### Common Issues

#### API Key Errors
```
Error: Missing or invalid API keys for providers: ['openai']
```
**Solution**: Ensure OPENAI_API_KEY is set in environment variables

#### Rate Limiting
```
Warning: Rate limit exceeded: 65 requests in last minute (limit: 60)
```
**Solution**: Increase rate limit limits or add delays between tests

#### Cost Limits
```
Warning: Session cost warning: $5.20 (threshold: $4.00)
```
**Solution**: Tests will be skipped until cost resets or limits increased

#### Timeouts
```
Error: Test exceeded timeout of 300.0s
```
**Solution**: Increase timeout or optimize test performance

### Debug Mode
```python
# Enable debug logging
config = APITestConfig(
    log_level="DEBUG",
    log_requests=True,
    log_responses=True  # Be careful with sensitive data
)
```

## Examples

See `example_tests.py` for comprehensive test examples including:
- Basic API testing
- Cost control validation
- Error handling
- Performance testing
- End-to-end workflows

## Contributing

1. Follow the existing code style
2. Add comprehensive tests for new features
3. Update documentation
4. Ensure security best practices
5. Test cost controls thoroughly

## License

This framework is part of the Voice-RAG-System project and follows the same license terms.