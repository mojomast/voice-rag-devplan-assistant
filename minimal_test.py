#!/usr/bin/env python3
"""
Minimal test to check basic functionality.
"""

import sys
import os

def main():
    print("VOICE-RAG-SYSTEM MINIMAL TEST")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Check basic dependencies
    print("\nChecking basic dependencies:")
    deps = ["sys", "os", "json", "datetime"]
    for dep in deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
    
    # Check if key files exist
    print("\nChecking key files:")
    key_files = [
        "requirements-test.txt",
        "test_dependencies.py", 
        "test_phase4.py",
        "tests/",
        "backend/"
    ]
    
    for file in key_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
    
    # Try to import pytest
    print("\nChecking pytest:")
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__}")
    except ImportError:
        print("❌ pytest not available")
    
    print("\nMinimal test completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())