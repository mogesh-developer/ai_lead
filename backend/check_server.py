import requests
import json

try:
    print("Testing connection to backend...")
    # Check if bulk-scrape-simple exists
    response = requests.post('http://localhost:5000/api/bulk-scrape-simple', json={'urls': ['https://example.com']}, timeout=5)
    print(f"Bulk Scrape Status: {response.status_code}")
    
    # Check templates
    response2 = requests.get('http://localhost:5000/api/templates', timeout=5)
    print(f"Templates Status: {response2.status_code}")
    
except Exception as e:
    print(f"Backend connection failed: {e}")
