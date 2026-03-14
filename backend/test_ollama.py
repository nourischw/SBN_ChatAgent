"""
Test script to verify Ollama LLM is running correctly
"""
import httpx
import sys


def check_ollama_running():
    """Check if Ollama server is running"""
    ollama_host = "http://localhost:11434"
    
    print("=" * 50)
    print("Testing Ollama LLM Connection")
    print("=" * 50)
    
    # Step 1: Check if Ollama server is running
    print("\n[1/3] Checking if Ollama server is running...")
    try:
        response = httpx.get(f"{ollama_host}/api/tags", timeout=5.0)
        if response.status_code == 200:
            print(f"✓ Ollama server is running at {ollama_host}")
            models = response.json().get("models", [])
            if models:
                print(f"✓ Available models:")
                for model in models:
                    print(f"  - {model.get('name')}")
            else:
                print("✗ No models found. You may need to pull a model.")
                print("  Run: ollama pull qwen2.5:0.5b")
            return True, models
        else:
            print(f"✗ Ollama server returned status code: {response.status_code}")
            return False, []
    except httpx.ConnectError as e:
        print(f"✗ Cannot connect to Ollama server at {ollama_host}")
        print(f"  Error: {e}")
        print("\n  Make sure Ollama is running:")
        print("  - Windows: Check if Ollama app is running in system tray")
        print("  - Or run: ollama serve")
        return False, []
    except Exception as e:
        print(f"✗ Error: {e}")
        return False, []


def test_model_chat_completion(model_name: str = "qwen2.5:0.5b"):
    """Test if the model can generate responses"""
    ollama_host = "http://localhost:11434"
    
    print(f"\n[2/3] Testing model: {model_name}")
    try:
        response = httpx.post(
            f"{ollama_host}/api/generate",
            json={
                "model": model_name,
                "prompt": "Say hello, this is a test.",
                "stream": False
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Model generated response successfully")
            print(f"  Response: {result.get('response', '')[:100]}...")
            return True
        else:
            print(f"✗ Model generation failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error testing model: {e}")
        return False


def test_backend_endpoint():
    """Test the backend's Ollama test endpoint"""
    backend_url = "http://localhost:8000/api/ollama/test"
    
    print(f"\n[3/3] Testing backend Ollama endpoint...")
    try:
        response = httpx.get(backend_url, timeout=30.0)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✓ Backend Ollama test passed")
                print(f"  Model: {result.get('model')}")
                print(f"  Response: {result.get('response', '')[:100]}...")
                return True
            else:
                print(f"✗ Backend test returned failure")
                print(f"  Error: {result.get('error')}")
                return False
        else:
            print(f"✗ Backend endpoint returned: {response.status_code}")
            print(f"  Make sure the backend is running: python backend/app.py")
            return False
    except httpx.ConnectError:
        print(f"✗ Cannot connect to backend at {backend_url}")
        print(f"  Make sure the backend is running:")
        print(f"  cd backend && python app.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    
    # Test 1: Check Ollama running
    ollama_ok, models = check_ollama_running()
    
    if not ollama_ok:
        print("\n" + "=" * 50)
        print("RESULT: Ollama is NOT running correctly")
        print("=" * 50)
        print("\nTroubleshooting:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. Start Ollama: ollama serve")
        print("3. Pull model: ollama pull qwen2.5:0.5b")
        sys.exit(1)
    
    # Test 2: Test model directly
    model_to_test = "qwen2.5:0.5b"
    if models:
        # Use first available model if qwen2.5:0.5b not found
        model_names = [m.get("name") for m in models]
        if "qwen2.5:0.5b" not in model_names:
            print(f"\n  Note: qwen2.5:0.5b not found, using first available model")
            model_to_test = model_names[0]
    
    model_ok = test_model_chat_completion(model_to_test)
    
    if not model_ok:
        print("\n" + "=" * 50)
        print("RESULT: Model test FAILED")
        print("=" * 50)
        print("\nTroubleshooting:")
        print(f"1. Pull the model: ollama pull {model_to_test}")
        sys.exit(1)
    
    # Test 3: Test backend endpoint (optional)
    print("\n" + "-" * 50)
    print("Note: Backend test is optional (requires backend running)")
    print("-" * 50)
    backend_ok = test_backend_endpoint()
    
    # Summary
    print("\n" + "=" * 50)
    if ollama_ok and model_ok:
        print("RESULT: ✓ Ollama and LLM are working correctly!")
    else:
        print("RESULT: ✗ Some tests failed")
    print("=" * 50)
    
    if not backend_ok:
        print("\nTip: Start the backend to test full integration:")
        print("  cd backend && python app.py")
        print("  Then visit: http://localhost:8000/api/ollama/test")
    
    return 0 if (ollama_ok and model_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
