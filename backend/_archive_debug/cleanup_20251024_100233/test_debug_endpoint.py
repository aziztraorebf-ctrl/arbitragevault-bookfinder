"""
Test the debug endpoint to find the exact error location.
"""

from fastapi.testclient import TestClient
import json
import sys
sys.path.insert(0, '.')

from app.main import app

client = TestClient(app)

def test_debug_endpoint():
    """Call the debug endpoint to trace the error."""
    print("🔍 CALLING DEBUG ENDPOINT")
    print("=" * 60)
    
    try:
        response = client.post("/api/v1/keepa/debug-analyze", json={"asin": "B00FLIJJSA"})
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("✅ DEBUG SUCCESS!")
                print(f"Current price: {data.get('current_price')}")
                print(f"ROI: {data.get('roi_summary')}")
                print(f"Velocity: {data.get('velocity_summary')}")
            else:
                print("❌ DEBUG FOUND ERROR:")
                print(f"Error: {data.get('error')}")
                
                print("\n🔍 DEBUG TRACE:")
                for i, trace in enumerate(data.get('debug_trace', [])):
                    print(f"  {i+1:2d}. {trace}")
                
                if 'stack_trace' in data:
                    print(f"\n📋 STACK TRACE:")
                    print(data['stack_trace'])
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug_endpoint()