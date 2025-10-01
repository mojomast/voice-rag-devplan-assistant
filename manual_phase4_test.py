"""Manual Phase 4 Testing Script"""
import asyncio
import time
import httpx
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_backend_health():
    """Test backend health"""
    print("🔍 Testing backend health...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Backend healthy: {data.get('status')}")
                print(f"   Vector store exists: {data.get('vector_store_exists')}")
                print(f"   Document count: {data.get('document_count')}")
                return True
            else:
                print(f"   ❌ Backend unhealthy: {response.text}")
                return False
    except Exception as e:
        print(f"   ❌ Backend connection failed: {e}")
        return False

async def test_search_endpoints():
    """Test all 4 search endpoints"""
    print("\n🔍 Testing search API endpoints...")
    results = {}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Search Plans
        print("\n1. Testing POST /search/plans")
        try:
            start_time = time.time()
            response = await client.post(
                f"{BASE_URL}/search/plans",
                json={"query": "authentication", "limit": 5}
            )
            elapsed = (time.time() - start_time) * 1000
            print(f"   Status: {response.status_code}, Latency: {elapsed:.1f}ms")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['total_found']} results")
                if data['results']:
                    print(f"   Top result: {data['results'][0]['title']} (score: {data['results'][0]['score']:.2f})")
                results['search_plans'] = {'status': 200, 'latency': elapsed, 'results': data['total_found']}
            else:
                print(f"   ❌ Error: {response.text}")
                results['search_plans'] = {'status': response.status_code, 'latency': elapsed}
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results['search_plans'] = {'status': 'error', 'error': str(e)}
        
        # Test 2: Search Projects
        print("\n2. Testing POST /search/projects")
        try:
            start_time = time.time()
            response = await client.post(
                f"{BASE_URL}/search/projects",
                json={"query": "development", "limit": 3}
            )
            elapsed = (time.time() - start_time) * 1000
            print(f"   Status: {response.status_code}, Latency: {elapsed:.1f}ms")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['total_found']} results")
                if data['results']:
                    print(f"   Top result: {data['results'][0]['title']} (score: {data['results'][0]['score']:.2f})")
                results['search_projects'] = {'status': 200, 'latency': elapsed, 'results': data['total_found']}
            else:
                print(f"   ❌ Error: {response.text}")
                results['search_projects'] = {'status': response.status_code, 'latency': elapsed}
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results['search_projects'] = {'status': 'error', 'error': str(e)}
        
        # Test 3: Related Plans (need a plan ID first)
        print("\n3. Testing GET /search/related-plans/{plan_id}")
        try:
            # Get a plan ID first
            search_response = await client.post(
                f"{BASE_URL}/search/plans",
                json={"query": "test", "limit": 1}
            )
            if search_response.status_code == 200 and search_response.json()['results']:
                plan_id = search_response.json()['results'][0]['id']
                start_time = time.time()
                response = await client.get(f"{BASE_URL}/search/related-plans/{plan_id}?limit=3")
                elapsed = (time.time() - start_time) * 1000
                print(f"   Status: {response.status_code}, Latency: {elapsed:.1f}ms")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Found {len(data.get('results', []))} related plans")
                    results['related_plans'] = {'status': 200, 'latency': elapsed, 'results': len(data.get('results', []))}
                else:
                    print(f"   ⚠️  Response: {response.text}")
                    results['related_plans'] = {'status': response.status_code, 'latency': elapsed}
            else:
                print("   ⚠️  No plans found to test with")
                results['related_plans'] = {'status': 'no_data', 'error': 'No plans found'}
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results['related_plans'] = {'status': 'error', 'error': str(e)}
        
        # Test 4: Similar Projects (need a project ID first)
        print("\n4. Testing GET /search/similar-projects/{project_id}")
        try:
            # Get a project ID first
            search_response = await client.post(
                f"{BASE_URL}/search/projects",
                json={"query": "test", "limit": 1}
            )
            if search_response.status_code == 200 and search_response.json()['results']:
                project_id = search_response.json()['results'][0]['id']
                start_time = time.time()
                response = await client.get(f"{BASE_URL}/search/similar-projects/{project_id}?limit=3")
                elapsed = (time.time() - start_time) * 1000
                print(f"   Status: {response.status_code}, Latency: {elapsed:.1f}ms")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Found {len(data.get('results', []))} similar projects")
                    results['similar_projects'] = {'status': 200, 'latency': elapsed, 'results': len(data.get('results', []))}
                else:
                    print(f"   ⚠️  Response: {response.text}")
                    results['similar_projects'] = {'status': response.status_code, 'latency': elapsed}
            else:
                print("   ⚠️  No projects found to test with")
                results['similar_projects'] = {'status': 'no_data', 'error': 'No projects found'}
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results['similar_projects'] = {'status': 'error', 'error': str(e)}
    
    return results

