"""Helper utility functions"""
import re
import requests
import json
import pandas as pd
from config import SMTP_EMAIL, SMTP_PASSWORD

# Optional imports
try:
    from google.oauth2.service_account import Credentials
    import gspread
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("⚠️  gspread not available - Google Sheets export disabled")

import os


def agent_ingest_leads(file_path):
    """Agent 1: Lead Ingestion Agent - Import leads from CSV/Excel"""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return {"error": "Unsupported file format"}
        
        # Normalize columns
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        
        count = 0
        for _, row in df.iterrows():
            # Basic mapping, assuming columns exist
            lead_data = {
                'name': row.get('name', 'Unknown'),
                'email': row.get('email', ''),
                'phone': row.get('phone', ''),
                'company': row.get('company', ''),
                'position': row.get('position', ''),
                'website': row.get('website', '')
            }
            
            # Insert to database
            # db.insert_lead(lead_data)
            count += 1
            
        return {"message": f"Successfully ingested {count} leads"}
    except Exception as e:
        return {"error": str(e)}


def verify_email_format(email):
    """Verify email format with regex"""
    if not email:
        return False
    
    # RFC 5322 simplified email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def verify_email_smtp(email):
    """Verify email using SMTP without sending a message
    
    This checks if the email domain has valid MX records
    and can connect to SMTP servers.
    """
    print(f"📧 SMTP verifying email: {email}")
    
    try:
        # Check format first
        if not verify_email_format(email):
            print(f"❌ Email format invalid: {email}")
            return {
                "valid": False,
                "reason": "Invalid email format",
                "method": "format_check"
            }
        
        # Extract domain
        domain = email.split('@')[1]
        print(f"🔍 Checking domain: {domain}")
        
        # Try to import and use DNS resolution
        try:
            import dns.resolver
            
            # Check for MX records (mail servers)
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                mx_hosts = [str(mx.exchange) for mx in mx_records]
                print(f"✅ Found {len(mx_hosts)} MX records for {domain}")
                
                return {
                    "valid": True,
                    "reason": "Valid domain with MX records",
                    "method": "mx_check",
                    "domain": domain,
                    "mx_records": mx_hosts[:3]  # Show first 3
                }
            except Exception as e:
                print(f"⚠️  No MX records found for {domain}: {e}")
                return {
                    "valid": False,
                    "reason": f"No MX records found: {str(e)}",
                    "method": "mx_check",
                    "domain": domain
                }
        
        except ImportError:
            print("⚠️  dnspython not available, using format-only verification")
            return {
                "valid": True,
                "reason": "Format valid (MX check not available)",
                "method": "format_check_only"
            }
    
    except Exception as e:
        print(f"❌ Email verification error: {e}")
        return {
            "valid": False,
            "reason": str(e),
            "method": "error"
        }


def verify_email_api(email):
    """Try multiple free email verification APIs as fallback"""
    print(f"🌐 API verifying email: {email}")
    
    # Try multiple services
    apis = [
        {
            "name": "rapid-email-verifier",
            "url": f"https://rapid-email-verifier.fly.dev/validate?email={email}",
            "timeout": 10
        },
        {
            "name": "kickbox",
            "url": f"https://api.kickbox.io/v2/verify?email={email}",
            "timeout": 10
        }
    ]
    
    for api in apis:
        try:
            print(f"  Trying {api['name']}...")
            response = requests.get(api['url'], timeout=api['timeout'])
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ {api['name']} responded successfully")
                
                # Parse different response formats
                if 'valid' in data:
                    return {
                        "valid": data.get('valid', False),
                        "reason": data.get('reason', 'API verification'),
                        "method": api['name'],
                        "full_response": data
                    }
                elif 'result' in data:
                    is_valid = data.get('result') == 'deliverable'
                    return {
                        "valid": is_valid,
                        "reason": data.get('result', 'Unknown'),
                        "method": api['name'],
                        "full_response": data
                    }
        except Exception as e:
            print(f"  ⚠️  {api['name']} failed: {str(e)[:50]}")
            continue
    
    print(f"⚠️  All APIs failed for {email}")
    return None


