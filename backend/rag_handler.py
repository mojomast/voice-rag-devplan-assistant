import os
from typing import Dict, List, Optional
from loguru import logger
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings
from langchain.schema import BaseLanguageModel
from langchain.llms.base import BaseLLM
from .config import settings
from .requesty_client import RequestyClient

class RequestyLLM(BaseLLM):
    """Custom LangChain LLM wrapper for Requesty.ai client"""

    def __init__(self, requesty_client: RequestyClient):
        super().__init__()
        self.requesty_client = requesty_client

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self.requesty_client.chat_completion(messages)

    @property
    def _llm_type(self) -> str:
        return "requesty"

class RAGHandler:
    def __init__(self):
        # Check if vector store exists
        if not os.path.exists(settings.VECTOR_STORE_PATH) or not os.listdir(settings.VECTOR_STORE_PATH):
            raise FileNotFoundError(f"Vector store not found at {settings.VECTOR_STORE_PATH}. Please upload and index documents first.")

        # Initialize embeddings
        self.embeddings_model = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL
        )

        # Load vector store
        logger.info("Loading vector store")
        self.vector_store = FAISS.load_local(
            settings.VECTOR_STORE_PATH,
            self.embeddings_model,
            allow_dangerous_deserialization=True
        )

        # Initialize Requesty.ai client and LLM
        self.requesty_client = RequestyClient()
        self.llm = RequestyLLM(self.requesty_client)

        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key='answer'
        )

        # Create retrieval chain
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            ),
            memory=self.memory,
            return_source_documents=True,
            verbose=settings.DEBUG
        )

        logger.info("RAG Handler initialized successfully")

    def ask_question(self, query: str) -> Dict:
        """Asks a question to the RAG chain and returns the answer and sources."""
        logger.info(f"Processing query: {query[:100]}...")

        try:
            result = self.qa_chain.invoke({"question": query})

            # Process source documents
            source_documents = []
            if 'source_documents' in result:
                for doc in result['source_documents']:
                    source_info = {
                        "source": doc.metadata.get('source', 'Unknown'),
                        "page": doc.metadata.get('page', 'N/A'),
                        "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    }
                    source_documents.append(source_info)

            response = {
                "answer": result["answer"],
                "sources": source_documents,
                "query": query,
                "status": "success"
            }

            logger.info("Query processed successfully")
            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "answer": f"I apologize, but I encountered an error processing your question: {str(e)}",
                "sources": [],
                "query": query,
                "status": "error",
                "error": str(e)
            }

    def clear_memory(self):
        """Clear the conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory cleared")

    def get_memory_summary(self) -> Dict:
        """Get a summary of the current conversation memory"""
        try:
            messages = self.memory.chat_memory.messages
            return {
                "message_count": len(messages),
                "memory_buffer": str(self.memory.buffer) if hasattr(self.memory, 'buffer') else "N/A"
            }
        except Exception as e:
            return {"error": str(e)}

    def reload_vector_store(self):
        """Reload the vector store (useful after adding new documents)"""
        try:
            logger.info("Reloading vector store")
            self.vector_store = FAISS.load_local(
                settings.VECTOR_STORE_PATH,
                self.embeddings_model,
                allow_dangerous_deserialization=True
            )

            # Update the retriever in the chain
            self.qa_chain.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )

            logger.info("Vector store reloaded successfully")
            return {"status": "success", "message": "Vector store reloaded"}

        except Exception as e:
            logger.error(f"Error reloading vector store: {e}")
            return {"status": "error", "error": str(e)}