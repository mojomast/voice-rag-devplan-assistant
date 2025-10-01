"""Simple Phase 4 Test with file output"""
import requests
import time
import json
from pathlib import Path

def test_backend():
    """Test backend and write results to file"""
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {}
    }
    
    try:
        # Test 1: Backend health
        print("Testing backend health...")
        response = requests.get('http://localhost:8000/', timeout=10)
        results['tests']['backend_health'] = {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else response.text,
            'success': response.status_code == 200
        }
        print(f"Backend health: {response.status_code}")
        
        if response.status_code == 200:
            # Test 2: Search plans
            print("Testing search plans...")
            start = time.time()
            response = requests.post('http://localhost:8000/search/plans', 
                                   json={"query": "authentication", "limit": 5}, timeout=30)
            elapsed = (time.time() - start) * 1000
            results['tests']['search_plans'] = {
                'status_code': response.status_code,
                'latency_ms': elapsed,
                'data': response.json() if response.status_code == 200 else response.text,
                'success': response.status_code == 200
            }
            print(f"Search plans: {response.status_code}, {elapsed:.1f}ms")
            
            # Test 3: Search projects
            print("Testing search projects...")
            start = time.time()
            response = requests.post('http://localhost:8000/search/projects', 
                                   json={"query": "development", "limit": 3}, timeout=30)
            elapsed = (time.time() - start) * 1000
            results['tests']['search_projects'] = {
                'status_code': response.status_code,
                'latency_ms': elapsed,
                'data': response.json() if response.status_code == 200 else response.text,
                'success': response.status_code == 200
            }
            print(f"Search projects: {response.status_code}, {elapsed:.1f}ms")
            
            # Test 4: Performance test
            print("Testing performance...")
            timings = []
            for i in range(3):
                start = time.time()
                response = requests.post('http://localhost:8000/search/plans', 
                                       json={"query": f"test query {i}", "limit": 10}, timeout=30)
                elapsed = (time.time() - start) * 1000
                timings.append(elapsed)
                print(f"  Query {i+1}: {elapsed:.1f}ms")
            
            avg_latency = sum(timings) / len(timings)
            results['tests']['performance'] = {
                'average_latency_ms': avg_latency,
                'individual_timings': timings,
                'target_met': avg_latency < 500
            }
            print(f"Average latency: {avg_latency:.1f}ms")
        
        # Test 5: Check vector stores
        print("Checking vector stores...")
        vector_path = Path("vector_store")
        vector_exists = vector_path.exists()
        vector_files = list(vector_path.glob("*")) if vector_exists else []
        results['tests']['vector_stores'] = {
            'exists': vector_exists,
            'file_count': len(vector_files),
            'files': [f.name for f in vector_files[:10]]  # First 10 files
        }
        print(f"Vector stores: {vector_exists}, {len(vector_files)} files")
        
        # Test 6: Check database
        print("Checking database...")
        db_path = Path("data/devplanning.db")
        db_exists = db_path.exists()
        results['tests']['database'] = {
            'exists': db_exists
        }
        print(f"Database: {db_exists}")
        
        # Calculate overall success
        all_successful = all(
            test.get('success', False) if 'success' in test else test.get('exists', False)
            for test in results['tests'].values()
        )
        results['overall_success'] = all_successful
        
    except Exception as e:
        results['error'] = str(e)
        print(f"Error during testing: {e}")
    
    # Write results to file
    with open('phase4_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults written to phase4_test_results.json")
    print(f"Overall success: {results.get('overall_success', False)}")
    
    return results

if __name__ == "__main__":
    test_backend()