#!/usr/bin/env python3
"""Debug outreach email sending"""

import os
import sys
import json
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

import db
from helpers import send_email

def debug_outreach():
    """Debug the outreach email sending process"""

    print("🔍 DEBUGGING OUTREACH EMAIL SENDING")
    print("=" * 50)

    # Get all leads from database
    conn = db.get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, company, phone, location FROM leads LIMIT 5")
    leads = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"📊 Found {len(leads)} leads in database:")
    for lead in leads:
        print(f"  ID {lead['id']}: {lead.get('company', 'No company')} <{lead['email']}>")

    if not leads:
        print("❌ No leads found in database!")
        return

    # Test sending to first lead
    test_lead = leads[0]
    print(f"\n📧 Testing email send to: {test_lead.get('company', 'No company')} <{test_lead['email']}>")

    # Check lead data
    full_lead = db.get_lead_by_id(test_lead['id'])
    print(f"Full lead data: {json.dumps(full_lead, indent=2, default=str)}")

    # Try sending email
    subject = "Test Outreach from AI Lead System"
    body = f"Hi,\n\nThis is a test outreach email for {test_lead.get('company', 'your company')}.\n\nBest regards,\nAI Lead Outreach"

    print(f"\n🚀 Sending email...")
    success, error = send_email(
        to_email=test_lead['email'],
        subject=subject,
        body=body,
        lead_name=test_lead.get('company', 'Unknown')
    )

    if success:
        print("✅ Email sent successfully!")
    else:
        print(f"❌ Email failed: {error}")

if __name__ == "__main__":
    debug_outreach()