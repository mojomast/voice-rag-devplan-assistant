"""Complete Phase 4 Test including all 4 endpoints"""
import requests
import time
import json
from pathlib import Path

def test_all_endpoints():
    """Test all 4 search endpoints"""
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {}
    }
    
    try:
        base_url = 'http://localhost:8000'
        
        # Test 1: Backend health
        print("Testing backend health...")
        response = requests.get(f'{base_url}/', timeout=10)
        results['tests']['backend_health'] = {
            'status_code': response.status_code,
            'success': response.status_code == 200
        }
        print(f"Backend health: {response.status_code}")
        
        # Test 2: Search plans
        print("Testing search plans...")
        start = time.time()
        response = requests.post(f'{base_url}/search/plans', 
                               json={"query": "authentication", "limit": 5}, timeout=30)
        elapsed = (time.time() - start) * 1000
        results['tests']['search_plans'] = {
            'status_code': response.status_code,
            'latency_ms': elapsed,
            'success': response.status_code == 200
        }
        print(f"Search plans: {response.status_code}, {elapsed:.1f}ms")
        
        # Test 3: Search projects
        print("Testing search projects...")
        start = time.time()
        response = requests.post(f'{base_url}/search/projects', 
                               json={"query": "development", "limit": 3}, timeout=30)
        elapsed = (time.time() - start) * 1000
        results['tests']['search_projects'] = {
            'status_code': response.status_code,
            'latency_ms': elapsed,
            'success': response.status_code == 200
        }
        print(f"Search projects: {response.status_code}, {elapsed:.1f}ms")
        
        # Test 4: Related plans (need a plan ID first)
        print("Testing related plans...")
        try:
            # Get a plan ID first
            search_response = requests.post(f'{base_url}/search/plans', 
                                          json={"query": "test", "limit": 1}, timeout=30)
            if search_response.status_code == 200 and search_response.json()['results']:
                plan_id = search_response.json()['results'][0]['id']
                start = time.time()
                response = requests.get(f'{base_url}/search/related-plans/{plan_id}?limit=3', timeout=30)
                elapsed = (time.time() - start) * 1000
                results['tests']['related_plans'] = {
                    'status_code': response.status_code,
                    'latency_ms': elapsed,
                    'success': response.status_code == 200
                }
                print(f"Related plans: {response.status_code}, {elapsed:.1f}ms")
            else:
                results['tests']['related_plans'] = {
                    'status_code': 'no_data',
                    'success': False
                }
                print("Related plans: No plans found to test with")
        except Exception as e:
            results['tests']['related_plans'] = {
                'status_code': 'error',
                'success': False,
                'error': str(e)
            }
            print(f"Related plans: Error - {e}")
        
        # Test 5: Similar projects (need a project ID first)
        print("Testing similar projects...")
        try:
            # Get a project ID first
            search_response = requests.post(f'{base_url}/search/projects', 
                                          json={"query": "test", "limit": 1}, timeout=30)
            if search_response.status_code == 200 and search_response.json()['results']:
                project_id = search_response.json()['results'][0]['id']
                start = time.time()
                response = requests.get(f'{base_url}/search/similar-projects/{project_id}?limit=3', timeout=30)
                elapsed = (time.time() - start) * 1000
                results['tests']['similar_projects'] = {
                    'status_code': response.status_code,
                    'latency_ms': elapsed,
                    'success': response.status_code == 200
                }
                print(f"Similar projects: {response.status_code}, {elapsed:.1f}ms")
            else:
                results['tests']['similar_projects'] = {
                    'status_code': 'no_data',
                    'success': False
                }
                print("Similar projects: No projects found to test with")
        except Exception as e:
            results['tests']['similar_projects'] = {
                'status_code': 'error',
                'success': False,
                'error': str(e)
            }
            print(f"Similar projects: Error - {e}")
        
        # Test 6: Performance test
        print("Testing performance...")
        timings = []
        for i in range(5):
            start = time.time()
            response = requests.post(f'{base_url}/search/plans', 
                                   json={"query": f"test query {i}", "limit": 10}, timeout=30)
            elapsed = (time.time() - start) * 1000
            timings.append(elapsed)
            print(f"  Query {i+1}: {elapsed:.1f}ms")
        
        avg_latency = sum(timings) / len(timings)
        results['tests']['performance'] = {
            'average_latency_ms': avg_latency,
            'target_met': avg_latency < 500
        }
        print(f"Average latency: {avg_latency:.1f}ms")
        
        # Calculate overall success
        api_endpoints = ['search_plans', 'search_projects', 'related_plans', 'similar_projects']
        all_endpoints_ok = all(
            results['tests'][ep].get('success', False) 
            for ep in api_endpoints
        )
        performance_ok = avg_latency < 500
        
        results['overall_success'] = all_endpoints_ok and performance_ok
        
    except Exception as e:
        results['error'] = str(e)
        print(f"Error during testing: {e}")
    
    # Write results to file
    with open('complete_phase4_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults written to complete_phase4_results.json")
    print(f"Overall success: {results.get('overall_success', False)}")
    
    return results

if __name__ == "__main__":
    test_all_endpoints()