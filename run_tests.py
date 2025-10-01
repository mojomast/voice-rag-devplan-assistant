#!/usr/bin/env python3
"""
Comprehensive test runner for voice-rag-system.
This script will run all tests and generate a report.
"""

import sys
import os
import subprocess
import json
from datetime import datetime

def run_command(cmd, timeout=300):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Command timed out',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def check_dependencies():
    """Check if test dependencies are available."""
    print("=" * 60)
    print("CHECKING DEPENDENCIES")
    print("=" * 60)
    
    # Check basic Python modules
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
    
    results = {}
    for dep in dependencies:
        result = run_command(f'python -c "import {dep}"')
        status = "✅" if result['success'] else "❌"
        print(f"{status} {dep}")
        results[dep] = result['success']
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nSummary: {passed}/{total} dependencies available")
    
    return {
        'total': total,
        'passed': passed,
        'failed': total - passed,
        'details': results
    }

def run_unit_tests():
    """Run unit tests with verbose output."""
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    # Run unit tests with verbose output
    result = run_command("python -m pytest tests/unit/ -v --tb=short")
    
    print("UNIT TEST OUTPUT:")
    print(result['stdout'])
    if result['stderr']:
        print("STDERR:")
        print(result['stderr'])
    
    return {
        'success': result['success'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'returncode': result['returncode']
    }

def run_unit_tests_with_coverage():
    """Run unit tests with coverage report."""
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS WITH COVERAGE")
    print("=" * 60)
    
    # Run unit tests with coverage
    result = run_command("python -m pytest tests/unit/ --cov=backend --cov-report=term-missing --cov-report=html")
    
    print("COVERAGE TEST OUTPUT:")
    print(result['stdout'])
    if result['stderr']:
        print("STDERR:")
        print(result['stderr'])
    
    return {
        'success': result['success'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'returncode': result['returncode']
    }

def run_integration_tests():
    """Run integration tests."""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    # Run integration tests
    result = run_command("python -m pytest tests/integration/ -v --tb=short")
    
    print("INTEGRATION TEST OUTPUT:")
    print(result['stdout'])
    if result['stderr']:
        print("STDERR:")
        print(result['stderr'])
    
    return {
        'success': result['success'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'returncode': result['returncode']
    }

def run_phase4_tests():
    """Run Phase 4 comprehensive testing."""
    print("\n" + "=" * 60)
    print("RUNNING PHASE 4 COMPREHENSIVE TESTING")
    print("=" * 60)
    
    # Run Phase 4 tests
    result = run_command("python test_phase4.py")
    
    print("PHASE 4 TEST OUTPUT:")
    print(result['stdout'])
    if result['stderr']:
        print("STDERR:")
        print(result['stderr'])
    
    return {
        'success': result['success'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'returncode': result['returncode']
    }

def run_dependency_verification():
    """Run dependency verification script."""
    print("\n" + "=" * 60)
    print("RUNNING DEPENDENCY VERIFICATION")
    print("=" * 60)
    
    # Run dependency verification
    result = run_command("python test_dependencies.py")
    
    print("DEPENDENCY VERIFICATION OUTPUT:")
    print(result['stdout'])
    if result['stderr']:
        print("STDERR:")
        print(result['stderr'])
    
    return {
        'success': result['success'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'returncode': result['returncode']
    }

def run_performance_benchmarks():
    """Run performance benchmarks."""
    print("\n" + "=" * 60)
    print("RUNNING PERFORMANCE BENCHMARKS")
    print("=" * 60)
    
    # Run performance benchmarks
    result = run_command("python tests/benchmark_performance.py")
    
    print("PERFORMANCE BENCHMARK OUTPUT:")
    print(result['stdout'])
    if result['stderr']:
        print("STDERR:")
        print(result['stderr'])
    
    return {
        'success': result['success'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'returncode': result['returncode']
    }

def generate_report(results):
    """Generate a comprehensive test report."""
    print("\n" + "=" * 60)
    print("GENERATING TEST REPORT")
    print("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': len(results),
            'passed': sum(1 for r in results.values() if r['success']),
            'failed': sum(1 for r in results.values() if not r['success'])
        },
        'results': results
    }
    
    # Save report to file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Test report saved to: {report_file}")
    
    # Print summary
    print("\nTEST SUMMARY:")
    print(f"Total test suites: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    
    return report

def main():
    """Main test runner function."""
    print("VOICE-RAG-SYSTEM COMPREHENSIVE TEST SUITE")
    print(f"Started at: {datetime.now().isoformat()}")
    
    results = {}
    
    # 1. Check dependencies
    results['dependencies'] = check_dependencies()
    
    # 2. Run unit tests
    results['unit_tests'] = run_unit_tests()
    
    # 3. Run unit tests with coverage
    results['unit_tests_coverage'] = run_unit_tests_with_coverage()
    
    # 4. Run integration tests
    results['integration_tests'] = run_integration_tests()
    
    # 5. Run dependency verification
    results['dependency_verification'] = run_dependency_verification()
    
    # 6. Run Phase 4 tests
    results['phase4_tests'] = run_phase4_tests()
    
    # 7. Run performance benchmarks
    results['performance_benchmarks'] = run_performance_benchmarks()
    
    # 8. Generate report
    report = generate_report(results)
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
    
    return 0 if report['summary']['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())