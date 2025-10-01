import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger
from pydantic import Field
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.llms.base import BaseLLM
from langchain.schema import Document, Generation, LLMResult

try:
    from langchain_community.embeddings import FakeEmbeddings
except ImportError:  # pragma: no cover - fake embeddings may be unavailable in minimal envs
    FakeEmbeddings = None

try:
    from .auto_indexer import get_auto_indexer
    from .config import settings
    from .indexing.requesty_embeddings import RequestyEmbeddings
    from .requesty_client import RequestyClient
    from .small_talk import get_small_talk_response
except ImportError:  # pragma: no cover - support direct imports in tests
    from auto_indexer import get_auto_indexer
    from config import settings
    from indexing.requesty_embeddings import RequestyEmbeddings
    from requesty_client import RequestyClient
    from small_talk import get_small_talk_response

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
        self.plan_vector_store: Optional[FAISS] = None
        self.plan_embeddings: Optional[Any] = None
        self.project_vector_store: Optional[FAISS] = None
        self.project_embeddings: Optional[Any] = None

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
        try:
            get_auto_indexer().register_rag_handler(self)
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("Failed to register RAG handler with auto indexer: %s", exc)

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
        self.plan_vector_store = self.vector_store
        self.project_vector_store = self.vector_store

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

        self._load_plan_vector_store()
        self._load_project_vector_store()

    def ask_question(self, query: str) -> Dict:
        """Asks a question to the RAG chain and returns the answer and sources."""
        preview = "" if query is None else str(query)
        logger.info("Processing query snippet: {}", preview[:100])

        stripped_query = (query or "").strip()

        if not stripped_query:
            answer = "No query provided."
            response = {
                "answer": answer,
                "sources": [],
                "query": stripped_query,
                "status": "error",
                "error": "empty_query"
            }

            if self.test_mode:
                response["test_mode"] = True
                self._append_test_history(stripped_query, answer, "error", response_type="system")
            return response

        small_talk_answer = get_small_talk_response(stripped_query)
        if small_talk_answer:
            logger.debug("Handled small talk without invoking RAG chain")
            return self._build_small_talk_response(stripped_query, small_talk_answer)

        if self.test_mode:
            normalized_query = stripped_query
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

            self._append_test_history(normalized_query, answer, status)

            return {
                "answer": answer,
                "sources": sources,
                "query": normalized_query,
                "status": status,
                "test_mode": True
            }

        try:
            result = self.qa_chain.invoke({"question": query})

            raw_source_documents = result.get("source_documents", []) or []

            source_documents = []
            for doc in raw_source_documents:
                source_info = {
                    "source": doc.metadata.get('source', 'Unknown'),
                    "page": doc.metadata.get('page', 'N/A'),
                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                source_documents.append(source_info)

            answer_text = result.get("answer", "")

            if self._looks_like_insufficient_answer(answer_text) and source_documents:
                summary_text = self._build_summary_from_sources(source_documents, stripped_query)
                if summary_text:
                    logger.debug("Generated contextual summary fallback for insufficient LLM answer")
                    return {
                        "answer": summary_text,
                        "sources": source_documents,
                        "query": query,
                        "status": "success",
                        "metadata": {"response_type": "context_summary"}
                    }

            response = {
                "answer": answer_text,
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

    def _build_small_talk_response(self, query: str, answer: str) -> Dict:
        response: Dict[str, Any] = {
            "answer": answer,
            "sources": [],
            "query": query,
            "status": "success",
            "metadata": {"response_type": "small_talk"}
        }

        if self.test_mode:
            response["test_mode"] = True
            self._append_test_history(query, answer, "success", response_type="small_talk")
        else:
            memory = getattr(self, "memory", None)
            chat_memory = getattr(memory, "chat_memory", None) if memory else None
            if chat_memory:
                try:
                    chat_memory.add_user_message(query)
                    chat_memory.add_ai_message(answer)
                except Exception as exc:  # pragma: no cover - best effort logging
                    logger.debug("Failed to record small talk in conversation memory: %s", exc)

        return response

    def _append_test_history(
        self,
        question: str,
        answer: str,
        status: str,
        *,
        response_type: str = "default"
    ) -> None:
        record = {
            "question": question,
            "answer": answer,
            "status": status,
            "type": response_type,
        }

        if not hasattr(self, "_conversation_history") or self._conversation_history is None:
            self._conversation_history = []

        self._conversation_history.append(record)

        history_limit = getattr(self, "_history_limit", 50)
        if len(self._conversation_history) > history_limit:
            self._conversation_history = self._conversation_history[-history_limit:]

    @staticmethod
    def _looks_like_insufficient_answer(answer: str) -> bool:
        if not answer:
            return False

        lowered = answer.lower()
        insufficient_phrases = (
            "i don't have enough information",
            "i don't have enough info",
            "i cannot find",
            "i can't find",
            "no information found",
            "unable to locate",
        )
        return any(phrase in lowered for phrase in insufficient_phrases)

    @staticmethod
    def _build_summary_from_sources(sources: List[Dict[str, Any]], query: str) -> Optional[str]:
        if not sources:
            return None

        summary_lines = [
            "Here's what I can gather from the matching documents:",
        ]

        for index, source in enumerate(sources[:3], start=1):
            source_name = source.get("source", f"Document {index}")
            preview = source.get("content_preview", "").strip()
            if not preview:
                continue

            condensed = " ".join(preview.split())
            if len(condensed) > 300:
                condensed = condensed[:300] + "..."

            summary_lines.append(f"- **{source_name}**: {condensed}")

        if len(summary_lines) == 1:
            return None

        summary_lines.append(
            "Let me know if you'd like a deeper breakdown or specific actions for this file."
        )

        return "\n".join(summary_lines)

    def search(
        self,
        query: str,
        *,
        k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform similarity search across available vector stores."""

        metadata_filter = metadata_filter or {}

        if self.test_mode:
            return [
                {
                    "score": 0.0,
                    "metadata": {"type": metadata_filter.get("type", "test"), "query": query},
                    "content": f"Test mode result for '{query}'",
                }
            ]

        target_type = metadata_filter.get("type")
        store, description = self._resolve_store_for_search(target_type)
        if store is None:
            logger.debug("No vector store available for search type %s", target_type)
            return []

        results = []
        try:
            matches = store.similarity_search_with_score(query, k=k)
            for document, score in matches:
                metadata = getattr(document, "metadata", {}) or {}
                if self._metadata_matches(metadata, metadata_filter):
                    results.append(
                        {
                            "score": score,
                            "metadata": metadata,
                            "content": document.page_content,
                            "source": metadata.get("source"),
                            "index": description,
                        }
                    )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Vector search failed (%s): %s", description, exc)
        return results

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

    def reload_plan_vector_store(self) -> None:
        """Reload the devplan index from disk."""
        self._load_plan_vector_store(force_reload=True)

    def reload_project_vector_store(self) -> None:
        """Reload the project/conversation index from disk."""
        self._load_project_vector_store(force_reload=True)

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

    def _resolve_store_for_search(self, target_type: Optional[str]) -> tuple[Optional[FAISS], str]:
        if target_type == "devplan":
            return self.plan_vector_store, "devplan_index"
        if target_type in {"project", "conversation"}:
            return self.project_vector_store, "project_index"
        return self.vector_store, "document_index"

    def _metadata_matches(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        for key, value in filters.items():
            if value is None:
                continue
            if metadata.get(key) != value:
                return False
        return True

    def _load_plan_vector_store(self, force_reload: bool = False) -> None:
        if not force_reload and self.plan_vector_store is not None:
            return

        index_path = Path(settings.DEVPLAN_VECTOR_STORE_PATH)
        index_file = index_path / "index.faiss"
        if not index_file.exists():
            self.plan_vector_store = None
            return

        try:
            embeddings = RequestyEmbeddings(RequestyClient())
            self.plan_vector_store = FAISS.load_local(
                str(index_path),
                embeddings,
                allow_dangerous_deserialization=True,
            )
            self.plan_embeddings = embeddings
            logger.info("Loaded devplan vector store from %s", index_path)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to load devplan vector store: %s", exc)
            self.plan_vector_store = None

    def _load_project_vector_store(self, force_reload: bool = False) -> None:
        if not force_reload and self.project_vector_store is not None:
            return

        index_path = Path(settings.PROJECT_VECTOR_STORE_PATH)
        index_file = index_path / "index.faiss"
        if not index_file.exists():
            self.project_vector_store = None
            return

        try:
            embeddings = RequestyEmbeddings(RequestyClient())
            self.project_vector_store = FAISS.load_local(
                str(index_path),
                embeddings,
                allow_dangerous_deserialization=True,
            )
            self.project_embeddings = embeddings
            logger.info("Loaded project vector store from %s", index_path)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to load project vector store: %s", exc)
            self.project_vector_store = None