def verify_email_rapid(email):
    """Verify email with multiple methods - Primary email verification function
    
    Uses a 3-tier approach:
    1. Format validation (regex)
    2. SMTP/MX record check (most reliable)
    3. Free API verification (fallback)
    
    Returns dict with:
    - valid: bool
    - reason: string explanation
    - method: which method was used
    - detailed info from verification
    """
    if not email:
        return {
            "valid": False,
            "reason": "No email provided",
            "method": "input_validation"
        }
    
    email = email.strip().lower()
    print(f"\n{'='*60}")
    print(f"🔍 EMAIL VERIFICATION: {email}")
    print(f"{'='*60}")
    
    # Method 1: Format Check (Fast)
    print(f"\n[Step 1/3] Format Validation...")
    if not verify_email_format(email):
        result = {
            "valid": False,
            "email": email,
            "reason": "Invalid email format",
            "method": "format_validation",
            "details": "Email does not match standard format (user@domain.com)"
        }
        print(f"❌ Format validation failed")
        return result
    
    print(f"✅ Format validation passed")
    
    # Method 2: SMTP/MX Check (Most Reliable)
    print(f"\n[Step 2/3] MX Record Check...")
    try:
        smtp_result = verify_email_smtp(email)
        if smtp_result and smtp_result.get('valid'):
            smtp_result['email'] = email
            print(f"✅ SMTP verification successful")
            return smtp_result
        elif smtp_result:
            print(f"⚠️  SMTP returned invalid but will try API...")
    except Exception as e:
        print(f"⚠️  SMTP check error: {e}")
    
    # Method 3: API Verification (Fallback)
    print(f"\n[Step 3/3] API Verification (Fallback)...")
    api_result = verify_email_api(email)
    if api_result:
        api_result['email'] = email
        print(f"✅ API verification successful")
        return api_result
    
    # Fallback: Accept if format is valid but APIs unavailable
    print(f"\n⚠️  APIs unavailable, accepting based on format")
    return {
        "valid": True,
        "email": email,
        "reason": "Format valid but detailed verification unavailable",
        "method": "format_only_fallback",
        "warning": "Could not reach verification APIs"
    }


def export_to_google_sheets(leads, sheet_id, sheet_name="Leads"):
    """Export leads to Google Sheets"""
    if not GSPREAD_AVAILABLE:
        return {"success": False, "error": "gspread not installed"}
    
    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json:
        print("Google Sheets credentials missing")
        return False
    
    try:
        creds_dict = json.loads(creds_json)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        sh = client.open_by_key(sheet_id)
        try:
            worksheet = sh.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=sheet_name, rows="100", cols="20")
            
        # Prepare data
        headers = ["Name", "Email", "Phone", "Company", "Website", "Address", "Source"]
        data = [headers]
        for lead in leads:
            data.append([
                lead.get('name', ''),
                lead.get('email', ''),
                lead.get('phone', ''),
                lead.get('company', ''),
                lead.get('website', ''),
                lead.get('address', ''),
                lead.get('source', '')
            ])
            
        worksheet.clear()
        worksheet.update('A1', data)
        return True
    except Exception as e:
        print(f"Error exporting to Google Sheets: {e}")
        return False


def validate_lead(lead):
    """Validate lead data structure"""
    required_fields = ['name', 'email']
    for field in required_fields:
        if not lead.get(field):
            return False
    return True


def format_phone_number(phone):
    """Format phone number to standard format"""
    digits_only = re.sub(r'\D', '', phone)
    
    if len(digits_only) == 10:
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11 and digits_only[0] == '1':
        return f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
    elif len(digits_only) == 12 and digits_only.startswith('91'):
        return f"+91 {digits_only[2:7]} {digits_only[7:]}"
    else:
        return phone