async def test_performance():
    """Test search performance"""
    print("\n⏱️  Testing search performance...")
    timings = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(5):
            start = time.time()
            try:
                response = await client.post(
                    f"{BASE_URL}/search/plans",
                    json={"query": f"test query {i}", "limit": 10}
                )
                elapsed = (time.time() - start) * 1000
                timings.append(elapsed)
                status = "✅" if elapsed < 500 else "⚠️"
                print(f"   Query {i+1}: {elapsed:.1f}ms {status}")
            except Exception as e:
                print(f"   Query {i+1}: Failed - {e}")
        
        if timings:
            avg_time = sum(timings) / len(timings)
            print(f"\n📊 Average: {avg_time:.1f}ms")
            if avg_time < 500:
                print("   ✅ Performance target met!")
            else:
                print("   ⚠️  Performance below target")
            return avg_time
        return None

def check_vector_stores():
    """Check vector store structure"""
    print("\n📁 Checking vector stores...")
    vector_path = Path("vector_store")
    
    if not vector_path.exists():
        print("   ❌ Vector store directory not found")
        return False
    
    # Check for expected directories
    expected = ["devplans", "projects"]
    for subdir in expected:
        subdir_path = vector_path / subdir
        if subdir_path.exists():
            files = list(subdir_path.glob("*"))
            print(f"   ✅ {subdir}/: {len(files)} files")
            for f in files[:3]:  # Show first 3 files
                size_kb = f.stat().st_size / 1024
                print(f"      - {f.name}: {size_kb:.1f} KB")
            if len(files) > 3:
                print(f"      ... and {len(files) - 3} more files")
        else:
            print(f"   ⚠️  {subdir}/: Not found")
    
    # Check main vector store
    main_files = list(vector_path.glob("index.*"))
    if main_files:
        print(f"   ✅ Main vector store: {len(main_files)} files")
        for f in main_files:
            size_kb = f.stat().st_size / 1024
            print(f"      - {f.name}: {size_kb:.1f} KB")
    
    return True

def check_database():
    """Check database state"""
    print("\n🗄️  Checking database...")
    db_path = Path("data/devplanning.db")
    
    if not db_path.exists():
        print("   ❌ Database not found")
        return False
    
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   ✅ Database found with {len(tables)} tables")
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"      - {table}: {count} rows")
        
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

async def main():
    """Run manual Phase 4 tests"""
    print("🚀" * 30)
    print("MANUAL PHASE 4 TESTING")
    print("🚀" * 30)
    
    # Test backend health
    backend_healthy = await test_backend_health()
    if not backend_healthy:
        print("\n❌ Backend not healthy - cannot continue")
        return
    
    # Test search endpoints
    search_results = await test_search_endpoints()
    
    # Test performance
    avg_latency = await test_performance()
    
    # Check vector stores
    vector_ok = check_vector_stores()
    
    # Check database
    db_ok = check_database()
    
    # Summary
    print("\n" + "=" * 60)
    print("PHASE 4 TEST SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 API Endpoints:")
    for endpoint, result in search_results.items():
        status_icon = "✅" if result.get('status') == 200 else "❌"
        latency = result.get('latency', 0)
        print(f"   {status_icon} {endpoint}: {result.get('status')} ({latency:.1f}ms)")
    
    print(f"\n⏱️  Performance:")
    if avg_latency:
        perf_icon = "✅" if avg_latency < 500 else "⚠️"
        print(f"   {perf_icon} Average latency: {avg_latency:.1f}ms (target: <500ms)")
    
    print(f"\n📁 Infrastructure:")
    print(f"   {'✅' if vector_ok else '❌'} Vector stores")
    print(f"   {'✅' if db_ok else '❌'} Database")
    print(f"   {'✅' if backend_healthy else '❌'} Backend health")
    
    # Overall assessment
    all_endpoints_ok = all(result.get('status') == 200 for result in search_results.values())
    performance_ok = avg_latency and avg_latency < 500
    infrastructure_ok = vector_ok and db_ok and backend_healthy
    
    print(f"\n🎯 OVERALL STATUS:")
    if all_endpoints_ok and performance_ok and infrastructure_ok:
        print("   ✅ PHASE 4 VALIDATION SUCCESSFUL")
    else:
        print("   ⚠️  PHASE 4 VALIDATION NEEDS ATTENTION")
        if not all_endpoints_ok:
            print("      - Some API endpoints failing")
        if not performance_ok:
            print("      - Performance below target")
        if not infrastructure_ok:
            print("      - Infrastructure issues")

if __name__ == "__main__":
    asyncio.run(main())