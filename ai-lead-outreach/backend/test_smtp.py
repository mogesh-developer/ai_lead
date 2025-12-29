import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def test_smtp():
    """Test SMTP email sending"""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("❌ SMTP credentials not found in .env file")
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = SMTP_EMAIL  # Send to yourself for testing
        msg['Subject'] = "AI Lead Outreach - SMTP Test"

        body = """
        Hello!

        This is a test email from your AI Lead Outreach system.
        Your SMTP configuration is working correctly!

        If you received this email, your email sending functionality is ready to use.

        Best regards,
        AI Lead Outreach System
        """

        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail SMTP server
        print(f"📧 Attempting to send test email from {SMTP_EMAIL}...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("✅ Test email sent successfully!")
        print(f"📨 Check your inbox at {SMTP_EMAIL}")
        return True

    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        print("💡 Make sure:")
        print("   1. Your Gmail has 'Less secure app access' enabled OR")
        print("   2. You have generated an App Password for this application")
        print("   3. The App Password is correctly set in your .env file")
        return False

if __name__ == "__main__":
    print("🧪 Testing SMTP Configuration...")
    print(f"📧 SMTP Email: {SMTP_EMAIL}")
    print(f"🔑 SMTP Password: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'Not set'}")
    print()

    success = test_smtp()

    if success:
        print("\n🎉 SMTP configuration is working! You can now send real emails.")
    else:
        print("\n⚠️  SMTP configuration needs fixing. Check the error messages above.")