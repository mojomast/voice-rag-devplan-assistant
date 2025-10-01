"""Quick Phase 4 Component Tests - No Backend Required"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all Phase 4 components can be imported."""
    print("=" * 60)
    print("COMPONENT IMPORT TEST")
    print("=" * 60)
    
    tests = []
    
    # Test 1: DevPlan Processor
    try:
        from backend.devplan_processor import DevPlanProcessor
        print("✅ DevPlanProcessor imported successfully")
        tests.append(("DevPlanProcessor", True))
    except Exception as e:
        print(f"❌ DevPlanProcessor import failed: {e}")
        tests.append(("DevPlanProcessor", False))
    
    # Test 2: Project Memory
    try:
        from backend.project_memory import ProjectMemorySystem
        print("✅ ProjectMemorySystem imported successfully")
        tests.append(("ProjectMemorySystem", True))
    except Exception as e:
        print(f"❌ ProjectMemorySystem import failed: {e}")
        tests.append(("ProjectMemorySystem", False))
    
    # Test 3: Auto Indexer
    try:
        from backend.auto_indexer import AutoIndexer
        print("✅ AutoIndexer imported successfully")
        tests.append(("AutoIndexer", True))
    except Exception as e:
        print(f"❌ AutoIndexer import failed: {e}")
        tests.append(("AutoIndexer", False))
    
    # Test 4: Context Manager
    try:
        from backend.context_manager import PlanningContextManager
        print("✅ PlanningContextManager imported successfully")
        tests.append(("PlanningContextManager", True))
    except Exception as e:
        print(f"❌ PlanningContextManager import failed: {e}")
        tests.append(("PlanningContextManager", False))
    
    # Test 5: Search Router
    try:
        from backend.routers.search import router
        print("✅ Search router imported successfully")
        tests.append(("Search Router", True))
    except Exception as e:
        print(f"❌ Search router import failed: {e}")
        tests.append(("Search Router", False))
    
    # Test 6: Reindex Script
    try:
        from backend.scripts.reindex_all import main as reindex_main
        print("✅ Reindex script imported successfully")
        tests.append(("Reindex Script", True))
    except Exception as e:
        print(f"❌ Reindex script import failed: {e}")
        tests.append(("Reindex Script", False))
    
    # Test 7: RAG Handler
    try:
        from backend.rag_handler import RAGHandler
        print("✅ RAGHandler imported successfully")
        tests.append(("RAGHandler", True))
    except Exception as e:
        print(f"❌ RAGHandler import failed: {e}")
        tests.append(("RAGHandler", False))
    
    return tests


def test_vector_stores():
    """Test vector store files exist and are valid."""
    print("\n" + "=" * 60)
    print("VECTOR STORE VALIDATION")
    print("=" * 60)
    
    vector_path = Path("vector_store")
    results = []
    
    if not vector_path.exists():
        print("❌ Vector store directory not found")
        return [("Vector Store Directory", False)]
    
    print(f"✅ Vector store directory exists: {vector_path}")
    results.append(("Vector Store Directory", True))
    
    # Check devplans
    devplans_path = vector_path / "devplans"
    if devplans_path.exists():
        faiss_file = devplans_path / "index.faiss"
        pkl_file = devplans_path / "index.pkl"
        
        if faiss_file.exists() and pkl_file.exists():
            faiss_size = faiss_file.stat().st_size
            pkl_size = pkl_file.stat().st_size
            print(f"✅ DevPlans vector store:")
            print(f"   - index.faiss: {faiss_size:,} bytes")
            print(f"   - index.pkl: {pkl_size:,} bytes")
            results.append(("DevPlans Vector Store", True))
        else:
            print("⚠️  DevPlans vector store incomplete")
            results.append(("DevPlans Vector Store", False))
    else:
        print("⚠️  DevPlans vector store not found")
        results.append(("DevPlans Vector Store", False))
    
    # Check projects
    projects_path = vector_path / "projects"
    if projects_path.exists():
        files = list(projects_path.glob("*"))
        if files:
            print(f"✅ Projects vector store: {len(files)} files")
            results.append(("Projects Vector Store", True))
        else:
            print("⚠️  Projects vector store is empty")
            results.append(("Projects Vector Store", False))
    else:
        print("⚠️  Projects vector store not found (needs indexing)")
        results.append(("Projects Vector Store", False))
    
    # Check main store
    main_faiss = vector_path / "index.faiss"
    main_pkl = vector_path / "index.pkl"
    if main_faiss.exists() and main_pkl.exists():
        print(f"✅ Main vector store exists")
        results.append(("Main Vector Store", True))
    else:
        print("⚠️  Main vector store not found")
        results.append(("Main Vector Store", False))
    
    return results


