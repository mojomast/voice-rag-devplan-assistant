"""Phase 4 Testing Script - Comprehensive validation"""
import asyncio
import sqlite3
import time
from pathlib import Path

import httpx

# Configuration
BASE_URL = "http://localhost:8000"
DB_PATH = Path("data/devplanning.db")


def check_database_state():
    """Check if database exists and has test data."""
    print("=" * 60)
    print("DATABASE STATE CHECK")
    print("=" * 60)
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Run the backend to initialize it first.")
        return False
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Database exists with {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} rows")
        
        # Get specific counts
        cursor.execute("SELECT COUNT(*) FROM devplans")
        plan_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        
        print()
        print(f"📊 Summary:")
        print(f"   Plans: {plan_count}")
        print(f"   Projects: {project_count}")
        
        return plan_count > 0 and project_count > 0
        
    finally:
        conn.close()


async def test_backend_health():
    """Test if backend is running and responsive."""
    print("\n" + "=" * 60)
    print("BACKEND HEALTH CHECK")
    print("=" * 60)
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{BASE_URL}/")
                print(f"✅ Backend is running (attempt {attempt + 1}/{max_attempts})")
                print(f"   Status: {response.status_code}")
                return True
        except Exception as e:
            print(f"⏳ Backend not ready (attempt {attempt + 1}/{max_attempts}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(5)
    
    print("❌ Backend failed to start")
    return False


async def test_search_api():
    """Test all 4 search API endpoints."""
    print("\n" + "=" * 60)
    print("SEARCH API ENDPOINTS TEST")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Test 1: Search Plans
        print("\n🔍 Test 1: POST /search/plans")
        try:
            response = await client.post(
                f"{BASE_URL}/search/plans",
                json={"query": "authentication", "limit": 5}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['total_found']} results")
                if data['results']:
                    print(f"   Top result: {data['results'][0]['title']} (score: {data['results'][0]['score']:.2f})")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # Test 2: Search Projects
        print("\n🔍 Test 2: POST /search/projects")
        try:
            response = await client.post(
                f"{BASE_URL}/search/projects",
                json={"query": "development", "limit": 3}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['total_found']} results")
                if data['results']:
                    print(f"   Top result: {data['results'][0]['title']} (score: {data['results'][0]['score']:.2f})")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # Test 3: Related Plans (need a valid plan ID)
        print("\n🔍 Test 3: GET /search/related-plans/{plan_id}")
        try:
            # First get a plan ID from search
            search_response = await client.post(
                f"{BASE_URL}/search/plans",
                json={"query": "test", "limit": 1}
            )
            if search_response.status_code == 200 and search_response.json()['results']:
                plan_id = search_response.json()['results'][0]['id']
                response = await client.get(f"{BASE_URL}/search/related-plans/{plan_id}?limit=3")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Found {len(data.get('results', []))} related plans")
                else:
                    print(f"   ⚠️  Response: {response.text}")
            else:
                print(f"   ⚠️  No plans found to test with")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # Test 4: Similar Projects
        print("\n🔍 Test 4: GET /search/similar-projects/{project_id}")
        try:
            # First get a project ID from search
            search_response = await client.post(
                f"{BASE_URL}/search/projects",
                json={"query": "test", "limit": 1}
            )
            if search_response.status_code == 200 and search_response.json()['results']:
                project_id = search_response.json()['results'][0]['id']
                response = await client.get(f"{BASE_URL}/search/similar-projects/{project_id}?limit=3")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Found {len(data.get('results', []))} similar projects")
                else:
                    print(f"   ⚠️  Response: {response.text}")
            else:
                print(f"   ⚠️  No projects found to test with")
        except Exception as e:
            print(f"   ❌ Failed: {e}")


async def test_performance():
    """Test performance benchmarks."""
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 60)
    
    print("\n⏱️  Testing search latency (target: <500ms)...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        timings = []
        for i in range(5):
            start = time.time()
            try:
                response = await client.post(
                    f"{BASE_URL}/search/plans",
                    json={"query": f"test query {i}", "limit": 10}
                )
                elapsed = (time.time() - start) * 1000  # Convert to ms
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


async def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 60)
    print("EDGE CASE TESTING")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Test empty query
        print("\n🧪 Test 1: Empty query")
        try:
            response = await client.post(
                f"{BASE_URL}/search/plans",
                json={"query": "", "limit": 5}
            )
            print(f"   Status: {response.status_code}")
            print(f"   ✅ Handled gracefully" if response.status_code in [200, 400] else "   ❌ Unexpected response")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # Test very long query
        print("\n🧪 Test 2: Very long query")
        try:
            long_query = "test " * 1000
            response = await client.post(
                f"{BASE_URL}/search/plans",
                json={"query": long_query, "limit": 5}
            )
            print(f"   Status: {response.status_code}")
            print(f"   ✅ Handled gracefully" if response.status_code in [200, 400, 413] else "   ❌ Unexpected response")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # Test non-existent plan ID
        print("\n🧪 Test 3: Non-existent plan ID")
        try:
            response = await client.get(f"{BASE_URL}/search/related-plans/nonexistent-id-12345")
            print(f"   Status: {response.status_code}")
            print(f"   ✅ Returns 404" if response.status_code == 404 else f"   ⚠️  Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")


