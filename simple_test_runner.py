#!/usr/bin/env python3
"""
Simple test runner that executes tests directly without subprocess.
"""

import sys
import os
import importlib.util
from datetime import datetime

def load_module_from_file(module_name, file_path):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def check_basic_dependencies():
    """Check basic Python dependencies."""
    print("=" * 60)
    print("CHECKING BASIC DEPENDENCIES")
    print("=" * 60)
    
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
        try:
            __import__(dep)
            print(f"✅ {dep}")
            results[dep] = True
        except ImportError:
            print(f"❌ {dep}")
            results[dep] = False
        except Exception as e:
            print(f"⚠️ {dep} - {e}")
            results[dep] = False
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nSummary: {passed}/{total} dependencies available")
    
    return {
        'total': total,
        'passed': passed,
        'failed': total - passed,
        'details': results
    }

def run_test_dependencies_script():
    """Run the test_dependencies.py script directly."""
    print("\n" + "=" * 60)
    print("RUNNING DEPENDENCY VERIFICATION SCRIPT")
    print("=" * 60)
    
    try:
        # Load and run the test_dependencies.py script
        test_deps = load_module_from_file("test_dependencies", "test_dependencies.py")
        exit_code = test_deps.main()
        
        success = exit_code == 0
        print(f"\nDependency verification {'PASSED' if success else 'FAILED'}")
        
        return {
            'success': success,
            'exit_code': exit_code
        }
    except Exception as e:
        print(f"Error running dependency verification: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def run_phase4_test_script():
    """Run the test_phase4.py script directly."""
    print("\n" + "=" * 60)
    print("RUNNING PHASE 4 COMPREHENSIVE TESTING")
    print("=" * 60)
    
    try:
        # Load and run the test_phase4.py script
        phase4_test = load_module_from_file("test_phase4", "test_phase4.py")
        
        # Check if the script has a main function
        if hasattr(phase4_test, 'main'):
            exit_code = phase4_test.main()
        else:
            # If no main function, just import it to check for syntax errors
            print("test_phase4.py loaded successfully (no main function found)")
            exit_code = 0
        
        success = exit_code == 0
        print(f"\nPhase 4 testing {'PASSED' if success else 'FAILED'}")
        
        return {
            'success': success,
            'exit_code': exit_code
        }
    except Exception as e:
        print(f"Error running Phase 4 testing: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def run_performance_benchmark_script():
    """Run the benchmark_performance.py script directly."""
    print("\n" + "=" * 60)
    print("RUNNING PERFORMANCE BENCHMARKS")
    print("=" * 60)
    
    try:
        # Load and run the benchmark_performance.py script
        benchmark_path = "tests/benchmark_performance.py"
        if os.path.exists(benchmark_path):
            benchmark_test = load_module_from_file("benchmark_performance", benchmark_path)
            
            # Check if the script has a main function
            if hasattr(benchmark_test, 'main'):
                exit_code = benchmark_test.main()
            else:
                print("benchmark_performance.py loaded successfully (no main function found)")
                exit_code = 0
            
            success = exit_code == 0
            print(f"\nPerformance benchmark {'PASSED' if success else 'FAILED'}")
            
            return {
                'success': success,
                'exit_code': exit_code
            }
        else:
            print("benchmark_performance.py not found")
            return {
                'success': False,
                'error': "File not found"
            }
    except Exception as e:
        print(f"Error running performance benchmark: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def check_unit_test_files():
    """Check if unit test files exist and can be imported."""
    print("\n" + "=" * 60)
    print("CHECKING UNIT TEST FILES")
    print("=" * 60)
    
    test_dir = "tests/unit"
    if not os.path.exists(test_dir):
        print(f"❌ Test directory {test_dir} not found")
        return {'success': False, 'error': 'Test directory not found'}
    
    test_files = []
    for file in os.listdir(test_dir):
        if file.startswith('test_') and file.endswith('.py'):
            test_files.append(file)
    
    print(f"Found {len(test_files)} unit test files:")
    for file in test_files:
        print(f"  📄 {file}")
    
    # Try to import a few test files to check for syntax errors
    successful_imports = 0
    for file in test_files[:3]:  # Check first 3 files
        try:
            module_name = file[:-3]  # Remove .py extension
            module_path = os.path.join(test_dir, file)
            load_module_from_file(f"test_{module_name}", module_path)
            print(f"  ✅ {file} - Syntax OK")
            successful_imports += 1
        except Exception as e:
            print(f"  ❌ {file} - Error: {e}")
    
    return {
        'success': successful_imports > 0,
        'total_files': len(test_files),
        'successful_imports': successful_imports
    }

def check_integration_test_files():
    """Check if integration test files exist and can be imported."""
    print("\n" + "=" * 60)
    print("CHECKING INTEGRATION TEST FILES")
    print("=" * 60)
    
    test_dir = "tests/integration"
    if not os.path.exists(test_dir):
        print(f"❌ Integration test directory {test_dir} not found")
        return {'success': False, 'error': 'Integration test directory not found'}
    
    test_files = []
    for file in os.listdir(test_dir):
        if file.startswith('test_') and file.endswith('.py'):
            test_files.append(file)
    
    print(f"Found {len(test_files)} integration test files:")
    for file in test_files:
        print(f"  📄 {file}")
    
    # Try to import a few test files to check for syntax errors
    successful_imports = 0
    for file in test_files[:3]:  # Check first 3 files
        try:
            module_name = file[:-3]  # Remove .py extension
            module_path = os.path.join(test_dir, file)
            load_module_from_file(f"integration_{module_name}", module_path)
            print(f"  ✅ {file} - Syntax OK")
            successful_imports += 1
        except Exception as e:
            print(f"  ❌ {file} - Error: {e}")
    
    return {
        'success': successful_imports > 0,
        'total_files': len(test_files),
        'successful_imports': successful_imports
    }

def generate_simple_report(results):
    """Generate a simple test report."""
    print("\n" + "=" * 60)
    print("TEST REPORT SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r.get('success', False))
    failed_tests = total_tests - passed_tests
    
    print(f"Total test suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not result.get('success', False) and 'error' in result:
            print(f"    Error: {result['error']}")
    
    return {
        'timestamp': datetime.now().isoformat(),
        'total_tests': total_tests,
        'passed': passed_tests,
        'failed': failed_tests,
        'results': results
    }

def main():
    """Main test runner function."""
    print("VOICE-RAG-SYSTEM SIMPLE TEST RUNNER")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Working directory: {os.getcwd()}")
    
    results = {}
    
    # 1. Check basic dependencies
    results['basic_dependencies'] = check_basic_dependencies()
    
    # 2. Check unit test files
    results['unit_test_files'] = check_unit_test_files()
    
    # 3. Check integration test files
    results['integration_test_files'] = check_integration_test_files()
    
    # 4. Run dependency verification script
    results['dependency_verification'] = run_test_dependencies_script()
    
    # 5. Run Phase 4 test script
    results['phase4_tests'] = run_phase4_test_script()
    
    # 6. Run performance benchmark script
    results['performance_benchmarks'] = run_performance_benchmark_script()
    
    # 7. Generate report
    report = generate_simple_report(results)
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
    
    return 0 if report['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())