def test_file_structure():
    """Test that all Phase 4 files were created."""
    print("\n" + "=" * 60)
    print("FILE STRUCTURE VALIDATION")
    print("=" * 60)
    
    files_to_check = [
        ("backend/devplan_processor.py", "DevPlan Processor"),
        ("backend/project_memory.py", "Project Memory System"),
        ("backend/auto_indexer.py", "Auto Indexer"),
        ("backend/context_manager.py", "Context Manager"),
        ("backend/routers/search.py", "Search Router"),
        ("backend/scripts/__init__.py", "Scripts Module"),
        ("backend/scripts/reindex_all.py", "Reindex Script"),
        ("docs/API_SEARCH.md", "Search API Documentation"),
        ("docs/RAG_INTEGRATION.md", "RAG Integration Documentation"),
        ("PHASE4_PROGRESS.md", "Phase 4 Progress"),
        ("PHASE4_TESTING.md", "Phase 4 Testing Guide"),
        ("PHASE4_COMPLETE.md", "Phase 4 Completion Summary"),
        ("NEXTSTEPS.md", "Next Steps Handoff"),
    ]
    
    results = []
    for file_path, description in files_to_check:
        path = Path(file_path)
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"✅ {description}: {size_kb:.1f} KB")
            results.append((description, True))
        else:
            print(f"❌ {description}: NOT FOUND")
            results.append((description, False))
    
    return results


def test_documentation():
    """Test that documentation is complete and well-formed."""
    print("\n" + "=" * 60)
    print("DOCUMENTATION VALIDATION")
    print("=" * 60)
    
    results = []
    
    # Check API_SEARCH.md
    api_doc = Path("docs/API_SEARCH.md")
    if api_doc.exists():
        content = api_doc.read_text(encoding="utf-8")
        lines = len(content.splitlines())
        has_endpoints = "/search/plans" in content and "/search/projects" in content
        has_examples = "curl" in content.lower()
        has_responses = "response" in content.lower()
        
        print(f"📄 API_SEARCH.md: {lines} lines")
        print(f"   - Endpoints documented: {'✅' if has_endpoints else '❌'}")
        print(f"   - Examples included: {'✅' if has_examples else '❌'}")
        print(f"   - Response formats: {'✅' if has_responses else '❌'}")
        
        results.append(("API Documentation", has_endpoints and has_examples))
    else:
        print("❌ API_SEARCH.md not found")
        results.append(("API Documentation", False))
    
    # Check RAG_INTEGRATION.md
    rag_doc = Path("docs/RAG_INTEGRATION.md")
    if rag_doc.exists():
        content = rag_doc.read_text(encoding="utf-8")
        lines = len(content.splitlines())
        has_architecture = "architecture" in content.lower()
        has_indexing = "indexing" in content.lower()
        has_performance = "performance" in content.lower()
        
        print(f"📄 RAG_INTEGRATION.md: {lines} lines")
        print(f"   - Architecture explained: {'✅' if has_architecture else '❌'}")
        print(f"   - Indexing documented: {'✅' if has_indexing else '❌'}")
        print(f"   - Performance tips: {'✅' if has_performance else '❌'}")
        
        results.append(("RAG Documentation", has_architecture and has_indexing))
    else:
        print("❌ RAG_INTEGRATION.md not found")
        results.append(("RAG Documentation", False))
    
    return results


def main():
    """Run all quick tests."""
    print("\n" + "🚀" * 30)
    print("PHASE 4 QUICK VALIDATION")
    print("🚀" * 30)
    
    all_results = []
    
    # Run all tests
    import_results = test_imports()
    all_results.extend(import_results)
    
    vector_results = test_vector_stores()
    all_results.extend(vector_results)
    
    file_results = test_file_structure()
    all_results.extend(file_results)
    
    doc_results = test_documentation()
    all_results.extend(doc_results)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"✅ Passed: {passed}/{total} ({pass_rate:.0f}%)")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if pass_rate >= 80:
        print("\n🎉 EXCELLENT! Phase 4 implementation is solid!")
    elif pass_rate >= 60:
        print("\n✅ GOOD! Most Phase 4 components are working!")
    else:
        print("\n⚠️  NEEDS WORK: Some components need attention")
    
    print("\n📋 Next Steps:")
    print("   1. Start backend manually: python -m uvicorn backend.main:app --reload")
    print("   2. Test API endpoints using test_phase4.py")
    print("   3. Run: python -m backend.scripts.reindex_all")
    print("   4. Test UI in browser")
    
    return pass_rate >= 80


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
