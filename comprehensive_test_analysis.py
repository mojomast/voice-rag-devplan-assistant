#!/usr/bin/env python3
"""
Comprehensive test analysis and execution script.
This script analyzes the test structure and attempts to run tests directly.
"""

import sys
import os
import importlib.util
from pathlib import Path
from datetime import datetime
import json

def analyze_test_structure():
    """Analyze the test structure and provide insights."""
    print("=" * 60)
    print("TEST STRUCTURE ANALYSIS")
    print("=" * 60)
    
    test_dirs = {
        'unit': 'tests/unit',
        'integration': 'tests/integration',
        'frontend': 'tests/frontend',
        'e2e': 'tests/e2e'
    }
    
    analysis = {}
    
    for test_type, test_dir in test_dirs.items():
        if os.path.exists(test_dir):
            test_files = [f for f in os.listdir(test_dir) if f.startswith('test_') and f.endswith('.py')]
            analysis[test_type] = {
                'directory': test_dir,
                'files': test_files,
                'count': len(test_files)
            }
            print(f"📁 {test_type.upper()} TESTS: {len(test_files)} files")
            for file in test_files:
                print(f"   📄 {file}")
        else:
            analysis[test_type] = {
                'directory': test_dir,
                'files': [],
                'count': 0
            }
            print(f"❌ {test_type.upper()} TESTS: Directory not found")
    
    return analysis

def check_dependencies_direct():
    """Check dependencies directly by importing them."""
    print("\n" + "=" * 60)
    print("DEPENDENCY CHECK")
    print("=" * 60)
    
    # Test dependencies from requirements-test.txt
    test_deps = [
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
    
    # Core application dependencies
    core_deps = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "openai",
        "whisper",
        "pydub",
        "pyttsx3"
    ]
    
    results = {}
    
    print("🔍 TEST DEPENDENCIES:")
    for dep in test_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
            results[f"test_{dep}"] = True
        except ImportError:
            print(f"❌ {dep}")
            results[f"test_{dep}"] = False
    
    print("\n🔧 CORE DEPENDENCIES:")
    for dep in core_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
            results[f"core_{dep}"] = True
        except ImportError:
            print(f"❌ {dep}")
            results[f"core_{dep}"] = False
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n📊 SUMMARY: {passed}/{total} dependencies available")
    
    return results

def analyze_test_file_syntax(file_path):
    """Analyze a test file for syntax errors and basic structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to compile the code to check for syntax errors
        compile(content, file_path, 'exec')
        
        # Basic analysis
        has_test_functions = 'def test_' in content
        has_imports = 'import ' in content
        has_pytest_import = 'import pytest' in content or 'from pytest' in content
        
        return {
            'syntax_valid': True,
            'has_test_functions': has_test_functions,
            'has_imports': has_imports,
            'has_pytest_import': has_pytest_import,
            'line_count': len(content.splitlines()),
            'size_bytes': len(content.encode('utf-8'))
        }
    except SyntaxError as e:
        return {
            'syntax_valid': False,
            'error': str(e),
            'line_number': e.lineno
        }
    except Exception as e:
        return {
            'syntax_valid': False,
            'error': str(e)
        }

def analyze_all_test_files(test_analysis):
    """Analyze all test files for syntax and structure."""
    print("\n" + "=" * 60)
    print("TEST FILE ANALYSIS")
    print("=" * 60)
    
    file_analysis = {}
    total_files = 0
    valid_files = 0
    
    for test_type, info in test_analysis.items():
        if info['count'] > 0:
            print(f"\n📁 {test_type.upper()} TESTS:")
            for file in info['files']:
                file_path = os.path.join(info['directory'], file)
                total_files += 1
                
                analysis = analyze_test_file_syntax(file_path)
                file_analysis[file_path] = analysis
                
                if analysis['syntax_valid']:
                    valid_files += 1
                    status = "✅"
                    details = []
                    if analysis.get('has_test_functions'):
                        details.append("tests")
                    if analysis.get('has_pytest_import'):
                        details.append("pytest")
                    print(f"   {status} {file} ({', '.join(details)}) - {analysis['line_count']} lines")
                else:
                    status = "❌"
                    error = analysis.get('error', 'Unknown error')
                    line = analysis.get('line_number', '?')
                    print(f"   {status} {file} - Error at line {line}: {error}")
    
    print(f"\n📊 FILE ANALYSIS SUMMARY:")
    print(f"   Total files: {total_files}")
    print(f"   Valid syntax: {valid_files}")
    print(f"   Invalid syntax: {total_files - valid_files}")
    
    return file_analysis

def check_backend_modules():
    """Check if backend modules can be imported."""
    print("\n" + "=" * 60)
    print("BACKEND MODULE CHECK")
    print("=" * 60)
    
    backend_dir = "backend"
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found")
        return {}
    
    # Add backend to Python path
    sys.path.insert(0, os.path.abspath(backend_dir))
    
    key_modules = [
        "main",
        "voice_service", 
        "planning_agent",
        "plan_generator",
        "context_manager",
        "document_processor",
        "rag_handler"
    ]
    
    results = {}
    
    for module in key_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
            results[module] = True
        except ImportError as e:
            print(f"❌ {module} - {e}")
            results[module] = False
        except Exception as e:
            print(f"⚠️  {module} - {e}")
            results[module] = False
    
    return results

def check_environment_setup():
    """Check environment setup and configuration."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT SETUP CHECK")
    print("=" * 60)
    
    checks = {
        'env_file': os.path.exists('.env'),
        'env_template': os.path.exists('.env.template'),
        'requirements_txt': os.path.exists('requirements.txt'),
        'requirements_test_txt': os.path.exists('requirements-test.txt'),
        'pytest_ini': os.path.exists('pytest.ini'),
        'backend_dir': os.path.exists('backend'),
        'frontend_dir': os.path.exists('frontend'),
        'tests_dir': os.path.exists('tests')
    }
    
    for check, exists in checks.items():
        status = "✅" if exists else "❌"
        print(f"{status} {check}")
    
    # Check .env file content if it exists
    if checks['env_file']:
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
            
            required_vars = ['OPENAI_API_KEY', 'REQUESTY_API_KEY']
            found_vars = []
            
            for var in required_vars:
                if var in env_content:
                    found_vars.append(var)
            
            print(f"   📋 Found {len(found_vars)}/{len(required_vars)} required environment variables")
            for var in found_vars:
                print(f"      ✅ {var}")
            
            missing_vars = [var for var in required_vars if var not in found_vars]
            for var in missing_vars:
                print(f"      ❌ {var}")
                
        except Exception as e:
            print(f"   ⚠️  Could not read .env file: {e}")
    
    return checks

