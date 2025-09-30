import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any, List
import time
import os

# Configuration
API_BASE_URL = st.secrets.get("API_URL", "http://localhost:8000")

def main():
    st.set_page_config(
        page_title="📚 Multi-Modal Document Manager",
        page_icon="📚",
        layout="wide"
    )

    st.title("📚 Multi-Modal Document Manager")
    st.markdown("**Advanced document processing with OCR, image analysis, and multi-format support**")

    # Sidebar with supported formats and features
    with st.sidebar:
        st.header("🔧 Features & Formats")
        display_supported_formats()

        st.markdown("---")

        st.header("⚙️ Processing Options")
        enable_ocr = st.checkbox("🔍 Enable OCR for images", value=True)
        enable_advanced_pdf = st.checkbox("📄 Advanced PDF processing", value=True)
        chunk_optimization = st.selectbox(
            "📝 Text chunking strategy",
            ["balanced", "detailed", "summary"],
            index=0
        )

    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload Documents",
        "📊 Document Analysis",
        "🔍 Search & Query",
        "📈 Processing Insights"
    ])

    with tab1:
        render_upload_interface(enable_ocr, enable_advanced_pdf, chunk_optimization)

    with tab2:
        render_document_analysis()

    with tab3:
        render_search_interface()

    with tab4:
        render_processing_insights()

