#!/usr/bin/env python3
"""Test email sending functionality"""

import os
import sys
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

from helpers import send_email

def test_email_sending():
    """Test sending an email"""

    print("🔧 EMAIL CONFIGURATION TEST")
    print("=" * 50)

    # Check configuration
    brevo_key = os.getenv('BREVO_API_KEY')
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))

    print(f"Brevo API Key: {'✓ SET' if brevo_key else '✗ MISSING'}")
    print(f"SMTP Email: {smtp_email or '✗ MISSING'}")
    print(f"SMTP Password: {'✓ SET' if smtp_password and smtp_password != 'your_smtp_password_or_app_password' else '✗ MISSING/PLACEHOLDER'}")
    print(f"SMTP Server: {smtp_server or '✗ MISSING'}")
    print(f"SMTP Port: {smtp_port}")
    print()

    # Test email details
    test_email = "mogeshwaran09@gmail.com"  # Send to yourself for testing
    subject = "Test Email from AI Lead Outreach"
    body = "This is a test email to verify that email sending is working correctly."

    print("📧 TESTING EMAIL SEND")
    print("=" * 50)
    print(f"To: {test_email}")
    print(f"Subject: {subject}")
    print(f"Body: {body[:100]}...")
    print()

    # Try sending
    success, error = send_email(test_email, subject, body)

    print("📊 RESULT")
    print("=" * 50)
    if success:
        print("✅ SUCCESS: Email sent successfully!")
        print("Check your inbox for the test email.")
    else:
        print("❌ FAILED: Email sending failed!")
        print(f"Error: {error}")
        print()
        print("🔍 TROUBLESHOOTING:")
        print("1. Check if BREVO_API_KEY is valid")
        print("2. Verify that your sender email is confirmed in Brevo dashboard")
        print("3. For SMTP fallback, ensure SMTP_PASSWORD is set correctly")
        print("4. Check Brevo dashboard for any error messages")

if __name__ == "__main__":
    test_email_sending()