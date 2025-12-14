import os
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def health_check():
    r = requests.get(f"{API_BASE_URL}/api/health/")
    r.raise_for_status()
    return r.json()
