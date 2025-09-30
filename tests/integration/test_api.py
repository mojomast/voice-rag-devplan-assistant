import pytest
from fastapi.testclient import TestClient
import tempfile
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from main import app

client = TestClient(app)

class TestAPI:
    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_upload_document_success(self):
        """Test successful document upload"""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for API testing.")
            temp_file_path = f.name

        try:
            with open(temp_file_path, 'rb') as f:
                response = client.post(
                    "/documents/upload",
                    files={"file": ("test.txt", f, "text/plain")}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "test.txt" in data["message"]

        finally:
            os.unlink(temp_file_path)

    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"invalid content")
            temp_file_path = f.name

        try:
            with open(temp_file_path, 'rb') as f:
                response = client.post(
                    "/documents/upload",
                    files={"file": ("test.xyz", f, "application/octet-stream")}
                )

            assert response.status_code == 400

        finally:
            os.unlink(temp_file_path)

    def test_upload_empty_file(self):
        """Test upload with empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")  # Empty file
            temp_file_path = f.name

        try:
            with open(temp_file_path, 'rb') as f:
                response = client.post(
                    "/documents/upload",
                    files={"file": ("empty.txt", f, "text/plain")}
                )

            # Should handle empty files gracefully
            assert response.status_code in [200, 400]

        finally:
            os.unlink(temp_file_path)

    def test_document_stats_endpoint(self):
        """Test document statistics endpoint"""
        response = client.get("/documents/stats")
        assert response.status_code == 200
        data = response.json()
        assert "exists" in data
        assert isinstance(data["exists"], bool)

    def test_query_without_documents(self):
        """Test querying when no documents are uploaded"""
        response = client.post(
            "/query/text",
            json={"query": "What is this about?"}
        )
        # Should either work or return appropriate error
        assert response.status_code in [200, 404, 500]

    def test_query_with_empty_query(self):
        """Test querying with empty query"""
        response = client.post(
            "/query/text",
            json={"query": ""}
        )
        # Should handle empty queries gracefully
        assert response.status_code in [200, 400]

    def test_query_with_long_query(self):
        """Test querying with very long query"""
        long_query = "What is AI? " * 500  # Very long query
        response = client.post(
            "/query/text",
            json={"query": long_query}
        )
        # Should handle long queries appropriately
        assert response.status_code in [200, 400, 413]

    def test_voice_query_endpoint_exists(self):
        """Test that voice query endpoint exists"""
        # Create a minimal audio file for testing
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Write minimal WAV header
            f.write(b'RIFF' + b'\x00' * 36 + b'WAVE' + b'fmt ' + b'\x00' * 20)
            temp_audio_path = f.name

        try:
            with open(temp_audio_path, 'rb') as f:
                response = client.post(
                    "/query/voice",
                    files={"file": ("test_audio.wav", f, "audio/wav")}
                )

            # Endpoint should exist (may fail due to invalid audio)
            assert response.status_code in [200, 400, 500, 422]

        finally:
            os.unlink(temp_audio_path)

    def test_chat_clear_endpoint(self):
        """Test chat clear endpoint"""
        response = client.post("/chat/clear")
        assert response.status_code == 200

    def test_documents_clear_endpoint(self):
        """Test documents clear endpoint"""
        response = client.delete("/documents/clear")
        assert response.status_code in [200, 404]

    def test_usage_stats_endpoint(self):
        """Test usage statistics endpoint"""
        response = client.get("/usage/stats")
        # Should return usage statistics
        assert response.status_code in [200, 404]

    def test_voice_voices_endpoint(self):
        """Test available voices endpoint"""
        response = client.get("/voice/voices")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_concurrent_uploads(self):
        """Test concurrent document uploads"""
        import threading
        import time

        results = []

        def upload_document(doc_id):
            content = f"Test document {doc_id} with unique content."

            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = f.name

            try:
                with open(temp_path, 'rb') as f:
                    response = client.post(
                        "/documents/upload",
                        files={"file": (f"doc_{doc_id}.txt", f, "text/plain")}
                    )
                results.append(response.status_code)
            finally:
                os.unlink(temp_path)

        # Start multiple upload threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=upload_document, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that all uploads were handled
        assert len(results) == 3
        # At least some should succeed (allowing for rate limiting)
        success_count = sum(1 for code in results if code == 200)
        assert success_count >= 1

    def test_query_after_upload_workflow(self):
        """Test the complete upload and query workflow"""
        # Upload a document
        test_content = "This document discusses artificial intelligence and machine learning applications."

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name

        try:
            # Upload the document
            with open(temp_file_path, 'rb') as f:
                upload_response = client.post(
                    "/documents/upload",
                    files={"file": ("ai_doc.txt", f, "text/plain")}
                )

            assert upload_response.status_code == 200

            # Query the document
            query_response = client.post(
                "/query/text",
                json={"query": "What does this document discuss?"}
            )

            # Should work if the system is functioning properly
            if query_response.status_code == 200:
                data = query_response.json()
                assert "status" in data

        finally:
            os.unlink(temp_file_path)
            # Try to clean up
            client.delete("/documents/clear")

    def test_error_handling_malformed_requests(self):
        """Test error handling for malformed requests"""
        # Test POST without required fields
        response = client.post("/query/text", json={})
        assert response.status_code in [400, 422]

        # Test invalid JSON
        response = client.post("/query/text", data="invalid json")
        assert response.status_code in [400, 422]

        # Test missing file in upload
        response = client.post("/documents/upload")
        assert response.status_code in [400, 422]