import os
import io
import base64
import importlib
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from loguru import logger
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

try:
    from langchain_community.embeddings import FakeEmbeddings
except ImportError:  # pragma: no cover - fallback for environments without langchain fake embeddings
    FakeEmbeddings = None

try:
    from .config import settings
except ImportError:  # pragma: no cover - allows direct module execution in tests
    from config import settings

# Optional OCR and image processing imports
try:
    import pytesseract  # type: ignore[import-unresolved]
    from PIL import Image, ImageEnhance, ImageFilter
    import cv2  # type: ignore[import-unresolved]
    import numpy as np
    OCR_AVAILABLE = True
    logger.info("OCR capabilities enabled (pytesseract, PIL, cv2)")
except ImportError as e:
    OCR_AVAILABLE = False
    logger.warning(f"OCR not available - install pytesseract, pillow, opencv-python: {e}")

# Optional advanced PDF processing
try:
    import fitz  # type: ignore[import-unresolved]  # PyMuPDF
    import pymupdf  # type: ignore[import-unresolved]
    PDF_ADVANCED = True
    logger.info("Advanced PDF processing enabled (PyMuPDF)")
except ImportError:
    PDF_ADVANCED = False
    logger.warning("Advanced PDF processing not available - install pymupdf for better PDF handling")

# Optional document format support
try:
    from langchain_community.document_loaders import UnstructuredPowerPointLoader, UnstructuredExcelLoader
    import pandas as pd
    OFFICE_SUPPORT = True
    logger.info("Extended office document support enabled")
except ImportError:
    OFFICE_SUPPORT = False
    logger.warning("Extended office support not available")

# Optional HTML parsing support
try:
    BeautifulSoup = importlib.import_module("bs4").BeautifulSoup  # type: ignore[attr-defined]
    BS4_AVAILABLE = True
    logger.info("BeautifulSoup available for HTML parsing")
except ImportError:
    BeautifulSoup = None  # type: ignore[assignment]
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup not available - HTML parsing will use fallback mode")

