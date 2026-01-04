#!/usr/bin/env python3
"""
Direct Outreach Script - Send targeted messages without AI analysis
"""
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import pymysql
from pymysql import Error

load_dotenv()

# Database connection
def get_db_connection():
    try:
        connection = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'ai_lead_outreach'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email(to_email, subject, message, company=None):
    """Send email directly"""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Lead Outreach <{SMTP_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        body = message
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_EMAIL, to_email, text)
        server.quit()

        print(f"✅ Email sent to {to_email}")
        return True, None
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False, str(e)

def get_leads_for_outreach(status='new', limit=10):
    """Get leads from database"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        query = "SELECT id, email, company, phone FROM leads WHERE status = %s LIMIT %s"
        cursor.execute(query, (status, limit))
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
        return leads
    except Exception as e:
        print(f"Error fetching leads: {e}")
        return []

def update_lead_status(lead_id, status='outreach_sent'):
    """Update lead status after sending"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE leads SET status = %s WHERE id = %s", (status, lead_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating lead status: {e}")
        return False

def main():
    print("🚀 Direct Outreach Script")
    print("=" * 50)

    # Get leads
    leads = get_leads_for_outreach('new', 5)  # Limit to 5 for testing
    if not leads:
        print("❌ No leads found to contact")
        return

    print(f"📋 Found {len(leads)} leads to contact:")
    for i, lead in enumerate(leads, 1):
        print(f"  {i}. {lead['email']} ({lead.get('company', 'Unknown Company')})")

    # Use default message for testing
    subject = "Business Partnership Opportunity"
    message = """Hi {company},

I came across your company and wanted to reach out about potential collaboration opportunities.

We specialize in AI-powered lead outreach solutions that can help businesses connect with their target audience more effectively.

Would you be interested in learning more about how we can help grow your business?

Best regards,
AI Lead Outreach Team"""

    print(f"\n📧 Subject: {subject}")
    print(f"💬 Message: {message[:100]}...")

    # Auto-send for testing
    print(f"\n⚠️  Auto-sending to {len(leads)} leads...")

    # Send emails
    sent_count = 0
    failed_count = 0

    for lead in leads:
        # Personalize message
        company_name = lead.get('company') or 'there'
        personalized_message = message.replace("{company}", company_name)

        # Send email
        success, error = send_email(
            lead['email'],
            subject,
            personalized_message,
            lead.get('company')
        )

        if success:
            sent_count += 1
            update_lead_status(lead['id'], 'outreach_sent')
        else:
            failed_count += 1
            print(f"   Error: {error}")

    print("\n📊 Results:")
    print(f"  ✅ Sent: {sent_count}")
    print(f"  ❌ Failed: {failed_count}")

if __name__ == "__main__":
    main()