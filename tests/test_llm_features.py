"""
Test LLM Features

Quick tests for the new Hugging Face API integration and AI features.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_ai_status():
    """Test AI connection status endpoint"""
    print("\n🔍 Testing AI Status Endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/ai-status?provider=gemini")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"   Provider: {data['provider']}")
        print(f"   Model: {data.get('model', 'N/A')}")
        print(f"   Details: {data.get('details', 'N/A')}")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False


def test_analyze():
    """Test document analysis endpoint"""
    print("\n📝 Testing Document Analysis Endpoint...")
    
    test_text = """
    An incident is any unplanned interruption to an IT service. The goal of
    incident management is to restore normal service operation as quickly as
    possible while minimizing business impact. Priority is derived from impact
    and urgency, and P1 incidents carry the tightest response and resolution
    targets.
    """

    payload = {
        "text": test_text,
        "provider": "gemini"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Analysis completed in {data.get('processing_time_ms', 0):.0f}ms")
        print(f"   Summary: {data.get('summary', 'N/A')[:100]}...")
        print(f"   Tags: {', '.join(data.get('tags', []))}")
        print(f"   Complexity: {data.get('complexity', 'N/A')}")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False


def test_query_with_followup():
    """Test query endpoint with follow-up questions"""
    print("\n💬 Testing Query with Follow-up Questions...")
    
    payload = {
        "query": "What is the resolution target for a P1 incident?",
        "k": 3,
        "provider": "gemini"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/query",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Query completed in {data.get('processing_time_ms', 0):.0f}ms")
        print(f"   Answer: {data.get('answer', 'N/A')[:100]}...")
        print(f"   Sources: {len(data.get('sources', []))}")
        
        follow_ups = data.get('follow_up_questions', [])
        if follow_ups:
            print(f"   Follow-up questions:")
            for i, q in enumerate(follow_ups, 1):
                print(f"      {i}. {q}")
        else:
            print("   ⚠️ No follow-up questions generated")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False


def main():
    print("=" * 60)
    print("🧪 Testing LLM Features")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend is not healthy. Please start the backend server.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Please start the server:")
        print("   cd /path/to/PS-Knowledge-Copilot")
        print("   source venv/bin/activate")
        print("   uvicorn app.api.main:app --reload --port 8000")
        return
    
    print("✅ Backend is running\n")
    
    # Run tests
    results = []
    results.append(("AI Status", test_ai_status()))
    results.append(("Document Analysis", test_analyze()))
    results.append(("Query with Follow-ups", test_query_with_followup()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The LLM features are working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