class DocumentProcessor:
    def __init__(self, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP):
        self.test_mode = settings.TEST_MODE
        self.embeddings_provider = "openai"
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
        )

        if self.test_mode or not settings.OPENAI_API_KEY:
            if FakeEmbeddings is None:
                raise ImportError("FakeEmbeddings is required for TEST_MODE but is not available")
            self.embeddings_model = FakeEmbeddings(size=1536)
            self.embeddings_provider = "fake"
            if not self.test_mode:
                logger.info("OPENAI_API_KEY not provided - using deterministic FakeEmbeddings for vector storage")
        else:
            # Use Requesty.ai if available, otherwise OpenAI directly
            self.embeddings_model = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL
            )
            self.embeddings_provider = "openai"

        self.vector_store_path = settings.VECTOR_STORE_PATH
        os.makedirs(self.vector_store_path, exist_ok=True)
        logger.info(f"DocumentProcessor initialized with chunk_size={chunk_size}")

    def load_document(self, file_path: str) -> List[Document]:
        """Loads a document from a file path using the appropriate loader."""
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        if not self._is_supported_extension(extension):
            raise ValueError(f"Unsupported file type: {extension or '[no extension]'}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Loading document: {file_path} (type: {extension})")

        try:
            # Image files - OCR processing
            if extension in [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"]:
                return self._process_image_with_ocr(file_path)

            # PDF files - enhanced processing
            elif extension == ".pdf":
                if PDF_ADVANCED:
                    return self._process_pdf_advanced(file_path)
                else:
                    loader = PyPDFLoader(file_path)
                    return loader.load()

            # Text files
            elif extension == ".txt":
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
                # Check if the text file contains HTML and clean it if necessary
                for doc in docs:
                    if self._contains_html(doc.page_content):
                        doc.page_content = self._clean_html(doc.page_content)
                        doc.metadata['cleaned_html'] = True
                return docs

            # Word documents
            elif extension == ".docx":
                loader = Docx2txtLoader(file_path)
                return loader.load()

            # PowerPoint files
            elif extension in [".ppt", ".pptx"] and OFFICE_SUPPORT:
                return self._process_powerpoint(file_path)

            # Excel files
            elif extension in [".xls", ".xlsx"] and OFFICE_SUPPORT:
                return self._process_excel(file_path)

            # CSV files
            elif extension == ".csv":
                return self._process_csv(file_path)

            # Markdown files
            elif extension in [".md", ".markdown"]:
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
                for doc in docs:
                    doc.metadata['content_type'] = 'markdown'
                return docs

            # HTML files
            elif extension in [".html", ".htm"]:
                return self._process_html(file_path)

        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            raise

    def _is_supported_extension(self, extension: str) -> bool:
        """Determine whether a file extension is supported by the processor."""
        always_supported = {
            ".txt",
            ".pdf",
            ".docx",
            ".csv",
            ".md",
            ".markdown",
            ".html",
            ".htm",
            ".jpg",
            ".jpeg",
            ".png",
            ".tiff",
            ".bmp",
            ".gif"
        }

        optional_support = {
            ".ppt": OFFICE_SUPPORT,
            ".pptx": OFFICE_SUPPORT,
            ".xls": OFFICE_SUPPORT,
            ".xlsx": OFFICE_SUPPORT
        }

        if extension in always_supported:
            return True

        if extension in optional_support:
            return optional_support[extension]

        return False

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits loaded documents into smaller chunks for processing."""
        logger.info(f"Splitting {len(documents)} documents into chunks")
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks")
        return chunks

    def create_vector_store(self, chunks: List[Document]):
        """Creates or updates the FAISS vector store with document chunks."""
        try:
            if not chunks:
                logger.info("No chunks provided - skipping vector store update")
                return

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
                "message": f"Successfully processed and indexed {file_path}",
                "test_mode": self.test_mode,
                "embedding_provider": self.embeddings_provider
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

    # ===== Multi-modal Document Processing Methods =====

    def _process_image_with_ocr(self, file_path: str) -> List[Document]:
        """Process image files using OCR to extract text."""
        if not OCR_AVAILABLE:
            raise ValueError("OCR not available - install pytesseract, pillow, and opencv-python")

        logger.info(f"Processing image with OCR: {file_path}")

        try:
            # Load and preprocess image
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError(f"Could not load image: {file_path}")

            # Convert to PIL Image for preprocessing
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            # Image preprocessing for better OCR
            processed_image = self._preprocess_image_for_ocr(pil_image)

            # Extract text using OCR
            ocr_text = pytesseract.image_to_string(processed_image)

            # Get additional OCR data for confidence and bounding boxes
            ocr_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)

            # Calculate average confidence
            confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            if not ocr_text.strip():
                logger.warning(f"No text extracted from image: {file_path}")
                ocr_text = f"[Image file: {os.path.basename(file_path)} - No text detected]"

            # Create document with metadata
            document = Document(
                page_content=ocr_text.strip(),
                metadata={
                    "source": file_path,
                    "file_type": "image",
                    "content_type": "ocr_text",
                    "ocr_confidence": avg_confidence,
                    "image_size": f"{pil_image.width}x{pil_image.height}",
                    "processing_method": "pytesseract_ocr"
                }
            )

            logger.info(f"OCR completed: extracted {len(ocr_text)} characters with {avg_confidence:.1f}% confidence")
            return [document]

        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            raise

    def _preprocess_image_for_ocr(self, image: "Image.Image") -> "Image.Image":
        """Preprocess image for better OCR results."""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)

            # Apply slight gaussian blur to reduce noise
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))

            # Resize if image is too small (improves OCR accuracy)
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000/width, 1000/height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {e}")
            return image

    def _process_pdf_advanced(self, file_path: str) -> List[Document]:
        """Process PDF with advanced features including OCR for scanned pages."""
        logger.info(f"Processing PDF with advanced features: {file_path}")

        documents = []
        try:
            pdf_document = fitz.open(file_path)

            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]

                # Try to extract text normally first
                text = page.get_text()

                # If no text found or very little text, try OCR
                if len(text.strip()) < 50 and OCR_AVAILABLE:
                    logger.info(f"Page {page_num + 1} appears to be scanned, applying OCR")

                    # Render page as image
                    mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")

                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(img_data))

                    # Preprocess and OCR
                    processed_image = self._preprocess_image_for_ocr(pil_image)
                    ocr_text = pytesseract.image_to_string(processed_image)

                    if ocr_text.strip():
                        text = ocr_text
                        content_type = "pdf_ocr"
                    else:
                        text = f"[Page {page_num + 1}: Scanned page with no extractable text]"
                        content_type = "pdf_scanned"
                else:
                    content_type = "pdf_text"

                if text.strip():
                    document = Document(
                        page_content=text.strip(),
                        metadata={
                            "source": file_path,
                            "page": page_num + 1,
                            "file_type": "pdf",
                            "content_type": content_type,
                            "total_pages": pdf_document.page_count
                        }
                    )
                    documents.append(document)

            pdf_document.close()
            logger.info(f"Successfully processed PDF: {len(documents)} pages extracted")
            return documents

        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            # Fallback to basic PDF loader
            loader = PyPDFLoader(file_path)
            return loader.load()

    def _process_powerpoint(self, file_path: str) -> List[Document]:
        """Process PowerPoint files."""
        logger.info(f"Processing PowerPoint file: {file_path}")

        try:
            loader = UnstructuredPowerPointLoader(file_path)
            documents = loader.load()

            # Enhance metadata
            for i, doc in enumerate(documents):
                doc.metadata.update({
                    "file_type": "powerpoint",
                    "content_type": "presentation",
                    "slide_number": i + 1,
                    "total_slides": len(documents)
                })

            return documents

        except Exception as e:
            logger.error(f"Error processing PowerPoint {file_path}: {e}")
            raise

    def _process_excel(self, file_path: str) -> List[Document]:
        """Process Excel files."""
        logger.info(f"Processing Excel file: {file_path}")

        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            documents = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # Convert dataframe to text representation
                if not df.empty:
                    # Create a summary of the sheet
                    sheet_text = f"Sheet: {sheet_name}\n"
                    sheet_text += f"Dimensions: {df.shape[0]} rows x {df.shape[1]} columns\n\n"

                    # Add column headers
                    sheet_text += "Columns: " + ", ".join(df.columns.astype(str)) + "\n\n"

                    # Add sample data (first 10 rows)
                    sheet_text += "Sample Data:\n"
                    sheet_text += df.head(10).to_string(index=False)

                    # Add summary statistics for numeric columns
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        sheet_text += "\n\nNumeric Summary:\n"
                        sheet_text += df[numeric_cols].describe().to_string()

                    document = Document(
                        page_content=sheet_text,
                        metadata={
                            "source": file_path,
                            "sheet_name": sheet_name,
                            "file_type": "excel",
                            "content_type": "spreadsheet",
                            "rows": df.shape[0],
                            "columns": df.shape[1]
                        }
                    )
                    documents.append(document)

            return documents

        except Exception as e:
            logger.error(f"Error processing Excel {file_path}: {e}")
            raise

    def _process_csv(self, file_path: str) -> List[Document]:
        """Process CSV files."""
        logger.info(f"Processing CSV file: {file_path}")

        try:
            df = pd.read_csv(file_path)

            if df.empty:
                return [Document(
                    page_content=f"Empty CSV file: {os.path.basename(file_path)}",
                    metadata={"source": file_path, "file_type": "csv", "content_type": "empty"}
                )]

            # Create text representation
            csv_text = f"CSV File: {os.path.basename(file_path)}\n"
            csv_text += f"Dimensions: {df.shape[0]} rows x {df.shape[1]} columns\n\n"

            # Add column information
            csv_text += "Columns: " + ", ".join(df.columns.astype(str)) + "\n\n"

            # Add sample data
            csv_text += "Sample Data (first 20 rows):\n"
            csv_text += df.head(20).to_string(index=False)

            # Add summary statistics
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                csv_text += "\n\nNumeric Summary:\n"
                csv_text += df[numeric_cols].describe().to_string()

            document = Document(
                page_content=csv_text,
                metadata={
                    "source": file_path,
                    "file_type": "csv",
                    "content_type": "structured_data",
                    "rows": df.shape[0],
                    "columns": df.shape[1]
                }
            )

            return [document]

        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {e}")
            raise

    def _process_html(self, file_path: str) -> List[Document]:
        """Process HTML files."""
        logger.info(f"Processing HTML file: {file_path}")

        if not BS4_AVAILABLE or BeautifulSoup is None:
            logger.error("BeautifulSoup not available for HTML processing")
            return self._load_raw_html(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            # Parse HTML and extract text
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # Extract title if available
            title = soup.title.string if soup.title else os.path.basename(file_path)

            document = Document(
                page_content=text,
                metadata={
                    "source": file_path,
                    "file_type": "html",
                    "content_type": "web_page",
                    "title": title
                }
            )

            return [document]

        except Exception as e:
            logger.error(f"Error processing HTML {file_path}: {e}")
            raise

    def _load_raw_html(self, file_path: str) -> List[Document]:
        """Fallback HTML processing that returns raw content."""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        document = Document(
            page_content=content,
            metadata={
                "source": file_path,
                "file_type": "html",
                "content_type": "raw_html"
            }
        )
        return [document]

    def _contains_html(self, text: str) -> bool:
        """Check if text contains HTML markup."""
        import re
        # Look for common HTML tags
        html_pattern = r'<\s*(html|head|body|div|table|tr|td|th|h[1-6]|p|span|style|script)'
        return bool(re.search(html_pattern, text, re.IGNORECASE))

    def _clean_html(self, text: str) -> str:
        """Clean HTML content from text, preserving important information."""
        if BS4_AVAILABLE and BeautifulSoup is not None:
            try:
                soup = BeautifulSoup(text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract text
                cleaned_text = soup.get_text()
                
                # Clean up whitespace while preserving line breaks
                lines = [line.strip() for line in cleaned_text.splitlines() if line.strip()]
                cleaned_text = '\n'.join(lines)
                
                logger.info("HTML content cleaned using BeautifulSoup")
                return cleaned_text
            except Exception as e:
                logger.warning(f"Failed to clean HTML with BeautifulSoup: {e}, using regex fallback")
        
        # Fallback: use regex to strip HTML tags
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        logger.info("HTML content cleaned using regex fallback")
        return text.strip()

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get all supported file formats organized by category."""
        formats = {
            "text": [".txt", ".md", ".markdown"],
            "documents": [".pdf", ".docx"],
            "images": [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"] if OCR_AVAILABLE else [],
            "web": [".html", ".htm"],
            "data": [".csv"]
        }

        if OFFICE_SUPPORT:
            formats["presentations"] = [".ppt", ".pptx"]
            formats["spreadsheets"] = [".xls", ".xlsx"]

        # Flatten for total count
        all_formats = []
        for category_formats in formats.values():
            all_formats.extend(category_formats)

        return {
            "categories": formats,
            "all_formats": all_formats,
            "total_supported": len(all_formats),
            "ocr_available": OCR_AVAILABLE,
            "pdf_advanced": PDF_ADVANCED,
            "office_support": OFFICE_SUPPORT
        }