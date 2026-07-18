"""Quick backend health check and functionality test."""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all backend modules can be imported."""
    print("Testing imports...")
    try:
        from backend import config, llm_client, ingest, copilot, compliance, main
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_data_files():
    """Test that required data files exist."""
    print("\nTesting data files...")
    from pathlib import Path

    required_files = [
        "data/entities.json",
        "data/compliance_rules.json",
        "data/benchmark.json",
        "data/graph.json",
    ]

    missing = []
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (missing)")
            missing.append(file_path)

    return len(missing) == 0

def test_chromadb():
    """Test ChromaDB connection."""
    print("\nTesting ChromaDB...")
    try:
        import chromadb
        from backend.config import CHROMA_PERSIST_DIR

        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        collection = client.get_collection("assetbrain_docs")
        count = collection.count()
        print(f"✓ ChromaDB connected: {count} chunks indexed")
        return count > 0
    except Exception as e:
        print(f"✗ ChromaDB error: {e}")
        return False

def test_knowledge_graph():
    """Test knowledge graph loading."""
    print("\nTesting knowledge graph...")
    try:
        from backend.ingest import KnowledgeGraph
        kg = KnowledgeGraph.load()
        print(f"✓ Knowledge graph loaded: {kg.graph.number_of_nodes()} nodes, {kg.graph.number_of_edges()} edges")
        return kg.graph.number_of_nodes() > 0
    except Exception as e:
        print(f"✗ Knowledge graph error: {e}")
        return False

def test_api_key():
    """Test if GEMINI_API_KEY is set."""
    print("\nTesting API key...")
    from backend.config import GEMINI_API_KEY
    if GEMINI_API_KEY:
        print(f"✓ GEMINI_API_KEY is set ({GEMINI_API_KEY[:10]}...)")
        return True
    else:
        print("✗ GEMINI_API_KEY not set")
        print("  Set it with: set GEMINI_API_KEY=your-key-here")
        return False

def main():
    print("=" * 60)
    print("AssetBrain Backend Health Check")
    print("=" * 60)

    tests = [
        ("Module Imports", test_imports),
        ("Data Files", test_data_files),
        ("ChromaDB", test_chromadb),
        ("Knowledge Graph", test_knowledge_graph),
        ("API Key", test_api_key),
    ]

    results = []
    for name, test_func in tests:
        try:
            results.append((name, test_func()))
        except Exception as e:
            print(f"✗ {name}: Unexpected error - {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ Backend is ready!")
        print("\nNext steps:")
        print("  1. Start backend: python -m uvicorn backend.main:app --reload")
        print("  2. Start frontend: cd frontend && npm run dev")
        print("  3. Open http://localhost:5173")
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