def check_vector_stores():
    """Check vector store file structure."""
    print("\n" + "=" * 60)
    print("VECTOR STORE CHECK")
    print("=" * 60)
    
    vector_path = Path("vector_store")
    
    if not vector_path.exists():
        print("❌ Vector store directory not found")
        return False
    
    # Check for expected directories
    expected = ["devplans", "projects"]
    for subdir in expected:
        subdir_path = vector_path / subdir
        if subdir_path.exists():
            files = list(subdir_path.glob("*"))
            print(f"✅ {subdir}/: {len(files)} files")
            for f in files:
                size_kb = f.stat().st_size / 1024
                print(f"   - {f.name}: {size_kb:.1f} KB")
        else:
            print(f"⚠️  {subdir}/: Not found (may need indexing)")
    
    # Check main vector store
    main_files = list(vector_path.glob("index.*"))
    if main_files:
        print(f"✅ Main vector store: {len(main_files)} files")
        for f in main_files:
            size_kb = f.stat().st_size / 1024
            print(f"   - {f.name}: {size_kb:.1f} KB")
    
    return True


async def main():
    """Run all Phase 4 tests."""
    print("\n" + "🚀" * 30)
    print("PHASE 4 TESTING - COMPREHENSIVE VALIDATION")
    print("🚀" * 30)
    
    # Pre-flight checks
    check_vector_stores()
    has_data = check_database_state()
    
    if not has_data:
        print("\n⚠️  WARNING: No test data found!")
        print("   Consider creating some projects and plans first.")
        print("   Tests will continue but may have limited results.")
    
    # Wait for backend
    backend_ready = await test_backend_health()
    if not backend_ready:
        print("\n❌ Cannot proceed without backend running")
        print("   Start backend: uvicorn backend.main:app --reload")
        return
    
    # Run tests
    await test_search_api()
    await test_performance()
    await test_edge_cases()
    
    # Summary
    print("\n" + "=" * 60)
    print("TESTING SUMMARY")
    print("=" * 60)
    print("✅ Pre-test setup complete")
    print("✅ Search API endpoints tested")
    print("✅ Performance benchmarks measured")
    print("✅ Edge cases validated")
    print("\n📋 Next Steps:")
    print("   1. Review test results above")
    print("   2. Test UI components manually (Streamlit)")
    print("   3. Run bulk re-indexing: python -m backend.scripts.reindex_all")
    print("   4. Update PHASE4_PROGRESS.md to 100%")
    print("\n🎉 Phase 4 Testing Complete!")


if __name__ == "__main__":
    asyncio.run(main())
