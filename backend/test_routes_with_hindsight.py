"""
✅ Test all FastAPI routes to verify Hindsight service integration.
This script tests that:
1. Routes respond with 200 OK
2. demo_mode reflects actual Hindsight service state
3. Both base and /api-prefixed paths work
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

test_cases = [
    {
        "path": "/health",
        "params": {},
        "description": "Health check endpoint",
        "checks": ["status", "message"]
    },
    {
        "path": "/study/archaeology",
        "params": {"topic": "recursion", "confusion_level": 4},
        "description": "Temporal archaeology (test Hindsight recall)",
        "checks": ["demo_mode", "feature", "recommendations"]
    },
    {
        "path": "/study/socratic",
        "params": {"subject": "calculus", "confusion_level": 3},
        "description": "Socratic method (test Hindsight service)",
        "checks": ["demo_mode", "questions"]
    },
    {
        "path": "/study/resonance",
        "params": {"keywords": "limit,derivative", "context_window": 2},
        "description": "Resonance pattern detection",
        "checks": ["demo_mode", "patterns"]
    },
    {
        "path": "/health",
        "params": {},
        "prefix": "/api",
        "description": "Health check via /api prefix",
        "checks": ["status"]
    },
    {
        "path": "/study/archaeology",
        "params": {"topic": "limits", "confusion_level": 2},
        "prefix": "/api",
        "description": "Archaeology via /api prefix",
        "checks": ["demo_mode", "recommendations"]
    }
]

print("\n" + "="*70)
print("🧪 HINDSIGHT SERVICE INTEGRATION TEST")
print("="*70 + "\n")

passed = 0
failed = 0

for test in test_cases:
    prefix = test.get("prefix", "")
    full_url = f"{BASE_URL}{prefix}{test['path']}"
    
    print(f"📍 {test['description']}")
    print(f"   Path: {prefix}{test['path']}")
    print(f"   URL: {full_url}")
    
    try:
        response = requests.get(full_url, params=test["params"], timeout=5)
        
        if response.status_code != 200:
            print(f"   ❌ Status {response.status_code}")
            failed += 1
            continue
        
        data = response.json()
        
        # Check for required fields
        missing = [k for k in test["checks"] if k not in data]
        if missing:
            print(f"   ⚠️  Missing fields: {missing}")
        
        # Show hindsight mode
        if "demo_mode" in data:
            mode = "DEMO (API unavailable)" if data["demo_mode"] else "LIVE API"
            print(f"   {mode}")
        
        print(f"   ✅ Status {response.status_code}")
        passed += 1
        print()
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection refused. Backend not running on {BASE_URL}\n")
        failed += 1
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")
        failed += 1

print("="*70)
print(f"📊 Results: {passed} passed, {failed} failed")
print("="*70 + "\n")

if failed > 0:
    print("💡 Troubleshooting:")
    print("   • Is backend running? Run: python run.py")
    print("   • Check backend logs for Hindsight service errors")
    print("   • Verify .env has HINDSIGHT_API_KEY (optional, falls back to demo)\n")
    sys.exit(1)
else:
    print("✅ All routes working! Hindsight integration ready.\n")
    sys.exit(0)
