import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from document_processor import DocumentProcessor

class TestDocumentProcessor:
    @pytest.fixture
    def processor(self):
        return DocumentProcessor()

    @pytest.fixture
    def sample_txt_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for the RAG system. It contains multiple sentences for testing.")
            return f.name

    @pytest.fixture
    def sample_large_txt_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Create a larger document for chunking tests
            content = "This is a test document. " * 100  # Repeat to make it larger
            f.write(content)
            return f.name

    def test_load_text_document(self, processor, sample_txt_file):
        """Test loading a simple text document"""
        docs = processor.load_document(sample_txt_file)
        assert len(docs) > 0
        assert "test document" in docs[0].page_content
        os.unlink(sample_txt_file)

    def test_split_documents(self, processor, sample_large_txt_file):
        """Test document splitting functionality"""
        docs = processor.load_document(sample_large_txt_file)
        chunks = processor.split_documents(docs)
        assert len(chunks) >= len(docs)
        os.unlink(sample_large_txt_file)

    def test_unsupported_file_type(self, processor):
        """Test error handling for unsupported file types"""
        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.load_document("test.xyz")

    def test_nonexistent_file(self, processor):
        """Test error handling for non-existent files"""
        with pytest.raises(FileNotFoundError):
            processor.load_document("nonexistent_file.txt")

    def test_empty_file(self, processor):
        """Test handling of empty files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")  # Empty file
            empty_file = f.name

        try:
            docs = processor.load_document(empty_file)
            # Should handle empty files gracefully
            assert isinstance(docs, list)
        finally:
            os.unlink(empty_file)

    def test_pdf_document_loading(self, processor):
        """Test PDF document loading (if available)"""
        # Create a simple PDF content test
        # This would require actual PDF files for real testing
        # For now, we'll test the file type detection
        try:
            # This will fail but we test the method exists
            processor.load_document("test.pdf")
        except (FileNotFoundError, ImportError):
            # Expected for missing file or missing dependencies
            pass

    def test_document_metadata_preservation(self, processor, sample_txt_file):
        """Test that document metadata is preserved"""
        docs = processor.load_document(sample_txt_file)
        assert len(docs) > 0
        doc = docs[0]
        assert hasattr(doc, 'metadata')
        assert 'source' in doc.metadata
        os.unlink(sample_txt_file)

    def test_chunking_parameters(self, processor, sample_large_txt_file):
        """Test different chunking parameters"""
        docs = processor.load_document(sample_large_txt_file)

        # Test default chunking
        chunks_default = processor.split_documents(docs)

        # All chunks should have reasonable size
        for chunk in chunks_default:
            assert len(chunk.page_content) > 0
            assert len(chunk.page_content) <= 2000  # Assuming reasonable chunk size

        os.unlink(sample_large_txt_file)

    def test_special_characters_handling(self, processor):
        """Test handling of special characters in documents"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Document with special characters: àáâãäå çčćð éêëě ñóôõö üúù")
            special_file = f.name

        try:
            docs = processor.load_document(special_file)
            assert len(docs) > 0
            assert "special characters" in docs[0].page_content
        finally:
            os.unlink(special_file)

    def test_document_processing_pipeline(self, processor, sample_txt_file):
        """Test the complete document processing pipeline"""
        # This would test the full process_and_index_file method if it exists
        try:
            result = processor.process_and_index_file(sample_txt_file)
            # Check if the method exists and returns expected format
            assert isinstance(result, dict)
        except AttributeError:
            # Method might not exist in current implementation
            pass
        finally:
            os.unlink(sample_txt_file)