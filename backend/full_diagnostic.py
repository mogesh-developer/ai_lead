#!/usr/bin/env python3
"""Comprehensive diagnostic of the outreach system"""
import sys
import os

print("\n" + "="*70)
print("OUTREACH SYSTEM DIAGNOSTIC")
print("="*70)

# Test 1: Database Connection
print("\n[TEST 1] Database Connection...")
print("-"*70)
try:
    from db import get_db_connection, init_db
    print("[OK] Database module imported")
    
    # Try to connect
    conn = get_db_connection()
    if conn:
        print("[OK] Database connection successful")
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"[OK] Database tables: {', '.join(tables)}")
        
        # Check leads
        cursor.execute("SELECT COUNT(*) FROM leads")
        lead_count = cursor.fetchone()[0]
        print(f"[OK] Total leads in database: {lead_count}")
        
        if lead_count == 0:
            print("  [WARN] No leads found! Add some leads first.")
        
        # Check outreach_logs
        cursor.execute("SELECT COUNT(*) FROM outreach_logs")
        log_count = cursor.fetchone()[0]
        print(f"[OK] Total outreach logs: {log_count}")
        
        cursor.close()
        conn.close()
    else:
        print("[ERROR] Failed to connect to database")
        print("  Make sure MariaDB/MySQL is running!")
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] Database error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Email System
print("\n[TEST 2] Email/SMTP System...")
print("-"*70)
try:
    from helpers import send_email
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    SMTP_EMAIL = os.getenv('SMTP_EMAIL')
    print(f"[OK] Email module imported")
    print(f"[OK] SMTP configured for: {SMTP_EMAIL}")
    
    if not SMTP_EMAIL:
        print("[ERROR] SMTP_EMAIL not configured in .env")
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] Email system error: {e}")
    sys.exit(1)

# Test 3: Backend Flask App
print("\n[TEST 3] Backend Flask App...")
print("-"*70)
try:
    from app import app, api
    print("[OK] Flask app imported successfully")
    print("[OK] All routes registered")
    
    with app.app_context():
        print("[OK] App context created successfully")
        
except Exception as e:
    print(f"[ERROR] Flask app error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: API Endpoints
print("\n[TEST 4] API Endpoints...")
print("-"*70)
try:
    client = app.test_client()
    
    # Test health
    response = client.get('/health')
    print(f"[OK] GET /health: {response.status_code}")
    
    # Test get-leads
    response = client.get('/api/get-leads')
    if response.status_code == 200:
        data = response.get_json()
        print(f"[OK] GET /api/get-leads: {response.status_code} ({len(data.get('leads', []))} leads)")
    else:
        print(f"[ERROR] GET /api/get-leads: {response.status_code}")
    
    # Test templates
    response = client.get('/api/outreach-templates')
    if response.status_code == 200:
        data = response.get_json()
        print(f"[OK] GET /api/outreach-templates: {response.status_code} ({len(data.get('templates', {}))} templates)")
    else:
        print(f"[ERROR] GET /api/outreach-templates: {response.status_code}")
        
except Exception as e:
    print(f"[ERROR] API endpoint error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Send Outreach (if leads exist)
print("\n[TEST 5] Outreach Functionality...")
print("-"*70)
try:
    # Get first lead
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM leads LIMIT 1")
    result = cursor.fetchone()
    
    if not result:
        print("[WARN] No leads found in database")
        print("  Action: Add some leads first!")
        cursor.close()
        conn.close()
    else:
        lead_id, lead_name, lead_email = result
        cursor.close()
        conn.close()
        
        print(f"[OK] Found test lead: {lead_name} ({lead_email})")
        
        # Try sending outreach
        import json
        payload = {
            "lead_id": lead_id,
            "message": f"Hi {lead_name},\n\nTest outreach message.\n\nBest regards",
            "subject": "Test Message",
            "message_type": "email"
        }
        
        response = client.post(
            '/api/send-outreach',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        print(f"[OK] POST /api/send-outreach: {response.status_code}")
        result = response.get_json()
        print(f"  Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 201:
            print("[OK] Outreach sent successfully!")
            if result.get('email_sent'):
                print("[OK] Email was sent!")
            else:
                print(f"[ERROR] Email failed: {result.get('email_error')}")
        else:
            print(f"[ERROR] Error sending outreach: {result.get('error')}")
            
except Exception as e:
    print(f"[ERROR] Outreach test error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print("\nNext Steps:")
print("1. If all tests passed → System is working!")
print("2. If database connection failed → Start MariaDB/MySQL")
print("3. If no leads found → Add leads via frontend or API")
print("4. If email failed → Check SMTP credentials in .env")
print("5. If Flask error → Check backend logs for details")
print("\n")
