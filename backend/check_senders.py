#!/usr/bin/env python3
"""Check Brevo verified senders"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('BREVO_API_KEY')
if not api_key:
    print("❌ BREVO_API_KEY not found")
    exit(1)

headers = {
    'api-key': api_key,
    'Content-Type': 'application/json'
}

try:
    response = requests.get('https://api.brevo.com/v3/senders', headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("✅ Verified Senders:")
        for sender in data.get('senders', []):
            print(f"  - {sender.get('email')} (ID: {sender.get('id')}, Active: {sender.get('active')})")
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")