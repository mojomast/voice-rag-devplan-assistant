#!/usr/bin/env python3
"""
Simple script to check if test dependencies are installed.
"""

import sys
import subprocess

def check_dependency(dependency):
    """Check if a dependency is installed."""
    try:
        result = subprocess.run([sys.executable, "-c", f"import {dependency}"],
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

def main():
    """Check test dependencies."""
    print("Checking test dependencies...")
    
    dependencies = [
        "pytest",
        "pytest_cov", 
        "pytest_mock",
        "pytest_asyncio",
        "httpx",
        "responses",
        "factory_boy",
        "faker",
        "pytest_benchmark",
        "pytest_xdist",
        "bandit",
        "safety"
    ]
    
    results = []
    for dep in dependencies:
        status = "✅" if check_dependency(dep) else "❌"
        print(f"{status} {dep}")
        results.append(check_dependency(dep))
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nSummary: {passed}/{total} dependencies available")
    
    if passed == total:
        print("🎉 All test dependencies are installed!")
        return 0
    else:
        print("⚠️ Some dependencies are missing")
        return 1

if __name__ == "__main__":
    sys.exit(main())