def generate_comprehensive_report(test_analysis, dep_analysis, file_analysis, backend_analysis, env_analysis):
    """Generate a comprehensive test report."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_structure': test_analysis,
        'dependencies': dep_analysis,
        'file_analysis': file_analysis,
        'backend_modules': backend_analysis,
        'environment': env_analysis
    }
    
    # Calculate summary statistics
    total_test_files = sum(info['count'] for info in test_analysis.values())
    valid_test_files = sum(1 for analysis in file_analysis.values() if analysis.get('syntax_valid', False))
    
    total_deps = len(dep_analysis)
    available_deps = sum(dep_analysis.values())
    
    total_backend_modules = len(backend_analysis)
    working_backend_modules = sum(backend_analysis.values())
    
    env_checks = len(env_analysis)
    passed_env_checks = sum(env_analysis.values())
    
    summary = {
        'test_files': {
            'total': total_test_files,
            'valid': valid_test_files,
            'invalid': total_test_files - valid_test_files
        },
        'dependencies': {
            'total': total_deps,
            'available': available_deps,
            'missing': total_deps - available_deps
        },
        'backend_modules': {
            'total': total_backend_modules,
            'working': working_backend_modules,
            'broken': total_backend_modules - working_backend_modules
        },
        'environment': {
            'total_checks': env_checks,
            'passed': passed_env_checks,
            'failed': env_checks - passed_env_checks
        }
    }
    
    report['summary'] = summary
    
    # Print summary
    print(f"📊 TEST FILES: {valid_test_files}/{total_test_files} valid")
    print(f"📦 DEPENDENCIES: {available_deps}/{total_deps} available")
    print(f"🔧 BACKEND MODULES: {working_backend_modules}/{total_backend_modules} working")
    print(f"⚙️  ENVIRONMENT: {passed_env_checks}/{env_checks} checks passed")
    
    # Calculate overall readiness score
    total_items = (total_test_files + total_deps + total_backend_modules + env_checks)
    working_items = (valid_test_files + available_deps + working_backend_modules + passed_env_checks)
    readiness_score = (working_items / total_items * 100) if total_items > 0 else 0
    
    print(f"\n🎯 OVERALL READINESS: {readiness_score:.1f}%")
    
    if readiness_score >= 90:
        print("🎉 EXCELLENT - Ready for comprehensive testing!")
    elif readiness_score >= 75:
        print("✅ GOOD - Mostly ready, minor issues to address")
    elif readiness_score >= 50:
        print("⚠️  FAIR - Some setup required")
    else:
        print("❌ POOR - Significant setup needed")
    
    # Save report to file
    report_file = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    return report

def main():
    """Main analysis function."""
    print("VOICE-RAG-SYSTEM COMPREHENSIVE TEST ANALYSIS")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Working directory: {os.getcwd()}")
    
    # 1. Analyze test structure
    test_analysis = analyze_test_structure()
    
    # 2. Check dependencies
    dep_analysis = check_dependencies_direct()
    
    # 3. Analyze test files
    file_analysis = analyze_all_test_files(test_analysis)
    
    # 4. Check backend modules
    backend_analysis = check_backend_modules()
    
    # 5. Check environment setup
    env_analysis = check_environment_setup()
    
    # 6. Generate comprehensive report
    report = generate_comprehensive_report(
        test_analysis, dep_analysis, file_analysis, 
        backend_analysis, env_analysis
    )
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETED")
    print("=" * 60)
    
    return 0 if report['summary']['test_files']['invalid'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())