def display_supported_formats():
    """Display supported file formats from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/supported-formats", timeout=5)
        if response.status_code == 200:
            formats_data = response.json()

            st.subheader("📋 Supported Formats")

            # Display by category
            for category, formats in formats_data["categories"].items():
                if formats:  # Only show categories with formats
                    st.markdown(f"**{category.title()}:**")
                    format_string = ", ".join(formats)
                    st.markdown(f"_{format_string}_")

            # Feature availability
            st.markdown("---")
            st.subheader("🚀 Available Features")

            features = [
                ("OCR Processing", formats_data.get("ocr_available", False)),
                ("Advanced PDF", formats_data.get("pdf_advanced", False)),
                ("Office Support", formats_data.get("office_support", False))
            ]

            for feature, available in features:
                status = "✅" if available else "❌"
                st.markdown(f"{status} {feature}")

            st.metric("Total Formats", formats_data.get("total_supported", 0))

        else:
            st.error("Could not load supported formats")
    except:
        st.warning("Backend unavailable - showing basic formats")
        st.markdown("**Basic Support:** PDF, TXT, DOCX, Images")

def render_upload_interface(enable_ocr: bool, enable_advanced_pdf: bool, chunk_optimization: str):
    st.header("📤 Document Upload & Processing")

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to process",
        accept_multiple_files=True,
        type=None,  # Allow all types, we'll validate server-side
        help="Upload documents, images, spreadsheets, presentations, and more"
    )

    if uploaded_files:
        st.subheader(f"📁 Selected Files ({len(uploaded_files)})")

        # Display file preview
        files_data = []
        for file in uploaded_files:
            file_info = {
                "Name": file.name,
                "Type": file.type if file.type else "Unknown",
                "Size": f"{file.size / 1024:.1f} KB" if file.size else "Unknown"
            }
            files_data.append(file_info)

        df = pd.DataFrame(files_data)
        st.dataframe(df, use_container_width=True)

        # Processing options
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚀 Process All Files", type="primary"):
                process_multiple_files(uploaded_files, enable_ocr, enable_advanced_pdf, chunk_optimization)

        with col2:
            if st.button("🔍 Analyze File Types"):
                analyze_file_types(uploaded_files)

    # Recent uploads
    st.subheader("📚 Recent Documents")
    display_document_stats()

def process_multiple_files(files: List, enable_ocr: bool, enable_advanced_pdf: bool, chunk_optimization: str):
    """Process multiple uploaded files."""

    progress_bar = st.progress(0)
    status_container = st.container()
    results_container = st.container()

    total_files = len(files)
    processed_files = 0
    successful_uploads = []
    failed_uploads = []

    for i, file in enumerate(files):
        with status_container:
            st.info(f"Processing: {file.name} ({i+1}/{total_files})")

        try:
            # Prepare file for upload
            files_payload = {"file": (file.name, file.getvalue(), file.type)}

            # Upload to backend
            response = requests.post(
                f"{API_BASE_URL}/documents/upload",
                files=files_payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                successful_uploads.append({
                    "file": file.name,
                    "chunks": result.get("chunk_count", 0),
                    "status": result.get("status", "success")
                })
                st.success(f"✅ {file.name} processed successfully")
            else:
                failed_uploads.append({
                    "file": file.name,
                    "error": f"HTTP {response.status_code}"
                })
                st.error(f"❌ Failed to process {file.name}")

        except Exception as e:
            failed_uploads.append({
                "file": file.name,
                "error": str(e)
            })
            st.error(f"❌ Error processing {file.name}: {e}")

        processed_files += 1
        progress_bar.progress(processed_files / total_files)
        time.sleep(0.1)  # Small delay for UI responsiveness

    # Display results summary
    with results_container:
        st.markdown("---")
        st.subheader("📊 Processing Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Files", total_files)
        with col2:
            st.metric("Successful", len(successful_uploads))
        with col3:
            st.metric("Failed", len(failed_uploads))

        if successful_uploads:
            st.success("✅ Successfully Processed:")
            success_df = pd.DataFrame(successful_uploads)
            st.dataframe(success_df, use_container_width=True)

        if failed_uploads:
            st.error("❌ Failed to Process:")
            failed_df = pd.DataFrame(failed_uploads)
            st.dataframe(failed_df, use_container_width=True)

def analyze_file_types(files: List):
    """Analyze the types of uploaded files."""

    file_analysis = {}

    for file in files:
        extension = os.path.splitext(file.name)[1].lower()
        file_type = get_file_category(extension)

        if file_type not in file_analysis:
            file_analysis[file_type] = {
                "count": 0,
                "total_size": 0,
                "files": []
            }

        file_analysis[file_type]["count"] += 1
        file_analysis[file_type]["total_size"] += file.size or 0
        file_analysis[file_type]["files"].append(file.name)

    st.subheader("📊 File Type Analysis")

    # Summary metrics
    cols = st.columns(len(file_analysis))
    for i, (file_type, data) in enumerate(file_analysis.items()):
        with cols[i]:
            st.metric(
                f"{file_type.title()} Files",
                data["count"],
                delta=f"{data['total_size'] / 1024:.1f} KB"
            )

    # Detailed breakdown
    for file_type, data in file_analysis.items():
        with st.expander(f"📁 {file_type.title()} Files ({data['count']})"):
            st.write("**Files:**")
            for filename in data["files"]:
                st.write(f"- {filename}")

            processing_note = get_processing_info(file_type)
            if processing_note:
                st.info(f"**Processing:** {processing_note}")

def get_file_category(extension: str) -> str:
    """Categorize file by extension."""
    categories = {
        'document': ['.pdf', '.docx', '.doc', '.txt', '.md'],
        'image': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'],
        'spreadsheet': ['.xlsx', '.xls', '.csv'],
        'presentation': ['.pptx', '.ppt'],
        'web': ['.html', '.htm'],
        'other': []
    }

    for category, extensions in categories.items():
        if extension in extensions:
            return category

    return 'other'

def get_processing_info(file_type: str) -> str:
    """Get processing information for file type."""
    info = {
        'document': "Text extraction with smart chunking",
        'image': "OCR text extraction with preprocessing",
        'spreadsheet': "Data analysis and summary generation",
        'presentation': "Slide content and structure extraction",
        'web': "HTML parsing and text cleaning",
        'other': "Format detection and best-effort processing"
    }
    return info.get(file_type, "Standard text processing")

def render_document_analysis():
    st.header("📊 Document Analysis & Insights")

    # Get document statistics
    try:
        response = requests.get(f"{API_BASE_URL}/documents/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()

            if stats.get("exists", False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Documents Indexed", stats.get("document_count", 0))
                with col2:
                    index_size_mb = stats.get("index_size", 0) / (1024 * 1024)
                    st.metric("Index Size", f"{index_size_mb:.2f} MB")
                with col3:
                    # Estimate based on typical chunk size
                    est_chunks = stats.get("document_count", 0) * 3
                    st.metric("Estimated Chunks", est_chunks)

                # Document type breakdown (mock data for demo)
                st.subheader("📈 Document Type Distribution")

                # Mock data - in real implementation, this would come from metadata
                doc_types = {
                    "PDF Documents": 45,
                    "Text Files": 23,
                    "Images (OCR)": 12,
                    "Spreadsheets": 8,
                    "Presentations": 5,
                    "Web Pages": 3,
                    "Other": 4
                }

                # Create a simple bar chart using native Streamlit
                chart_data = pd.DataFrame(
                    list(doc_types.items()),
                    columns=["Document Type", "Count"]
                )
                st.bar_chart(chart_data.set_index("Document Type"))

                # Processing insights
                st.subheader("🔍 Processing Insights")

                insights = [
                    "📄 PDF processing includes OCR for scanned documents",
                    "🖼️ Image files are processed with advanced OCR preprocessing",
                    "📊 Spreadsheets include data summaries and column analysis",
                    "🎨 Presentations extract slide content and structure",
                    "🌐 Web pages have scripts and styles filtered out"
                ]

                for insight in insights:
                    st.markdown(f"- {insight}")

            else:
                st.info("No documents have been indexed yet. Upload some documents to see analysis.")
        else:
            st.error("Unable to fetch document statistics")
    except:
        st.error("Backend connection failed")

def render_search_interface():
    st.header("🔍 Advanced Search & Query")

    # Search options
    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_area(
            "Enter your question or search query:",
            placeholder="e.g., What are the key findings in the research documents? Or search for specific terms...",
            height=100
        )

    with col2:
        st.subheader("🎛️ Search Options")
        search_mode = st.radio(
            "Search Mode",
            ["semantic", "keyword", "hybrid"],
            help="Semantic: AI-powered meaning search\nKeyword: Exact term matching\nHybrid: Combination of both"
        )

        max_results = st.slider("Max Results", 1, 20, 5)
        include_metadata = st.checkbox("Include Source Info", value=True)

    if st.button("🔍 Search", type="primary") and query.strip():
        search_documents(query, search_mode, max_results, include_metadata)

def search_documents(query: str, mode: str, max_results: int, include_metadata: bool):
    """Perform document search."""

    with st.spinner("🔍 Searching documents..."):
        try:
            payload = {
                "query": query,
                "include_sources": include_metadata
            }

            response = requests.post(
                f"{API_BASE_URL}/query/text",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                st.subheader("🎯 Search Results")

                # Display answer
                st.markdown("**Answer:**")
                st.write(result.get("answer", "No answer generated"))

                # Display sources if available
                if include_metadata and result.get("sources"):
                    st.subheader("📚 Sources")

                    for i, source in enumerate(result["sources"][:max_results]):
                        with st.expander(f"Source {i+1}: {source.get('source', 'Unknown')}"):
                            st.write(f"**Content:** {source.get('content', 'No content')}")

                            # Metadata
                            metadata = source.get('metadata', {})
                            if metadata:
                                st.write("**Metadata:**")
                                for key, value in metadata.items():
                                    if key not in ['content']:  # Skip content as it's shown above
                                        st.write(f"- {key}: {value}")

            else:
                st.error(f"Search failed: HTTP {response.status_code}")

        except Exception as e:
            st.error(f"Search error: {e}")

def render_processing_insights():
    st.header("📈 Processing Insights & Statistics")

    # Mock processing statistics
    st.subheader("⚡ Processing Performance")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Avg Processing Time", "2.3s", delta="-0.5s")
    with col2:
        st.metric("OCR Accuracy", "94.2%", delta="1.8%")
    with col3:
        st.metric("Chunk Quality", "8.7/10", delta="0.3")
    with col4:
        st.metric("Error Rate", "1.2%", delta="-0.8%")

    # Processing methods breakdown
    st.subheader("🔧 Processing Methods Used")

    methods_data = {
        "Standard Text Extraction": 65,
        "OCR Processing": 20,
        "Advanced PDF Analysis": 10,
        "Structured Data Parsing": 5
    }

    chart_data = pd.DataFrame(
        list(methods_data.items()),
        columns=["Method", "Percentage"]
    )
    st.bar_chart(chart_data.set_index("Method"))

    # Recent processing logs
    st.subheader("📜 Recent Processing Activity")

    # Mock log data
    recent_logs = [
        {"Time": "10:35:42", "File": "research_paper.pdf", "Method": "Advanced PDF", "Status": "✅ Success", "Chunks": 12},
        {"Time": "10:34:15", "File": "scanned_doc.png", "Method": "OCR", "Status": "✅ Success", "Chunks": 3},
        {"Time": "10:33:08", "File": "data_sheet.xlsx", "Method": "Structured Parsing", "Status": "✅ Success", "Chunks": 8},
        {"Time": "10:32:44", "File": "presentation.pptx", "Method": "Text Extraction", "Status": "⚠️ Partial", "Chunks": 15},
        {"Time": "10:31:22", "File": "webpage.html", "Method": "HTML Parsing", "Status": "✅ Success", "Chunks": 6},
    ]

    logs_df = pd.DataFrame(recent_logs)
    st.dataframe(logs_df, use_container_width=True)

def display_document_stats():
    """Display current document statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()

            if stats.get("exists", False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Documents", stats.get("document_count", 0))
                with col2:
                    st.metric("Index Size", f"{stats.get('index_size', 0) / 1024:.1f} KB")
            else:
                st.info("No documents indexed yet")
    except:
        st.warning("Unable to fetch document statistics")

if __name__ == "__main__":
    main()