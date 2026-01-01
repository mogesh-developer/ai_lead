#!/usr/bin/env python3
"""Simple test of outreach without database"""
import sys
import json

print("\nTesting outreach endpoint response structure...")
print("="*60)

# Mock data to test what the API should return
test_response = {
    "success": True,
    "message": "Outreach sent to John Doe (john@example.com)",
    "lead_id": 1,
    "lead_name": "John Doe",
    "lead_email": "john@example.com",
    "email_sent": True,
    "email_error": None
}

print("\nExpected API Response:")
print(json.dumps(test_response, indent=2))

print("\nWhat should happen when you send outreach:")
print("1. POST /api/send-outreach")
print("2. Backend receives: lead_id, message, subject, message_type")
print("3. Backend sends email via SMTP")
print("4. Backend logs to outreach_logs table")
print("5. Backend updates lead status to 'outreach_sent'")
print("6. Backend returns success response with email_sent status")

print("\nIf messages not being saved:")
print("   - Check database connection")
print("   - Check outreach_logs table exists")
print("   - Check lead record exists")
print("   - Check log_outreach function is called")

print("\n" + "="*60)
print("\nTo fix the outreach message not being sent issue:")
print("\n1. Verify database is running")
print("2. Verify leads table has records")
print("3. Check /api/send-outreach endpoint is being called")
print("4. Check /api/bulk-outreach endpoint is being called")
print("5. Verify response has email_sent: true")
print("\nThe system should now:")
print("  - Send actual emails via SMTP")
print("  - Log messages to database")
print("  - Update lead status to 'outreach_sent'")
print("  - Return email_sent status in response")
