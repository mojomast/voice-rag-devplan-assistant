import os
from typing import List
from loguru import logger
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from .config import settings

class DocumentProcessor:
    def __init__(self, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
        )

        # Use Requesty.ai if available, otherwise OpenAI directly
        if settings.REQUESTY_API_KEY:
            # TODO: Implement Requesty.ai embeddings wrapper
            self.embeddings_model = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL
            )
        else:
            self.embeddings_model = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL
            )

        self.vector_store_path = settings.VECTOR_STORE_PATH
        os.makedirs(self.vector_store_path, exist_ok=True)
        logger.info(f"DocumentProcessor initialized with chunk_size={chunk_size}")

    def load_document(self, file_path: str) -> List[Document]:
        """Loads a document from a file path using the appropriate loader."""
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        logger.info(f"Loading document: {file_path} (type: {extension})")

        try:
            if extension == ".pdf":
                loader = PyPDFLoader(file_path)
            elif extension == ".txt":
                loader = TextLoader(file_path, encoding='utf-8')
            elif extension == ".docx":
                loader = Docx2txtLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {extension}")

            documents = loader.load()
            logger.info(f"Successfully loaded {len(documents)} document pages")
            return documents

        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            raise

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits loaded documents into smaller chunks for processing."""
        logger.info(f"Splitting {len(documents)} documents into chunks")
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks")
        return chunks

    def create_vector_store(self, chunks: List[Document]):
        """Creates or updates the FAISS vector store with document chunks."""
        try:
            index_file = os.path.join(self.vector_store_path, "index.faiss")

            if os.path.exists(index_file):
                logger.info("Loading existing vector store")
                vector_store = FAISS.load_local(
                    self.vector_store_path, self.embeddings_model, allow_dangerous_deserialization=True
                )
                logger.info(f"Adding {len(chunks)} new chunks to existing vector store")
                vector_store.add_documents(chunks)
                logger.info("Vector store updated with new documents")
            else:
                logger.info(f"Creating new vector store with {len(chunks)} chunks")
                vector_store = FAISS.from_documents(chunks, self.embeddings_model)
                logger.info("New vector store created")

            vector_store.save_local(self.vector_store_path)
            logger.info("Vector store saved successfully")

        except Exception as e:
            logger.error(f"Error creating/updating vector store: {e}")
            raise

    def process_and_index_file(self, file_path: str) -> dict:
        """A full pipeline to load, split, and index a single document file."""
        logger.info(f"Starting processing pipeline for {file_path}")

        try:
            # Load document
            docs = self.load_document(file_path)

            # Split into chunks
            chunks = self.split_documents(docs)

            # Create/update vector store
            self.create_vector_store(chunks)

            result = {
                "status": "success",
                "file_path": file_path,
                "document_count": len(docs),
                "chunk_count": len(chunks),
                "message": f"Successfully processed and indexed {file_path}"
            }

            logger.info(result["message"])
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "file_path": file_path,
                "error": str(e),
                "message": f"Failed to process {file_path}: {e}"
            }
            logger.error(error_result["message"])
            return error_result

    def get_vector_store_stats(self) -> dict:
        """Get statistics about the current vector store."""
        try:
            index_file = os.path.join(self.vector_store_path, "index.faiss")

            if not os.path.exists(index_file):
                return {"exists": False, "document_count": 0}

            vector_store = FAISS.load_local(
                self.vector_store_path, self.embeddings_model, allow_dangerous_deserialization=True
            )

            return {
                "exists": True,
                "document_count": vector_store.index.ntotal,
                "index_size": os.path.getsize(index_file)
            }

        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return {"exists": False, "error": str(e)}