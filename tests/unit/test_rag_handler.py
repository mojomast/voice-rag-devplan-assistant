import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from rag_handler import RAGHandler

class TestRAGHandler:
    @pytest.fixture
    def rag_handler(self):
        return RAGHandler()

    def test_rag_handler_initialization(self, rag_handler):
        """Test that RAG handler initializes properly"""
        assert rag_handler is not None
        assert hasattr(rag_handler, 'ask_question')

    def test_rag_handler_has_required_methods(self, rag_handler):
        """Test that RAG handler has all required methods"""
        required_methods = [
            'ask_question',
            'clear_conversation',
            'get_conversation_history'
        ]

        for method in required_methods:
            assert hasattr(rag_handler, method), f"Missing method: {method}"
            assert callable(getattr(rag_handler, method)), f"Method {method} is not callable"

    def test_ask_question_without_documents(self, rag_handler):
        """Test asking questions when no documents are loaded"""
        result = rag_handler.ask_question("What is AI?")

        assert isinstance(result, dict)
        assert "answer" in result
        # Should either provide a response or indicate no documents available

    def test_ask_question_empty_query(self, rag_handler):
        """Test asking empty question"""
        result = rag_handler.ask_question("")

        assert isinstance(result, dict)
        # Should handle empty queries gracefully
        if "error" in result:
            assert result["error"] is not None

    def test_ask_question_none_query(self, rag_handler):
        """Test asking None question"""
        result = rag_handler.ask_question(None)

        assert isinstance(result, dict)
        assert "error" in result or "answer" in result

    def test_conversation_memory(self, rag_handler):
        """Test conversation memory functionality"""
        # Ask first question
        result1 = rag_handler.ask_question("What is machine learning?")
        assert isinstance(result1, dict)

        # Ask follow-up question that depends on context
        result2 = rag_handler.ask_question("Can you elaborate on that?")
        assert isinstance(result2, dict)

        # Get conversation history
        history = rag_handler.get_conversation_history()
        assert isinstance(history, list)
        # Should contain both questions
        assert len(history) >= 2

    def test_clear_conversation(self, rag_handler):
        """Test clearing conversation history"""
        # Add some conversation
        rag_handler.ask_question("Test question 1")
        rag_handler.ask_question("Test question 2")

        # Clear conversation
        rag_handler.clear_conversation()

        # History should be empty
        history = rag_handler.get_conversation_history()
        assert len(history) == 0

    def test_long_question_handling(self, rag_handler):
        """Test handling of very long questions"""
        long_question = "What is artificial intelligence? " * 100
        result = rag_handler.ask_question(long_question)

        assert isinstance(result, dict)
        # Should handle long questions appropriately
        assert "answer" in result or "error" in result

    def test_special_characters_in_query(self, rag_handler):
        """Test handling of special characters in queries"""
        special_query = "What about AI & ML? (specifically deep learning!)"
        result = rag_handler.ask_question(special_query)

        assert isinstance(result, dict)
        assert "answer" in result or "error" in result

    def test_multilingual_query(self, rag_handler):
        """Test handling of non-English queries"""
        multilingual_queries = [
            "¿Qué es la inteligencia artificial?",  # Spanish
            "Qu'est-ce que l'intelligence artificielle?",  # French
            "Was ist künstliche Intelligenz?",  # German
        ]

        for query in multilingual_queries:
            result = rag_handler.ask_question(query)
            assert isinstance(result, dict)
            # Should either handle or gracefully reject

    def test_conversation_context_preservation(self, rag_handler):
        """Test that conversation context is preserved across queries"""
        # Simulate a conversation
        queries = [
            "Tell me about Python programming",
            "What are its main features?",
            "How does it compare to Java?",
            "What about performance?"
        ]

        results = []
        for query in queries:
            result = rag_handler.ask_question(query)
            results.append(result)
            assert isinstance(result, dict)

        # All results should be valid
        assert len(results) == len(queries)

        # Context should be maintained (if implemented)
        history = rag_handler.get_conversation_history()
        assert len(history) >= len(queries)

    def test_error_recovery(self, rag_handler):
        """Test error recovery mechanisms"""
        # Test with problematic queries
        problematic_queries = [
            "",  # Empty
            None,  # None
            "?" * 1000,  # Very long
            "\n\n\n",  # Just whitespace
        ]

        for query in problematic_queries:
            try:
                result = rag_handler.ask_question(query)
                assert isinstance(result, dict)
                # Should handle errors gracefully
            except Exception as e:
                # Should not raise unhandled exceptions
                pytest.fail(f"Unhandled exception for query '{query}': {e}")

    def test_source_attribution(self, rag_handler):
        """Test that sources are properly attributed in responses"""
        result = rag_handler.ask_question("Test question for source attribution")

        if isinstance(result, dict) and "sources" in result:
            sources = result["sources"]
            assert isinstance(sources, list)
            # Each source should have required fields
            for source in sources:
                assert isinstance(source, dict)

    def test_answer_quality_indicators(self, rag_handler):
        """Test answer quality indicators if implemented"""
        result = rag_handler.ask_question("What is machine learning?")

        assert isinstance(result, dict)

        # Check for quality indicators
        possible_indicators = ["confidence", "relevance", "completeness"]
        for indicator in possible_indicators:
            if indicator in result:
                assert isinstance(result[indicator], (int, float))
                assert 0 <= result[indicator] <= 1  # Assuming normalized scores

    @patch('openai.ChatCompletion.create')
    def test_llm_integration(self, mock_create, rag_handler):
        """Test LLM integration"""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "This is a test response about AI."
        mock_create.return_value = mock_response

        result = rag_handler.ask_question("What is AI?")

        if result.get("status") == "success":
            assert "answer" in result
            assert isinstance(result["answer"], str)

    def test_conversation_limit_handling(self, rag_handler):
        """Test handling of conversation length limits"""
        # Add many questions to test memory limits
        for i in range(20):
            result = rag_handler.ask_question(f"Question number {i}")
            assert isinstance(result, dict)

        # Check that memory is managed appropriately
        history = rag_handler.get_conversation_history()
        # Should not grow infinitely
        assert len(history) <= 50  # Reasonable limit

    def test_concurrent_questions(self, rag_handler):
        """Test handling of concurrent questions"""
        import threading
        import time

        results = []

        def ask_question(question_id):
            result = rag_handler.ask_question(f"Concurrent question {question_id}")
            results.append(result)

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=ask_question, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All questions should be handled
        assert len(results) == 3
        for result in results:
            assert isinstance(result, dict)

    def test_retrieval_accuracy(self, rag_handler):
        """Test retrieval accuracy if documents are available"""
        # This test would be more meaningful with actual documents loaded
        # For now, test the structure

        result = rag_handler.ask_question("Find information about specific topic")

        if isinstance(result, dict) and result.get("status") == "success":
            # Check response structure
            assert "answer" in result
            if "sources" in result:
                assert isinstance(result["sources"], list)
            if "metadata" in result:
                assert isinstance(result["metadata"], dict)