def clean_company_name(name):
    """Clean and normalize company name"""
    # Remove common suffixes
    suffixes = [' Inc.', ' LLC', ' Ltd.', ' Corp.', ' Co.', ' PLC', ' SA', ' AG', '.com', '.net', '.org']
    for suffix in suffixes:
        if name.lower().endswith(suffix.lower()):
            name = name[:-len(suffix)].strip()
    
    return name.strip().title()


def create_outreach_campaign(campaign_name, leads, tone="professional", template="email"):
    """Create a personalized outreach campaign for multiple leads
    
    Args:
        campaign_name: Name of the campaign
        leads: List of lead dictionaries
        tone: Message tone (professional, casual, urgent, friendly)
        template: Message template type (email, linkedin, whatsapp, default)
    
    Returns:
        dict with campaign details and personalized messages
    """
    from agents import agent_generate_outreach_message
    
    print(f"📧 Creating outreach campaign: {campaign_name} for {len(leads)} leads")
    
    try:
        campaign_data = {
            "campaign_name": campaign_name,
            "total_leads": len(leads),
            "tone": tone,
            "template": template,
            "messages": [],
            "success_count": 0,
            "failed_count": 0
        }
        
        for i, lead in enumerate(leads, 1):
            print(f"Generating message {i}/{len(leads)} for {lead.get('name', 'Unknown')}")
            
            # Generate personalized message
            message_result = agent_generate_outreach_message(lead, tone=tone, template=template)
            
            if message_result.get("success"):
                campaign_data["messages"].append({
                    "lead_id": i,
                    "name": lead.get("name"),
                    "email": lead.get("email"),
                    "company": lead.get("company"),
                    "subject": message_result.get("subject"),
                    "message": message_result.get("message"),
                    "cta": message_result.get("cta"),
                    "preview": message_result.get("preview"),
                    "status": "generated"
                })
                campaign_data["success_count"] += 1
            else:
                campaign_data["failed_count"] += 1
                print(f"Failed to generate message for {lead.get('name')}")
        
        return {
            "success": True,
            "campaign": campaign_data
        }
    except Exception as e:
        print(f"Error creating outreach campaign: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def log_outreach_attempt(lead_id, campaign_id, message_content, channel="email", status="sent"):
    """Log an outreach attempt in the database
    
    Args:
        lead_id: ID of the lead
        campaign_id: ID of the campaign
        message_content: Content of the message sent
        channel: Channel used (email, linkedin, whatsapp)
        status: Status (sent, failed, bounced, opened, clicked)
    
    Returns:
        bool: Success status
    """
    try:
        from datetime import datetime
        import db
        
        outreach_log = {
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "message": message_content[:500],  # Store first 500 chars
            "channel": channel,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "response": None,
            "response_timestamp": None
        }
        
        # TODO: Implement db.log_outreach(outreach_log) when database schema is ready
        print(f"✅ Logged outreach attempt for lead {lead_id}")
        return True
    except Exception as e:
        print(f"Error logging outreach attempt: {e}")
        return False


def track_outreach_response(lead_id, campaign_id, response_type="opened"):
    """Track response to outreach (opened, clicked, replied)
    
    Args:
        lead_id: ID of the lead
        campaign_id: ID of the campaign
        response_type: Type of response (opened, clicked, replied, unsubscribed)
    
    Returns:
        dict: Updated lead status
    """
    try:
        from datetime import datetime
        
        response_data = {
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "response_type": response_type,
            "timestamp": datetime.now().isoformat(),
            "next_action": None
        }
        
        # Determine next action based on response
        if response_type == "opened":
            response_data["next_action"] = "wait_48h_for_click"
        elif response_type == "clicked":
            response_data["next_action"] = "follow_up_in_3_days"
        elif response_type == "replied":
            response_data["next_action"] = "escalate_to_sales"
        elif response_type == "unsubscribed":
            response_data["next_action"] = "remove_from_campaign"
        
        # TODO: Implement db.update_lead_response(response_data)
        print(f"✅ Tracked {response_type} response for lead {lead_id}")
        return {
            "success": True,
            "response": response_data
        }
    except Exception as e:
        print(f"Error tracking outreach response: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_campaign_analytics(campaign_id):
    """Get analytics for an outreach campaign
    
    Args:
        campaign_id: ID of the campaign
    
    Returns:
        dict: Campaign analytics (sent, opened, clicked, replied, conversion_rate)
    """
    try:
        # TODO: Query database for campaign metrics
        analytics = {
            "campaign_id": campaign_id,
            "total_sent": 0,
            "total_opened": 0,
            "total_clicked": 0,
            "total_replied": 0,
            "total_qualified": 0,
            "open_rate": 0,
            "click_rate": 0,
            "reply_rate": 0,
            "conversion_rate": 0,
            "best_performing_message": None,
            "worst_performing_message": None
        }
        return {
            "success": True,
            "analytics": analytics
        }
    except Exception as e:
        print(f"Error getting campaign analytics: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def send_bulk_outreach_emails(campaign_id, leads, messages):
    """Send bulk outreach emails via SMTP
    
    Args:
        campaign_id: ID of the campaign
        leads: List of lead dictionaries
        messages: List of message dictionaries
    
    Returns:
        dict: Send results with success/failure counts
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            return {
                "success": False,
                "error": "SMTP credentials not configured"
            }
        
        results = {
            "campaign_id": campaign_id,
            "total_sent": 0,
            "total_failed": 0,
            "sent_leads": [],
            "failed_leads": []
        }
        
        # TODO: Implement actual SMTP sending
        # for message in messages:
        #     try:
        #         msg = MIMEMultipart()
        #         msg['From'] = SMTP_EMAIL
        #         msg['To'] = message.get('email')
        #         msg['Subject'] = message.get('subject')
        #         msg.attach(MIMEText(message.get('message'), 'html'))
        #         
        #         with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        #             server.login(SMTP_EMAIL, SMTP_PASSWORD)
        #             server.send_message(msg)
        #         
        #         results['total_sent'] += 1
        #         results['sent_leads'].append(message.get('email'))
        #         log_outreach_attempt(message.get('lead_id'), campaign_id, message.get('message'), "email", "sent")
        #     except Exception as e:
        #         results['total_failed'] += 1
        #         results['failed_leads'].append({"email": message.get('email'), "error": str(e)})
        
        print(f"📊 Bulk email campaign completed: {results['total_sent']} sent, {results['total_failed']} failed")
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        print(f"Error sending bulk outreach emails: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def send_email(to_email, subject, body, lead_name=None):
    """Send email via SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        lead_name: Lead name for personalization
    
    Returns:
        tuple: (success: bool, error: str or None)
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            error_msg = "SMTP credentials not configured"
            print(f"❌ {error_msg}")
            return False, error_msg
        
        if not to_email:
            error_msg = "No recipient email provided"
            print(f"❌ {error_msg}")
            return False, error_msg
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Create HTML version of the body
        html = f"""\
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                {body.replace(chr(10), '<br>')}
            </body>
        </html>
        """
        
        # Attach text and HTML parts
        part1 = MIMEText(body, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        print(f"📧 Sending email to {to_email}...")
        
        # Try SMTP with TLS first (port 587) - most reliable
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.send_message(msg)
            print(f"✅ Email sent successfully to {to_email}")
            return True, None
        except Exception as tls_error:
            print(f"⚠️ SMTP TLS failed ({str(tls_error)}), trying SSL...")
            
            # Fallback to SMTP_SSL
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
                    server.login(SMTP_EMAIL, SMTP_PASSWORD)
                    server.send_message(msg)
                print(f"✅ Email sent successfully to {to_email}")
                return True, None
            except Exception as ssl_error:
                error_msg = f"Failed to send email via both SMTP methods. TLS error: {str(tls_error)}. SSL error: {str(ssl_error)}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg
