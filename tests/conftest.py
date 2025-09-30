import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

@pytest.fixture
def temp_directory():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_text_content():
    """Sample text content for testing"""
    return """
    This is a comprehensive test document for the Voice RAG system.
    It contains information about artificial intelligence, machine learning,
    and natural language processing. The document discusses various
    applications of AI in healthcare, finance, and education sectors.

    Machine learning is a subset of artificial intelligence that focuses
    on algorithms and statistical models that computer systems use to
    perform tasks without explicit instructions.

    Natural language processing (NLP) is a subfield of linguistics,
    computer science, and artificial intelligence concerned with the
    interactions between computers and human language.
    """

@pytest.fixture
def sample_pdf_content():
    """Sample PDF content metadata for testing"""
    return {
        "title": "Test Document",
        "author": "Test Author",
        "pages": 3,
        "content": "This is sample PDF content for testing purposes."
    }

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    class MockResponse:
        def __init__(self, text="Test response", status="success"):
            self.text = text
            self.status = status
            self.choices = [MockChoice(text)]

        class MockChoice:
            def __init__(self, text):
                self.message = MockMessage(text)

        class MockMessage:
            def __init__(self, text):
                self.content = text

    return MockResponse

@pytest.fixture
def test_audio_file():
    """Create a test audio file"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Write minimal WAV header for testing
        f.write(b'RIFF' + b'\x24\x08\x00\x00' + b'WAVE')
        f.write(b'fmt ' + b'\x10\x00\x00\x00')
        f.write(b'\x01\x00\x01\x00\x44\xAC\x00\x00')
        f.write(b'\x88\x58\x01\x00\x02\x00\x10\x00')
        f.write(b'data' + b'\x00\x08\x00\x00')
        # Add some fake audio data
        f.write(b'\x00' * 2048)
        return f.name

@pytest.fixture
def cleanup_test_files():
    """Cleanup test files after test completion"""
    files_to_cleanup = []

    def add_file(filepath):
        files_to_cleanup.append(filepath)

    yield add_file

    # Cleanup
    for filepath in files_to_cleanup:
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass

@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings"""
    return {
        "test_mode": True,
        "disable_external_apis": True,
        "mock_responses": True,
        "temp_dir": tempfile.gettempdir()
    }

# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )
    config.addinivalue_line(
        "markers", "voice: mark test as voice processing test"
    )
    config.addinivalue_line(
        "markers", "rag: mark test as RAG functionality test"
    )
    config.addinivalue_line(
        "markers", "document: mark test as document processing test"
    )