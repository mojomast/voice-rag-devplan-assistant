"""
Script to fix HTML in documents by:
1. Installing BeautifulSoup4 if needed
2. Re-indexing all documents with HTML cleaning
"""

import os
import subprocess
import sys
from pathlib import Path

def install_beautifulsoup():
    """Install BeautifulSoup4"""
    print("Installing BeautifulSoup4...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
        print("✅ BeautifulSoup4 installed successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to install BeautifulSoup4: {e}")
        return False

def reindex_documents():
    """Re-index all documents"""
    print("\nRe-indexing documents with HTML cleaning...")
    
    try:
        from document_processor import DocumentProcessor
        from config import settings
        
        # Clear existing vector store
        vector_store_path = settings.VECTOR_STORE_PATH
        if os.path.exists(vector_store_path):
            import shutil
            print(f"Clearing existing vector store at {vector_store_path}")
            shutil.rmtree(vector_store_path)
            os.makedirs(vector_store_path)
        
        # Re-index all files
        processor = DocumentProcessor()
        uploads_path = settings.UPLOAD_PATH
        
        if not os.path.exists(uploads_path):
            print(f"❌ Upload folder not found: {uploads_path}")
            return False
        
        files = list(Path(uploads_path).rglob("*.*"))
        if not files:
            print(f"❌ No files found in {uploads_path}")
            return False
        
        print(f"\nFound {len(files)} file(s) to process:")
        for file in files:
            print(f"  - {file.name}")
        
        print("\nProcessing files...")
        success_count = 0
        for file_path in files:
            try:
                result = processor.process_and_index_file(str(file_path))
                if result["status"] == "success":
                    print(f"✅ {file_path.name}: {result.get('chunks_created', 0)} chunks created")
                    success_count += 1
                else:
                    print(f"❌ {file_path.name}: Failed")
            except Exception as e:
                print(f"❌ {file_path.name}: {e}")
        
        print(f"\n✅ Successfully re-indexed {success_count}/{len(files)} files")
        return True
        
    except Exception as e:
        print(f"❌ Re-indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("HTML Document Cleanup Script")
    print("=" * 60)
    
    # Step 1: Install BeautifulSoup4
    if install_beautifulsoup():
        # Step 2: Re-index documents
        if reindex_documents():
            print("\n" + "=" * 60)
            print("✅ All done! Please restart your backend server.")
            print("=" * 60)
        else:
            print("\n❌ Re-indexing failed. Please check the errors above.")
    else:
        print("\n❌ Installation failed. Please install manually:")
        print("pip install beautifulsoup4")
