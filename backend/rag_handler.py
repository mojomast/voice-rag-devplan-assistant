import os
from typing import Dict, List, Optional, Any
from loguru import logger
from pydantic import Field
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.llms.base import BaseLLM
from langchain.schema import Document, LLMResult, Generation

try:
    from langchain_community.embeddings import FakeEmbeddings
except ImportError:  # pragma: no cover - fake embeddings may be unavailable in minimal envs
    FakeEmbeddings = None

try:
    from .config import settings
    from .requesty_client import RequestyClient
except ImportError:  # pragma: no cover - support direct imports in tests
    from config import settings
    from requesty_client import RequestyClient

class RequestyLLM(BaseLLM):
    """Custom LangChain LLM wrapper for Requesty.ai client"""
    
    requesty_client: Any = Field(default=None, exclude=True)

    def __init__(self, requesty_client: RequestyClient, **kwargs):
        super().__init__(**kwargs)
        self.requesty_client = requesty_client

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs) -> LLMResult:
        """Generate responses for the given prompts."""
        generations = []
        for prompt in prompts:
            messages = [{"role": "user", "content": prompt}]
            response_text = self.requesty_client.chat_completion(messages)
            generations.append([Generation(text=response_text)])
        return LLMResult(generations=generations)

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Legacy method for backwards compatibility."""
        messages = [{"role": "user", "content": prompt}]
        return self.requesty_client.chat_completion(messages)

    @property
    def _llm_type(self) -> str:
        return "requesty"

class RAGHandler:
    def __init__(self):
        self.test_mode = settings.TEST_MODE

        if self.test_mode:
            self._init_test_mode()
        else:
            try:
                self._init_standard_mode()
            except FileNotFoundError as exc:
                logger.warning(f"Vector store unavailable ({exc}); switching to TEST_MODE")
                self.test_mode = True
                self._init_test_mode()
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.error(f"Failed to initialize standard RAG mode: {exc}; switching to TEST_MODE")
                self.test_mode = True
                self._init_test_mode()

        logger.info("RAG Handler initialized successfully")

    def _init_test_mode(self):
        if FakeEmbeddings is None:
            raise ImportError("FakeEmbeddings is required for TEST_MODE but is not available")

        self.embeddings_model = FakeEmbeddings(size=1536)
        self._history_limit = 50
        self._test_documents = self._generate_test_documents()
        self.vector_store = self._build_test_vector_store(self._test_documents)
        self.requesty_client = None
        self.llm = None
        self.memory = None
        self.qa_chain = None
        self._conversation_history: List[Dict[str, Optional[str]]] = []

    def _init_standard_mode(self):
        if not os.path.exists(settings.VECTOR_STORE_PATH) or not os.listdir(settings.VECTOR_STORE_PATH):
            raise FileNotFoundError(
                f"Vector store not found at {settings.VECTOR_STORE_PATH}. Please upload and index documents first."
            )

        if settings.OPENAI_API_KEY:
            self.embeddings_model = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL
            )
        else:
            if FakeEmbeddings is None:
                raise ValueError("OPENAI_API_KEY is missing and FakeEmbeddings is unavailable for fallback")
            logger.info("OPENAI_API_KEY not provided - using FakeEmbeddings for vector store operations")
            self.embeddings_model = FakeEmbeddings(size=1536)

        logger.info("Loading vector store")
        self.vector_store = FAISS.load_local(
            settings.VECTOR_STORE_PATH,
            self.embeddings_model,
            allow_dangerous_deserialization=True
        )

        self.requesty_client = RequestyClient()
        self.llm = RequestyLLM(self.requesty_client)

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key='answer'
        )

        # Custom prompt template to ensure LLM uses the context
        qa_template = """You are a helpful assistant that answers questions by carefully reading and extracting information from the provided context.

IMPORTANT INSTRUCTIONS:
1. Answer ONLY based on the context provided below
2. Include specific details like IP addresses, credentials, names, numbers, etc. EXACTLY as they appear in the context
3. Quote or reference exact information from the context when available
4. If you cannot find the answer in the context, say "I don't have enough information in the provided documents to answer this question."
5. Do NOT make assumptions or add information not in the context

Context:
{context}

Question: {question}

