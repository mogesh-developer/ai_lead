#!/usr/bin/env python3
"""Debug outreach message sending"""
import sys
sys.path.insert(0, '.')
import json
from db import get_db_connection, init_db

# Initialize database
init_db()

# Check if outreach_logs table exists and has data
conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("OUTREACH LOGS TABLE CHECK")
    print("="*60)
    
    # Check if table exists
    try:
        cursor.execute("SELECT COUNT(*) FROM outreach_logs")
        count = cursor.fetchone()[0]
        print(f"\n✅ outreach_logs table exists")
        print(f"   Total records: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM outreach_logs ORDER BY sent_at DESC LIMIT 5")
            columns = [desc[0] for desc in cursor.description]
            print(f"\n   Recent outreach logs:")
            for row in cursor.fetchall():
                print(f"   - {dict(zip(columns, row))}")
    except Exception as e:
        print(f"❌ Error checking outreach_logs: {e}")
    
    # Check leads with outreach_sent status
    print("\n" + "="*60)
    print("LEADS WITH OUTREACH_SENT STATUS")
    print("="*60)
    
    try:
        cursor.execute("SELECT id, name, email, status FROM leads WHERE status = 'outreach_sent' LIMIT 10")
        rows = cursor.fetchall()
        if rows:
            print(f"\n✅ Found {len(rows)} leads with outreach_sent status:")
            for row in rows:
                print(f"   - {row[0]}: {row[1]} ({row[2]}) - Status: {row[3]}")
        else:
            print(f"\n❌ No leads with outreach_sent status")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Check leads count
    print("\n" + "="*60)
    print("LEADS STATUS BREAKDOWN")
    print("="*60)
    
    try:
        cursor.execute("SELECT status, COUNT(*) as count FROM leads GROUP BY status")
        rows = cursor.fetchall()
        print(f"\n   Status breakdown:")
        for status, count in rows:
            print(f"   - {status}: {count} leads")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    cursor.close()
    conn.close()

print("\n" + "="*60)
print("CHECKING BACKEND FUNCTIONALITY")
print("="*60)

# Test the log_outreach function directly
from db import log_outreach

print("\nAttempting to log test outreach...")
try:
    # Get a sample lead first
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM leads LIMIT 1")
        result = cursor.fetchone()
        if result:
            test_lead_id = result[0]
            print(f"✅ Found test lead: ID {test_lead_id}")
            
            # Try logging outreach
            log_outreach(test_lead_id, 'email', 'Test outreach message')
            print(f"✅ Successfully logged outreach for lead {test_lead_id}")
            
            # Verify it was logged
            cursor.execute("SELECT COUNT(*) FROM outreach_logs WHERE lead_id = %s", (test_lead_id,))
            count = cursor.fetchone()[0]
            print(f"✅ Verified: {count} outreach records for this lead")
        else:
            print("❌ No leads found in database - create some leads first!")
        cursor.close()
        conn.close()
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
