#!/usr/bin/env python3
"""Test outreach API endpoint directly"""
import sys
sys.path.insert(0, '.')
import json

print("\n" + "="*60)
print("TESTING OUTREACH API")
print("="*60)

# First, check if we can import everything
try:
    print("\n1. Checking imports...")
    from app import app, api
    print("   ✅ Flask app imported")
    
    from db import init_db
    print("   ✅ Database module imported")
    
    from helpers import send_email
    print("   ✅ Email helper imported")
    
except Exception as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Initialize database
print("\n2. Initializing database...")
try:
    init_db()
    print("   ✅ Database initialized")
except Exception as e:
    print(f"   ❌ Database init error: {e}")

# Create a test client
print("\n3. Creating test client...")
try:
    client = app.test_client()
    print("   ✅ Test client created")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test getting leads
print("\n4. Testing GET /api/get-leads...")
try:
    response = client.get('/api/get-leads')
    leads = response.get_json()
    if leads and isinstance(leads, dict) and 'leads' in leads:
        lead_list = leads['leads']
        print(f"   ✅ Found {len(lead_list)} leads")
        
        if lead_list:
            first_lead = lead_list[0]
            print(f"   Sample: {first_lead}")
        else:
            print("   ⚠️  No leads in database - need to add some first")
            sys.exit(0)
    else:
        print(f"   ❌ Unexpected response: {leads}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test sending outreach
if lead_list:
    print("\n5. Testing POST /api/send-outreach...")
    try:
        test_lead = lead_list[0]
        payload = {
            "lead_id": test_lead['id'],
            "message": f"Hi,\n\nThis is a test outreach message for {test_lead.get('company', 'your company')}.\n\nBest regards",
            "subject": f"Test message for {test_lead.get('company', 'your company')}",
            "message_type": "email"
        }
        
        print(f"   Sending to: {test_lead.get('company', 'Unknown')} ({test_lead['email']})")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        response = client.post(
            '/api/send-outreach',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        result = response.get_json()
        print(f"   Response: {result}")
        
        if response.status_code == 201:
            print(f"   ✅ Outreach sent successfully!")
            if 'email_sent' in result:
                print(f"   Email sent: {result.get('email_sent')}")
                print(f"   Email error: {result.get('email_error')}")
        else:
            print(f"   ❌ Error (status {response.status_code}): {result}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
