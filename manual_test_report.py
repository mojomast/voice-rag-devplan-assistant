#!/usr/bin/env python3
"""
Manual test report generation without subprocess calls.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

def main():
    """Generate manual test report."""
    print("VOICE-RAG-SYSTEM MANUAL TEST REPORT")
    print(f"Generated at: {datetime.now().isoformat()}")
    print(f"Working directory: {os.getcwd()}")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'working_directory': os.getcwd(),
        'analysis': {},
        'summary': {}
    }
    
    # 1. Environment Setup Check
    print("\n" + "=" * 60)
    print("ENVIRONMENT SETUP ANALYSIS")
    print("=" * 60)
    
    env_checks = {
        'env_file': os.path.exists('.env'),
        'env_template': os.path.exists('.env.template'),
        'requirements_txt': os.path.exists('requirements.txt'),
        'requirements_test_txt': os.path.exists('requirements-test.txt'),
        'pytest_ini': os.path.exists('pytest.ini'),
        'backend_dir': os.path.exists('backend'),
        'frontend_dir': os.path.exists('frontend'),
        'tests_dir': os.path.exists('tests')
    }
    
    for check, exists in env_checks.items():
        status = "✅" if exists else "❌"
        print(f"{status} {check}")
    
    report['analysis']['environment'] = env_checks
    
    # 2. Test Structure Analysis
    print("\n" + "=" * 60)
    print("TEST STRUCTURE ANALYSIS")
    print("=" * 60)
    
    test_structure = {}
    total_test_files = 0
    
    if os.path.exists('tests'):
        for test_type in ['unit', 'integration', 'frontend', 'e2e']:
            test_dir = f"tests/{test_type}"
            if os.path.exists(test_dir):
                test_files = [f for f in os.listdir(test_dir) if f.startswith('test_') and f.endswith('.py')]
                test_structure[test_type] = {
                    'directory': test_dir,
                    'files': test_files,
                    'count': len(test_files)
                }
                total_test_files += len(test_files)
                print(f"📁 {test_type.upper()}: {len(test_files)} files")
                for file in test_files:
                    print(f"   📄 {file}")
            else:
                test_structure[test_type] = {'directory': test_dir, 'files': [], 'count': 0}
                print(f"❌ {test_type.upper()}: Directory not found")
    
    report['analysis']['test_structure'] = test_structure
    
    # 3. Dependency Analysis
    print("\n" + "=" * 60)
    print("DEPENDENCY ANALYSIS")
    print("=" * 60)
    
    # Test dependencies
    test_deps = [
        "pytest", "pytest_cov", "pytest_mock", "pytest_asyncio",
        "httpx", "responses", "factory_boy", "faker",
        "pytest_benchmark", "pytest_xdist", "bandit", "safety"
    ]
    
    # Core dependencies
    core_deps = [
        "fastapi", "uvicorn", "sqlalchemy", "openai", 
        "whisper", "pydub", "pyttsx3"
    ]
    
    dep_results = {}
    
    print("🔍 TEST DEPENDENCIES:")
    for dep in test_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
            dep_results[f"test_{dep}"] = True
        except ImportError:
            print(f"❌ {dep}")
            dep_results[f"test_{dep}"] = False
    
    print("\n🔧 CORE DEPENDENCIES:")
    for dep in core_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
            dep_results[f"core_{dep}"] = True
        except ImportError:
            print(f"❌ {dep}")
            dep_results[f"core_{dep}"] = False
    
    report['analysis']['dependencies'] = dep_results
    
    # 4. Backend Module Analysis
    print("\n" + "=" * 60)
    print("BACKEND MODULE ANALYSIS")
    print("=" * 60)
    
    backend_modules = {}
    if os.path.exists('backend'):
        sys.path.insert(0, os.path.abspath('backend'))
        
        key_modules = [
            "main", "voice_service", "planning_agent", "plan_generator",
            "context_manager", "document_processor", "rag_handler"
        ]
        
        for module in key_modules:
            try:
                __import__(module)
                print(f"✅ {module}")
                backend_modules[module] = True
            except ImportError as e:
                print(f"❌ {module} - {e}")
                backend_modules[module] = False
            except Exception as e:
                print(f"⚠️  {module} - {e}")
                backend_modules[module] = False
    
    report['analysis']['backend_modules'] = backend_modules
    
    # 5. Key Test Files Analysis
    print("\n" + "=" * 60)
    print("KEY TEST FILES ANALYSIS")
    print("=" * 60)
    
    key_test_files = [
        "test_dependencies.py",
        "test_phase4.py",
        "tests/benchmark_performance.py"
    ]
    
    test_file_analysis = {}
    for file in key_test_files:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    content = f.read()
                compile(content, file, 'exec')  # Syntax check
                print(f"✅ {file} - Valid syntax ({len(content.splitlines())} lines)")
                test_file_analysis[file] = {'valid': True, 'lines': len(content.splitlines())}
            except SyntaxError as e:
                print(f"❌ {file} - Syntax error at line {e.lineno}: {e}")
                test_file_analysis[file] = {'valid': False, 'error': str(e), 'line': e.lineno}
            except Exception as e:
                print(f"⚠️  {file} - Error: {e}")
                test_file_analysis[file] = {'valid': False, 'error': str(e)}
        else:
            print(f"❌ {file} - Not found")
            test_file_analysis[file] = {'valid': False, 'error': 'File not found'}
    
    report['analysis']['key_test_files'] = test_file_analysis
    
    # 6. Summary Statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    
    env_passed = sum(env_checks.values())
    env_total = len(env_checks)
    
    deps_passed = sum(dep_results.values())
    deps_total = len(dep_results)
    
    backend_passed = sum(backend_modules.values()) if backend_modules else 0
    backend_total = len(backend_modules) if backend_modules else 0
    
    test_files_passed = sum(1 for analysis in test_file_analysis.values() if analysis.get('valid', False))
    test_files_total = len(test_file_analysis)
    
    summary = {
        'environment': {'passed': env_passed, 'total': env_total, 'percentage': (env_passed/env_total*100) if env_total > 0 else 0},
        'dependencies': {'passed': deps_passed, 'total': deps_total, 'percentage': (deps_passed/deps_total*100) if deps_total > 0 else 0},
        'backend_modules': {'passed': backend_passed, 'total': backend_total, 'percentage': (backend_passed/backend_total*100) if backend_total > 0 else 0},
        'test_files': {'passed': test_files_passed, 'total': test_files_total, 'percentage': (test_files_passed/test_files_total*100) if test_files_total > 0 else 0},
        'total_test_files_found': total_test_files
    }
    
    report['summary'] = summary
    
    print(f"📊 Environment Setup: {env_passed}/{env_total} ({summary['environment']['percentage']:.1f}%)")
    print(f"📦 Dependencies: {deps_passed}/{deps_total} ({summary['dependencies']['percentage']:.1f}%)")
    print(f"🔧 Backend Modules: {backend_passed}/{backend_total} ({summary['backend_modules']['percentage']:.1f}%)")
    print(f"📄 Key Test Files: {test_files_passed}/{test_files_total} ({summary['test_files']['percentage']:.1f}%)")
    print(f"📁 Total Test Files Found: {total_test_files}")
    
    # 7. Overall Assessment
    print("\n" + "=" * 60)
    print("OVERALL ASSESSMENT")
    print("=" * 60)
    
    total_items = env_total + deps_total + backend_total + test_files_total
    total_passed = env_passed + deps_passed + backend_passed + test_files_passed
    overall_percentage = (total_passed / total_items * 100) if total_items > 0 else 0
    
    print(f"🎯 Overall Readiness: {overall_percentage:.1f}%")
    
    if overall_percentage >= 90:
        print("🎉 EXCELLENT - Ready for comprehensive testing!")
        status = "EXCELLENT"
    elif overall_percentage >= 75:
        print("✅ GOOD - Mostly ready, minor issues to address")
        status = "GOOD"
    elif overall_percentage >= 50:
        print("⚠️  FAIR - Some setup required")
        status = "FAIR"
    else:
        print("❌ POOR - Significant setup needed")
        status = "POOR"
    
    report['overall_status'] = status
    report['overall_percentage'] = overall_percentage
    
    # 8. Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = []
    
    if env_passed < env_total:
        recommendations.append("Set up missing environment files (.env, .env.template)")
    
    if deps_passed < deps_total:
        recommendations.append("Install missing dependencies, especially test dependencies")
    
    if backend_passed < backend_total:
        recommendations.append("Fix backend module imports and dependencies")
    
    if test_files_passed < test_files_total:
        recommendations.append("Fix syntax errors in test files")
    
    if total_test_files == 0:
        recommendations.append("Create or restore test files")
    
    if not recommendations:
        recommendations.append("System appears ready for testing - proceed with test execution")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    report['recommendations'] = recommendations
    
    # 9. Save Report
    report_file = f"manual_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    return 0 if overall_percentage >= 75 else 1

if __name__ == "__main__":
    sys.exit(main())