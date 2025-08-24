#!/usr/bin/env python3
import time
import requests

print("⏳ Attente du serveur...")
time.sleep(4)

print("🧪 Test Health AutoSourcing...")
try:
    response = requests.get("http://localhost:8000/api/v1/autosourcing/health", timeout=10)
    if response.status_code == 200:
        health = response.json()
        print(f"✅ {health['status']} - {health['module']} v{health['version']}")
        print("🎉 Module AutoSourcing opérationnel!")
    else:
        print(f"❌ Status: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")