Detailed Answer (include specific details from the context):"""
        
        QA_PROMPT = PromptTemplate(
            template=qa_template,
            input_variables=["context", "question"]
        )

        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 6}  # Increased from 4 to 6 for better context
            ),
            memory=self.memory,
            return_source_documents=True,
            verbose=settings.DEBUG,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT}
        )

    def ask_question(self, query: str) -> Dict:
        """Asks a question to the RAG chain and returns the answer and sources."""
        preview = "" if query is None else str(query)
        logger.info("Processing query snippet: {}", preview[:100])

        if self.test_mode:
            normalized_query = (query or "").strip()

            has_query = bool(normalized_query)

            if not has_query:
                answer = "No query provided."
                status = "error"
            else:
                answer = f"Test response for: {normalized_query}"
                status = "success"

            sources = []

            if self.vector_store is not None:
                try:
                    search_query = normalized_query or "test context"
                    matches = self.vector_store.similarity_search(search_query, k=2)
                    for doc in matches:
                        sources.append({
                            "source": doc.metadata.get("source", "TEST_SOURCE"),
                            "page": doc.metadata.get("page", "N/A"),
                            "content_preview": (doc.page_content[:200] + "...") if len(doc.page_content) > 200 else doc.page_content
                        })
                except Exception as search_error:  # pragma: no cover - defensive logging only
                    logger.warning(f"TEST_MODE retrieval simulation failed: {search_error}")

            record = {"question": normalized_query, "answer": answer, "status": status}
            self._conversation_history.append(record)
            if len(self._conversation_history) > self._history_limit:
                self._conversation_history = self._conversation_history[-self._history_limit:]

            return {
                "answer": answer,
                "sources": sources,
                "query": normalized_query,
                "status": status,
                "test_mode": True
            }

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
        if self.test_mode:
            self._conversation_history.clear()
        else:
            self.memory.clear()
        logger.info("Conversation memory cleared")

    def clear_conversation(self):
        """Alias for clear_memory to match test expectations."""
        self.clear_memory()

    def get_conversation_history(self) -> List[Dict[str, Optional[str]]]:
        """Return the stored conversation history."""
        if self.test_mode:
            return list(self._conversation_history)

        try:
            messages = self.memory.chat_memory.messages
            history = []
            for msg in messages:
                history.append({
                    "type": getattr(msg, "type", getattr(msg, "role", "message")),
                    "content": msg.content
                })
            return history
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Failed to collect conversation history: {exc}")
            return []

    def get_memory_summary(self) -> Dict:
        """Get a summary of the current conversation memory"""
        if self.test_mode:
            return {
                "message_count": len(self._conversation_history),
                "memory_buffer": "TEST_MODE_BUFFER"
            }

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
        if self.test_mode:
            logger.info("TEST_MODE: reload_vector_store is a no-op")
            return {"status": "success", "message": "TEST_MODE vector store reload skipped"}

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

    def _generate_test_documents(self) -> List[Document]:
        """Create a small test corpus for TEST_MODE vector store operations."""
        base_docs = [
            Document(
                page_content=(
                    "Artificial intelligence (AI) enables machines to learn from experience, adjust to new "
                    "inputs, and perform human-like tasks."
                ),
                metadata={
                    "source": "test_corpus_ai.txt",
                    "topic": "ai_overview",
                    "page": 1
                }
            ),
            Document(
                page_content="Machine learning is a subset of AI focused on statistical techniques to give computers the ability to learn",
                metadata={
                    "source": "test_corpus_ml.txt",
                    "topic": "machine_learning_basics",
                    "page": 1
                }
            ),
            Document(
                page_content="Deep learning uses neural networks with many layers to model complex patterns in data.",
                metadata={
                    "source": "test_corpus_dl.txt",
                    "topic": "deep_learning_intro",
                    "page": 1
                }
            )
        ]

        return base_docs

    def _build_test_vector_store(self, documents: List[Document]) -> Optional[FAISS]:
        """Create and persist a FAISS vector store for test mode operations."""
        if not documents:
            return None

        try:
            os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
            vector_store = FAISS.from_documents(documents, self.embeddings_model)
            vector_store.save_local(settings.VECTOR_STORE_PATH)
            logger.info(
                "TEST_MODE vector store created with {} documents at {}",
                len(documents),
                settings.VECTOR_STORE_PATH
            )
            return vector_store
        except Exception as exc:
            logger.warning(f"Failed to create TEST_MODE vector store: {exc}")
            return None