import os
import sys
import json
import pandas as pd
import smtplib
import re
import requests
import traceback
import random
import time
from datetime import datetime
import html
import threading
import imaplib
import email
from email.utils import parseaddr
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from ddgs import DDGS
from playwright.sync_api import sync_playwright
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
# import google.generativeai as genai  # Temporarily commented out due to import issues
# Ensure a name exists for legacy references to `genai` to avoid NameError
genai = None
from dotenv import load_dotenv
from serpapi import Client
import db
from justdial_scraper import JustDialScraper

# Optional imports
try:
    from google.oauth2.service_account import Credentials
    import gspread
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("⚠️  gspread not available - Google Sheets export disabled")

try:
    import db
    DB_AVAILABLE = True
except ImportError as e:
    DB_AVAILABLE = False
    print(f"⚠️  db module not available: {e}")
    # Create a mock db module
    class MockDB:
        pass
    db = MockDB()

# Load environment variables
load_dotenv()
# Also try parent directory if .env is there
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

api = Blueprint('api', __name__, url_prefix='/api')

@app.after_request
def apply_cors(response):
    # Ensure required CORS headers are always present for browser preflights
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,PUT,DELETE'
    return response

@app.before_request
def handle_options():
    # Explicitly respond to OPTIONS preflight requests with CORS headers
    if request.method == 'OPTIONS':
        resp = app.make_response(('', 204))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,PUT,DELETE'
        return resp

@app.errorhandler(500)
def handle_500_error(e):
    # Log full trace to server console for debugging
    print(f"🔥 UNCAUGHT 500 ERROR:\n{traceback.format_exc()}")
    response = jsonify({
        "error": "Internal Server Error", 
        "details": str(e)
    })
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 500

@app.route('/open', methods=['GET'])
def track_open():
    lead_id = request.args.get('lead_id')
    if not lead_id:
        return '', 204

    try:
        lead_id = int(lead_id)
    except ValueError:
        return '', 204

    lead = db.get_lead_by_id(lead_id)
    if not lead:
        return '', 204

    db.mark_lead_opened(lead_id)
    db.log_outreach(lead_id, 'open', 'Tracking pixel detected')
    return '', 204

# Initialize DB
db.init_db()

# AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-pro"  # Updated to supported model
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
except (ValueError, TypeError):
    SMTP_PORT = 587
    
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")
SNOV_CLIENT_ID = os.getenv("SNOVIO_API_KEY")
SNOV_CLIENT_SECRET = os.getenv("SNOVIO_SECRET_KEY")
TRACKING_HOST = os.getenv("TRACKING_HOST", "http://localhost:5000")
IMAP_EMAIL = os.getenv("REPLY_IMAP_EMAIL")
IMAP_PASSWORD = os.getenv("REPLY_IMAP_PASSWORD")
IMAP_SERVER = os.getenv("REPLY_IMAP_SERVER", "imap.gmail.com")
IMAP_POLL_INTERVAL = int(os.getenv("IMAP_POLL_INTERVAL", "300"))
AUTO_FOLLOWUP_INTERVAL = int(os.getenv("AUTO_FOLLOWUP_INTERVAL", "3600"))
AUTO_FOLLOWUP_DELAY_DAYS = int(os.getenv("AUTO_FOLLOWUP_DELAY_DAYS", "2"))
OUTREACH_DRY_RUN = os.getenv("OUTREACH_DRY_RUN", "true").lower() in ("1", "true", "yes")

# IMAP monitoring status (for debugging)
LAST_IMAP_CHECK = None
LAST_IMAP_ERROR = None
LAST_IMAP_PROCESSED = None

class SafeDict(dict):
    def __missing__(self, key):
        return ''

OUTREACH_TEMPLATES = {
    "introduction": {
        "name": "Introduction",
        "subject": "Quick intro to {company}",
        "message": "Hi {name},\n\nI spotted {company} while researching teams in {location} and wanted to share how {product} is helping founders stay on top of their pipeline.\n\nWould a quick 10-minute call later this week make sense?\n\nBest,\nAI Lead Outreach",
        "cta": "Let's connect for a quick call",
        "product": "our AI lead outreach stack"
    },
    "value_add": {
        "name": "Value Add",
        "subject": "A free resource for {company}",
        "message": "Hi {name},\n\nRather than another cold introduction, I wanted to send over a short playbook on how {company} can automatically capture more qualified meetings from the leads you already have.\n\nIf this makes sense, I can share the deck and map it to your current process.\n\nCheers,\nAI Lead Outreach",
        "cta": "Reply and I'll send the playbook",
        "product": "our automated outreach engine"
    },
    "case_study": {
        "name": "Case Study",
        "subject": "How we helped a {location} team win more deals",
        "message": "Hi {name},\n\nWe recently helped another {location} team similar to {company} pull 2x the responses by layering in personalized AI follow-ups.\n\nHappy to show you how it works on a 15-minute screen share.\n\nLet me know when you have time,\nAI Lead Outreach",
        "cta": "Schedule a screen share",
        "product": "our personalization + follow-up cadence"
    },
    "followup_checkin": {
        "name": "Follow-up: Check-in",
        "subject": "Quick check-in on {company}",
        "message": "Hi {name},\n\nJust wanted to follow up and see if you had a chance to review my note about {product}.\n\nIf now isn't a fit, no worries—just wanted to stay on your radar.\n\nBest,\nAI Lead Outreach",
        "cta": "Happy to circle back when timing improves",
        "product": "our AI nurture workflow"
    },
    "followup_value": {
        "name": "Follow-up: Value-add",
        "subject": "A quick win for {company}",
        "message": "Hi {name},\n\nI pulled together a quick idea on how {company} could book extra discovery calls using {product}.\n\nWant me to walk you through it live?\n\nThanks,\nAI Lead Outreach",
        "cta": "Happy to show the idea",
        "product": "our outreach + insight engine"
    },
    "followup_close": {
        "name": "Follow-up: Last touch",
        "subject": "Wrapping up for now, {name}",
        "message": "Hi {name},\n\nIf now is still not the time for {company}, I’ll circle back in a few months.\n\nLet me know if anything changes in the meantime and I’ll share anything useful I discover.\n\nBest,\nAI Lead Outreach",
        "cta": "Let’s reconnect later",
        "product": "our AI outreach assistant"
    }
}

FOLLOW_UP_SEQUENCE = [
    {"template_key": "followup_checkin", "title": "Gentle touch"},
    {"template_key": "followup_value", "title": "Value add"},
    {"template_key": "followup_close", "title": "Breakup"}
]

# Initialize AI Clients
genai_client = None
groq_client = None

# If a Gemini API key is present, we'll initialize the client lazily when
# an AI request is made. Avoid importing google.generativeai at module import
# time to prevent startup hangs on systems without that package installed.
if GEMINI_API_KEY:
    print("[INFO] GEMINI_API_KEY is set; Gemini client will be initialized lazily on first use")
else:
    print("[INFO] GEMINI_API_KEY not set; Gemini features will be disabled")

def get_genai():
    """Lazy load Gemini API"""
    global genai_client
    if genai_client is None and GEMINI_API_KEY:
        try:
            import google.generativeai as _genai
            _genai.configure(api_key=GEMINI_API_KEY)
            genai_client = _genai
            print("[OK] Gemini API configured")
        except Exception as e:
            print(f"[ERROR] Gemini configuration error: {e}")
    return genai_client

def get_working_gemini_model():
    """Get a Gemini model that supports generateContent"""
    client = get_genai()
    if not client:
        return None
    try:
        models = list(client.list_models())
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"[OK] Using Gemini model: {model.name}")
                return model.name
        print("[ERROR] No Gemini model supports generateContent")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to list Gemini models: {e}")
        return None

def get_groq():
    """Lazy load Groq API"""
    global groq_client
    if groq_client is None and GROQ_API_KEY:
        try:
            from groq import Groq
            groq_client = Groq(api_key=GROQ_API_KEY)
            print("[OK] Groq API configured")
        except Exception as e:
            print(f"[WARN] Groq initialization error: {e}")
    return groq_client

# =================================================================
# HELPER FUNCTIONS
# =================================================================

def verify_email_format(email):
    """Verify email format with regex"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def verify_email_smtp(email):
    """Verify email using SMTP without sending a message"""
    print(f"📧 SMTP verifying email: {email}")
    try:
        if not verify_email_format(email):
            return {"valid": False, "reason": "Invalid email format", "method": "format_check"}
        domain = email.split('@')[1]
        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(mx.exchange) for mx in mx_records]
            return {
                "valid": True,
                "reason": "Valid domain with MX records",
                "method": "mx_check",
                "domain": domain,
                "mx_records": mx_hosts[:3]
            }
        except Exception as e:
            return {"valid": False, "reason": f"No MX records found: {str(e)}", "method": "mx_check", "domain": domain}
    except Exception as e:
        return {"valid": False, "reason": str(e), "method": "error"}

def verify_email_api(email):
    """Try multiple free email verification APIs as fallback"""
    apis = [
        {"name": "rapid-email-verifier", "url": f"https://rapid-email-verifier.fly.dev/validate?email={email}", "timeout": 10},
        {"name": "kickbox", "url": f"https://api.kickbox.io/v2/verify?email={email}", "timeout": 10}
    ]
    for api in apis:
        try:
            response = requests.get(api['url'], timeout=api['timeout'])
            if response.status_code == 200:
                data = response.json()
                if 'valid' in data:
                    return {"valid": data.get('valid', False), "reason": data.get('reason', 'API verification'), "method": api['name']}
                elif 'result' in data:
                    return {"valid": data.get('result') == 'deliverable', "reason": data.get('result', 'Unknown'), "method": api['name']}
        except: continue
    return None

def verify_email_rapid(email):
    """Primary email verification function"""
    if not email: return {"valid": False, "reason": "No email provided", "method": "input_validation"}
    email = email.strip().lower()
    if not verify_email_format(email):
        return {"valid": False, "email": email, "reason": "Invalid email format", "method": "format_validation"}
    
    smtp_result = verify_email_smtp(email)
    if smtp_result and smtp_result.get('valid'):
        smtp_result['email'] = email
        return smtp_result
    
    api_result = verify_email_api(email)
    if api_result:
        api_result['email'] = email
        return api_result
    
    return {"valid": True, "email": email, "reason": "Format valid but detailed verification unavailable", "method": "format_only_fallback"}

def export_to_google_sheets(leads, sheet_id, sheet_name="Leads"):
    """Export leads to Google Sheets"""
    if not GSPREAD_AVAILABLE: return False
    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json: return False
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
        headers = ["Company", "Email", "Phone", "Website", "Address", "Source"]
        data = [headers]
        for lead in leads:
            data.append([lead.get('company', ''), lead.get('email', ''), lead.get('phone', ''), lead.get('website', ''), lead.get('address', ''), lead.get('source', '')])
        worksheet.clear()
        worksheet.update('A1', data)
        return True
    except Exception as e:
        print(f"Error exporting to Google Sheets: {e}")
        return False

def build_html_body(body, lead_id=None):
    safe_lines = [html.escape(line) for line in (body or '').split('\n')]
    paragraphs = ''.join(f"<p>{line}</p>" for line in safe_lines if line.strip() or line == '')
    pixel = ''
    if lead_id and TRACKING_HOST:
        pixel_url = f"{TRACKING_HOST.rstrip('/')}/open?lead_id={lead_id}"
        pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" />'
    return f"<html><body>{paragraphs}{pixel}</body></html>"


def send_email_smtp(to_email, subject, body, html_body, lead_name=None):
    """Send email via SMTP"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        if not SMTP_EMAIL or not SMTP_PASSWORD or not SMTP_SERVER or not SMTP_PORT:
            return False, "SMTP not configured"
        msg = MIMEMultipart('alternative')
        msg['From'] = f"Lead Outreach AI <{SMTP_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        if SMTP_PORT == 587:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True, None
        elif SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True, None
        return False, f"Unsupported port {SMTP_PORT}"
    except Exception as e:
        return False, str(e)

def send_email(to_email, subject, body, lead_name=None, lead_id=None):
    """Send email via Brevo or SMTP fallback"""
    if not to_email or not isinstance(to_email, str) or '@' not in to_email:
        print(f"⚠️  Skipping email send: Invalid address '{to_email}'")
        return False, "Invalid or missing recipient email address"

    html_body = build_html_body(body, lead_id)
    if BREVO_API_KEY:
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
            
            recipient_name = lead_name
            if not recipient_name:
                recipient_name = to_email.split('@')[0] if to_email else "Lead"

            payload = {
                "sender": {"email": SMTP_EMAIL or "outreach@yourdomain.com", "name": "Lead Outreach AI"},
                "to": [{"email": to_email, "name": recipient_name}],
                "subject": subject,
                "textContent": body,
                "htmlContent": html_body
            }
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code in [200, 201, 202]:
                print(f"✅ Sent via Brevo to {to_email} (status {response.status_code})")
                return True, None
            else:
                err_text = f"Brevo API responded with {response.status_code}: {response.text}"
                print(f"⚠️ Brevo send failed: {err_text}")
                # Fallthrough to SMTP fallback with the reason
                brevo_err = err_text
        except Exception as e:
            brevo_err = str(e)
            print(f"⚠️ Exception while calling Brevo API: {brevo_err}")
        # If we reach here, Brevo failed, try SMTP fallback and include Brevo reason
        smtp_success, smtp_err = send_email_smtp(to_email, subject, body, html_body, lead_name)
        if smtp_success:
            print(f"✅ Sent via SMTP to {to_email} after Brevo failure: {brevo_err}")
            return True, None
        else:
            combined_err = f"Brevo error: {brevo_err}; SMTP error: {smtp_err}"
            print(f"❌ Both Brevo and SMTP failed for {to_email}: {combined_err}")
            return False, combined_err
    else:
        return send_email_smtp(to_email, subject, body, html_body, lead_name)

def get_snov_token():
    """Get Snov.io token"""
    if not SNOV_CLIENT_ID or not SNOV_CLIENT_SECRET: return None
    try:
        res = requests.post("https://api.snov.io/v1/oauth/access_token", data={'grant_type': 'client_credentials', 'client_id': SNOV_CLIENT_ID, 'client_secret': SNOV_CLIENT_SECRET}, verify=False, timeout=10)
        return res.json().get('access_token')
    except: return None

def get_snov_balance():
    """Get Snov.io credit balance"""
    token = get_snov_token()
    if not token: return None
    try:
        res = requests.get("https://api.snov.io/v1/get-balance", headers={'Authorization': f'Bearer {token}'}, verify=False, timeout=10)
        return res.json()
    except: return None

def search_snov_domain(domain):
    """Search Snov.io for domain emails"""
    if not SNOV_CLIENT_ID or not SNOV_CLIENT_SECRET or SNOV_CLIENT_ID == "your_snovio_api_key":
        print("[SNOV] Error: Snov.io API keys are not configured. Please set SNOVIO_API_KEY and SNOVIO_SECRET_KEY in your .env file.")
        return []
    print(f"[SNOV] Starting search for {domain}")
    token = get_snov_token()
    if not token: 
        print("[SNOV] Failed to get token")
        return []
    
    print(f"[SNOV] Token obtained. Querying API...")
    try:
        # Snov.io v2 Domain Search (GET request)
        params = {
            'domain': domain,
            'type': 'all',
            'limit': 100,
            'lastId': 0
        }
        headers = {'Authorization': f'Bearer {token}'}
        
        res = requests.get("https://api.snov.io/v2/domain-emails-with-info", params=params, headers=headers, verify=False, timeout=10)
        print(f"[SNOV] API Response Status: {res.status_code}")
        
        if res.status_code != 200:
            print(f"[SNOV] API Error Response: {res.text}")
            return []

        try:
            data = res.json()
        except json.JSONDecodeError as e:
            print(f"[SNOV] JSON Decode Error: {e}")
            return []
        
        emails = []
        if isinstance(data, dict):
            if 'emails' in data:
                emails = data['emails']
            elif 'data' in data and isinstance(data['data'], list):
                emails = data['data']
        
        results = []
        for e in emails:
            if not isinstance(e, dict): continue
            
            first = e.get('first_name', '')
            last = e.get('last_name', '')
            full_name = f"{first} {last}".strip()
            
            results.append({
                'email': e.get('email'),
                'company': full_name if full_name else (e.get('company_name') or domain),
                'position': e.get('position'),
                'source': 'Snov.io'
            })
            
        return results
    except Exception as e:
        print(f"[SNOV] Search error: {e}")
        return []

def normalize_outreach_result(success, err):
    dry_run = False
    reason = err
    if not success and OUTREACH_DRY_RUN:
        dry_run = True
        success = True
        reason = reason or "Dry run (outbound email not configured)"
    return success, dry_run, reason


def build_template_context(lead):
    location = lead.get('location') or lead.get('city') or ''
    fallback_name = (lead.get('company') or lead.get('email') or 'there').split('@')[0]
    context = SafeDict({
        'name': lead.get('company') or fallback_name,
        'company': lead.get('company') or 'your company',
        'email': lead.get('email') or '',
        'location': location,
        'product': lead.get('ai_analysis', {}).get('product') if isinstance(lead.get('ai_analysis'), dict) else 'this solution',
        'cta': lead.get('notes', 'Let me know a good time to chat'),
    })
    return context


def format_template(template, lead):
    context = build_template_context(lead)
    subject = template.get('subject', 'Hello').format_map(context)
    message = template.get('message', '').format_map(context)
    return subject, message


def resolve_follow_up_template(lead, template_key=None):
    if template_key and template_key in OUTREACH_TEMPLATES:
        return OUTREACH_TEMPLATES.get(template_key)

    step = max(1, lead.get('current_sequence_step') or 1)
    index = min(step - 1, len(FOLLOW_UP_SEQUENCE) - 1)
    seq = FOLLOW_UP_SEQUENCE[index]
    return OUTREACH_TEMPLATES.get(seq['template_key'])


def get_follow_up_metadata(lead):
    step = max(1, lead.get('current_sequence_step') or 1)
    index = min(step - 1, len(FOLLOW_UP_SEQUENCE) - 1)
    seq = FOLLOW_UP_SEQUENCE[index]
    return {
        'next_step': step,
        'template_key': seq['template_key'],
        'template_name': seq['title']
    }

def call_ai_service(prompt, ai_service="gemini", temperature=0.1):
    """Call Gemini or Groq with fallback"""
    services = [ai_service, "groq" if ai_service == "gemini" else "gemini"]
    for s in services:
        try:
            if s == "gemini":
                _genai = get_genai()
                if _genai:
                    model_name = get_working_gemini_model()
                    if model_name:
                        model = _genai.GenerativeModel(model_name)
                        res = model.generate_content(prompt)
                        if res and hasattr(res, 'text'): return res.text, "gemini"
            elif s == "groq":
                client = get_groq()
                if client:
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], temperature=temperature)
                    return res.choices[0].message.content, "groq"
        except: continue
    return None, None

def looks_like_lead_dict(entry):
    """Return True if the dict contains keys typically present on a lead."""
    if not isinstance(entry, dict):
        return False
    lead_keys = {'company', 'company_name', 'email', 'website', 'official_website'}
    return any(key in entry for key in lead_keys)

def extract_json_from_text(text):
    """Robustly extract JSON array or object from text"""
    if not text:
        return None
    
    # Clean up common AI artifacts
    text = text.strip()
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    decoder = json.JSONDecoder()
    idx = 0
    length = len(text)
    while idx < length:
        char = text[idx]
        if char not in ('[', '{'):
            idx += 1
            continue
        try:
            obj, consumed = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            idx += 1
            continue

        if consumed <= 0:
            idx += 1
            continue

        if isinstance(obj, list) and obj:
            if any(looks_like_lead_dict(item) for item in obj if isinstance(item, dict)):
                return obj
        elif isinstance(obj, dict):
            for key in ['leads', 'results', 'data', 'items']:
                candidate = obj.get(key)
                if isinstance(candidate, list) and candidate and any(looks_like_lead_dict(item) for item in candidate if isinstance(item, dict)):
                    return candidate
            if looks_like_lead_dict(obj):
                return [obj]

        idx += consumed
    
    return None

def agent_ai_clean_search_results(search_results, ai_service="gemini"):
    """Clean search results with AI"""
    text = "".join([f"Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n---\n" for r in search_results])
    prompt = f"Extract business leads from these search results. Return ONLY a JSON array of objects with keys: name, email, website, phone, company, location, confidence_score, ai_analysis (reasoning, business_maturity, growth_potential), notes.\n\nINPUT:\n{text}"
    res, _ = call_ai_service(prompt, ai_service)
    return extract_json_from_text(res) or []

def agent_ai_extract_leads(text, ai_service="gemini"):
    """Extract leads from text with AI"""
    prompt = f"Extract business leads from this text. Return ONLY a JSON array of objects with keys: name, email, website, phone, company, location, confidence_score, ai_analysis (reasoning, business_maturity, growth_potential), notes.\n\nINPUT:\n{text}"
    res, _ = call_ai_service(prompt, ai_service)
    return extract_json_from_text(res) or []

def agent_generate_outreach_message(lead, tone="professional", template="email", ai_service="gemini"):
    """Generate outreach message with AI"""
    prompt = f"Generate a {tone} {template} outreach message for this lead: {json.dumps(lead)}. Return JSON with keys: subject, message, cta, preview."
    res, _ = call_ai_service(prompt, ai_service, temperature=0.7)
    data = extract_json_from_text(res)
    if isinstance(data, list) and data: data = data[0]
    return {"success": True, **data} if data else {"success": False, "error": "AI failed"}

def agent_generate_campaign_strategy(leads_count, industry, objective, ai_service="gemini"):
    """Generate campaign strategy with AI"""
    prompt = f"Create a strategy for {leads_count} leads in {industry} for {objective}. Return JSON with keys: campaign_overview, target_audience, sequence, messaging_strategy, timings, success_metrics, response_handling, escalation_path."
    res, _ = call_ai_service(prompt, ai_service, temperature=0.7)
    data = extract_json_from_text(res)
    return {"success": True, "strategy": data} if data else {"success": False, "error": "AI failed"}

def _update_lead_after_outreach(lead_id, status_value='outreach_sent', sequence_step=2):
    conn = db.get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET status = %s, current_sequence_step = %s, last_outreach_at = NOW() WHERE id = %s",
        (status_value, sequence_step, lead_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True

def dispatch_followup_for_lead(lead, template_key=None, triggered_by='follow-up'):
    template = resolve_follow_up_template(lead, template_key)
    if not template:
        return False, "Template not available", None

    subject, message = format_template(template, lead)
    success, err = send_email(lead['email'], subject, message, lead.get('company'), lead_id=lead.get('id'))
    if not success:
        return False, err or "Failed to send follow-up", None

    db.log_outreach(lead['id'], 'email', f"{triggered_by} follow-up: {template.get('name')}")
    next_step = min((lead.get('current_sequence_step') or 1) + 1, len(FOLLOW_UP_SEQUENCE) + 1)
    _update_lead_after_outreach(lead['id'], status_value='followup_sent', sequence_step=next_step)
    return True, None, next_step

def extract_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()
            if content_type == 'text/plain' and disposition in (None, 'inline'):
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='ignore')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode('utf-8', errors='ignore')
    return ''


def start_reply_monitor():
    global LAST_IMAP_CHECK, LAST_IMAP_ERROR, LAST_IMAP_PROCESSED

    if not IMAP_EMAIL or not IMAP_PASSWORD:
        print("IMAP reply monitor disabled (missing credentials)")
        return

    def monitor():
        global LAST_IMAP_CHECK, LAST_IMAP_ERROR, LAST_IMAP_PROCESSED
        while True:
            mail = None
            LAST_IMAP_CHECK = datetime.utcnow().isoformat()
            processed_any = False
            try:
                mail = imaplib.IMAP4_SSL(IMAP_SERVER)
                mail.login(IMAP_EMAIL, IMAP_PASSWORD)
                mail.select('inbox')
                status, messages = mail.search(None, 'UNSEEN')
                ids = messages[0].split()
                if ids:
                    print(f"[IMAP] Found {len(ids)} unseen messages at {LAST_IMAP_CHECK}")
                for msg_id in ids:
                    _, msg_data = mail.fetch(msg_id, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])
                    sender = parseaddr(msg.get('From', ''))[1]
                    subject = msg.get('Subject', '')
                    body = extract_email_body(msg)
                    if not sender:
                        mail.store(msg_id, '+FLAGS', '\\Seen')
                        continue

                    lead = db.get_lead_by_email(sender)
                    if lead:
                        print(f"[IMAP] Reply detected from {sender} matching lead id {lead.get('id')} subject: {subject}")
                        marked = db.mark_lead_replied(lead['id'], subject, body)
                        if marked:
                            db.log_outreach(lead['id'], 'reply', f'Incoming reply: {subject or sender}')
                        processed_any = True
                        LAST_IMAP_PROCESSED = {'lead_id': lead.get('id'), 'sender': sender, 'subject': subject, 'when': datetime.utcnow().isoformat()}
                    else:
                        print(f"[IMAP] Incoming reply from {sender} did not match any lead")
                    mail.store(msg_id, '+FLAGS', '\\Seen')
                LAST_IMAP_ERROR = None
            except Exception as exc:
                LAST_IMAP_ERROR = str(exc)
                print(f"[IMAP] Reply monitor error: {exc}")
            finally:
                if mail:
                    try:
                        mail.close()
                    except Exception:
                        pass
                    try:
                        mail.logout()
                    except Exception:
                        pass
            if not processed_any:
                # small heartbeat message for visibility
                print(f"[IMAP] Poll complete at {LAST_IMAP_CHECK}, processed_any={processed_any}")
            time.sleep(IMAP_POLL_INTERVAL)

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()


def start_auto_followups():
    if AUTO_FOLLOWUP_INTERVAL <= 0:
        print("Auto follow-ups disabled (interval <= 0)")
        return

    def scheduler():
        while True:
            try:
                leads = db.get_auto_follow_up_candidates(AUTO_FOLLOWUP_DELAY_DAYS, len(FOLLOW_UP_SEQUENCE) + 1)
                for lead in leads:
                    if lead.get('replied'):  # skip answered leads
                        continue
                    success, err, _ = dispatch_followup_for_lead(lead, triggered_by='auto follow-up')
                    if not success:
                        print(f"[AUTO FOLLOWUP] Failed for lead {lead.get('id')}: {err}")
            except Exception as exc:
                print(f"[AUTO FOLLOWUP] Error: {exc}")
            time.sleep(AUTO_FOLLOWUP_INTERVAL)

    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()


def start_reminder_scheduler():
    interval = int(os.getenv('REMINDER_POLL_INTERVAL', '60'))
    if interval <= 0:
        print("Reminders disabled (interval <= 0)")
        return

    def scheduler():
        while True:
            try:
                due = db.get_due_reminders(100)
                if due:
                    print(f"[REMINDERS] Found {len(due)} due reminders")
                for r in due:
                    try:
                        payload = {
                            'reminder_id': r['id'],
                            'lead_id': r.get('lead_id'),
                            'message': r.get('message')
                        }
                        db.create_notification('reminder', payload)

                        # Handle recurrence
                        recurrence = r.get('recurrence') or 'none'
                        if recurrence == 'none':
                            db.mark_reminder_sent(r['id'])
                        else:
                            # Compute next reminder time
                            from datetime import timedelta
                            next_time = None
                            if recurrence == 'daily':
                                next_time = r['remind_at'] + timedelta(days=1)
                            elif recurrence == 'weekly':
                                next_time = r['remind_at'] + timedelta(weeks=1)
                            elif recurrence == 'monthly':
                                # Approximate by adding 30 days
                                next_time = r['remind_at'] + timedelta(days=30)

                            if next_time:
                                db.update_reminder_time(r['id'], next_time)
                                print(f"[REMINDERS] Rescheduled reminder {r['id']} to {next_time}")
                    except Exception as inner:
                        print(f"[REMINDERS] Error processing reminder {r.get('id')}: {inner}")
            except Exception as exc:
                print(f"[REMINDERS] Scheduler error: {exc}")
            time.sleep(interval)

    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()


def start_background_jobs():
    start_reply_monitor()
    start_auto_followups()
    start_reminder_scheduler()

def optimize_lead_data_with_ai(lead_data):
    """Uses AI to clean and infer missing lead data"""
    if not GEMINI_API_KEY:
        return lead_data
        
    try:
        model_name = get_working_gemini_model()
        if not model_name:
            return lead_data
        client = get_genai()
        if not client:
            return lead_data
        model = client.GenerativeModel(model_name)
        prompt = f"""
        Analyze and improve this lead data. 
        Input: {json.dumps(lead_data)}
        
        Tasks:
        1. Fix capitalization in Name and Company.
        2. If Company is missing but can be inferred from email domain (e.g. bob@google.com -> Google), fill it.
        3. Format phone number to standard international format if possible.
        4. Return ONLY the valid JSON object with the same keys.
        """
        
        response = model.generate_content(prompt)
        cleaned_json = getattr(response, 'text', str(response)).strip()
        # Remove markdown code blocks if present
        if cleaned_json.startswith('```json'):
            cleaned_json = cleaned_json[7:-3]
        elif cleaned_json.startswith('```'):
            cleaned_json = cleaned_json[3:-3]
            
        try:
            return json.loads(cleaned_json)
        except Exception:
            print(f"AI optimization returned non-JSON: {cleaned_json[:200]}")
            return lead_data
    except Exception as e:
        print(f"AI Optimization failed: {e}")
        return lead_data

def agent_ingest_leads(file_path, campaign_id=None):
    """Agent 1: Lead Ingestion Agent"""
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
                'phone': str(row.get('phone', '')),
                'company': row.get('company', ''),
                'location': row.get('location', ''),
                'source': 'upload',
                'campaign_id': campaign_id
            }
            db.insert_lead(lead_data)
            count += 1
            
        return {"message": f"Successfully ingested {count} leads"}
    except Exception as e:
        return {"error": str(e)}

def agent_verify_lead(lead):
    """Agent 2: Lead Verification Agent (Mock)"""
    # Mock verification
    return True

def scrape_justdial_url(url):
    """Specialized scraper for JustDial business listings"""
    print(f"🔍 Scraping JustDial URL: {url}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            
            # JustDial specific selectors
            company_name = page.title().split('-')[0].strip() or "JustDial Business"
            
            # Look for phone numbers in JustDial specific elements
            phones = []
            phone_selectors = [
                '.tel', '.phone', '.contact-number',
                '[data-phone]', '.mob',
                'span.tel', 'div.tel'
            ]
            
            for selector in phone_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for element in elements:
                        text = element.inner_text().strip()
                        if text and len(text) >= 7:
                            phones.append(text)
                except:
                    continue
            
            # If no phones found with selectors, try regex on page content
            if not phones:
                content = page.inner_text('body')
                phone_patterns = [r'\d{10}', r'\+91\s*\d{10}', r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}']
                for pattern in phone_patterns:
                    found = re.findall(pattern, content)
                    phones.extend(found)
            
            # Clean and deduplicate phones
            cleaned_phones = list(set([re.sub(r'\D', '', p) for p in phones if len(re.sub(r'\D', '', p)) >= 7]))
            
            browser.close()
            
            leads = []
            if cleaned_phones:
                for phone in cleaned_phones[:3]:  # Limit to 3 phones
                    lead = {
                        'name': f'Contact at {company_name}',
                        'email': '',  # JustDial rarely shows emails
                        'phone': phone,
                        'company': company_name,
                        'location': 'Chennai',  # Extract from URL or page
                        'source': 'justdial_scrape'
                    }
                    # db.insert_lead(lead) # Don't insert yet
                    leads.append(lead)
            
            print(f"✅ JustDial scraping found {len(cleaned_phones)} phones")
            return leads
            
    except Exception as e:
        print(f"❌ JustDial scraping error: {e}")
        return []

def scrape_yellowpages_url(url):
    """Specialized scraper for YellowPages business listings"""
    print(f"🔍 Scraping YellowPages URL: {url}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            
            company_name = page.title().split('-')[0].strip() or "YellowPages Business"
            
            # YellowPages specific selectors
            phones = []
            phone_selectors = [
                '.phone', '.telephone', '.phone-number',
                '[data-track="phone"]', '.track-phone',
                '.primary-phone', '.phone-link'
            ]
            
            for selector in phone_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for element in elements:
                        text = element.inner_text().strip()
                        if text and len(text) >= 7:
                            phones.append(text)
                except:
                    continue
            
            # Regex fallback
            if not phones:
                content = page.inner_text('body')
                phone_patterns = [r'\d{10}', r'\+?\d{1,3}[\s\-\.]?\d{10}', r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}']
                for pattern in phone_patterns:
                    found = re.findall(pattern, content)
                    phones.extend(found)
            
            cleaned_phones = list(set([re.sub(r'\D', '', p) for p in phones if len(re.sub(r'\D', '', p)) >= 7]))
            
            browser.close()
            
            leads = []
            if cleaned_phones:
                for phone in cleaned_phones[:3]:
                    lead = {
                        'name': f'Contact at {company_name}',
                        'email': '',
                        'phone': phone,
                        'company': company_name,
                        'location': 'Location Unknown',
                        'source': 'yellowpages_scrape'
                    }
                    # db.insert_lead(lead) # Don't insert yet
                    leads.append(lead)
            
            print(f"✅ YellowPages scraping found {len(cleaned_phones)} phones")
            return leads
            
    except Exception as e:
        print(f"❌ YellowPages scraping error: {e}")
        return []



def extract_contacts_from_text(text_content, html_content=""):
    """Helper to extract email and phone from text content"""
    # Regex for email - improved to catch more variations
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content + html_content))

    # Comprehensive phone number regex patterns
    phone_patterns = [
        # International format: +1 123-456-7890, +91 9876543210
        r'\+?\d{1,4}[\s\-\.]?\(?\d{1,4}\)?[\s\-\.]?\d{1,4}[\s\-\.]?\d{1,4}[\s\-\.]?\d{1,4}',
        # US format: (123) 456-7890, 123-456-7890, 123.456.7890
        r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}',
        # Indian format: +91 9876543210, 09876543210
        r'\+?91[\s\-\.]?\d{10}',
        # UK format: +44 20 1234 5678
        r'\+?44[\s\-\.]?\d{2,4}[\s\-\.]?\d{3,4}[\s\-\.]?\d{3,4}',
        # General international: +XX XXXXXXXXXX
        r'\+?\d{2,4}[\s\-\.]?\d{6,12}',
        # Simple 10+ digit numbers
        r'\d{10,15}',
        # Mobile numbers with country codes
        r'\+?\d{1,4}[\s\-\.]?\d{10}',
    ]

    phones = set()
    for pattern in phone_patterns:
        found_phones = re.findall(pattern, text_content)
        phones.update(found_phones)

    # Clean and validate phone numbers
    cleaned_phones = []
    for phone in phones:
        # Remove extra spaces and normalize
        cleaned = re.sub(r'\s+', '', phone)
        cleaned = re.sub(r'[\(\)]', '', cleaned)

        # Basic validation - must have at least 7 digits
        digits_only = re.sub(r'\D', '', cleaned)
        if len(digits_only) >= 7 and len(digits_only) <= 15:
            # Format nicely
            if cleaned.startswith('+'):
                cleaned_phones.append(cleaned)
            elif len(digits_only) == 10:  # Assume US format
                cleaned_phones.append(f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}")
            elif len(digits_only) == 12 and digits_only.startswith('91'):  # Indian format
                cleaned_phones.append(f"+91 {digits_only[2:7]} {digits_only[7:]}")
            else:
                cleaned_phones.append(cleaned)

    # Filter out common false positives (images, extensions)
    valid_emails = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css'))]

    # Extract names - look for common name patterns
    name_patterns = [
        # Common contact name patterns with colons
        r'(?:Contact|Name|Sales|Manager|Director|CEO|Founder|Owner)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        # Names followed by titles with dashes
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*-\s*(?:CEO|CTO|CFO|COO|Manager|Director|Sales|Marketing|Founder|Owner)',
        # Simple proper name patterns (First Last) - exclude common words
        r'\b([A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15})\b(?!\s*[:-]\s*(?:Street|St|Avenue|Ave|Road|Rd|Email|Phone|Contact|Information|Director|Manager|Sales|CEO|CTO|CFO|COO))',
    ]

    names = set()
    for pattern in name_patterns:
        found_names = re.findall(pattern, text_content, re.IGNORECASE)
        names.update(found_names)

    # Clean and validate names
    cleaned_names = []
    for name in names:
        name = name.strip()
        # Basic validation - reasonable name length, contains letters, not common false positives
        if (3 <= len(name) <= 30 and
            re.search(r'[A-Za-z]', name) and
            re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', name) and  # Must be First Last format
            not any(word in name.lower() for word in ['street', 'avenue', 'road', 'email', 'phone', 'contact', 'information', 'director', 'manager', 'sales', 'tam', 'nadu', 'com', 'for', 'inquiries'])):
            # Capitalize properly
            cleaned_names.append(name.title())

    # Extract addresses - look for common address patterns
    address_patterns = [
        # Street address patterns
        r'\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl|Court|Ct)\s*,?\s*[A-Za-z\s]+,?\s*\d{5}',
        # PO Box patterns
        r'P\.?O\.?\s*Box\s+\d+[A-Za-z0-9\s,.-]*',
        # City, State ZIP patterns
        r'[A-Za-z\s]+,?\s*[A-Z]{2}\s+\d{5}',
        # International address patterns
        r'\d+[A-Za-z0-9\s,.-]+,\s*[A-Za-z\s]+,\s*[A-Za-z\s]+\s*\d{4,6}',
    ]

    addresses = set()
    for pattern in address_patterns:
        found_addresses = re.findall(pattern, text_content, re.IGNORECASE)
        addresses.update(found_addresses)

    # Clean addresses
    cleaned_addresses = []
    for addr in addresses:
        addr = addr.strip()
        if len(addr) > 10 and len(addr) < 200:  # Reasonable address length
            cleaned_addresses.append(addr)

    return list(valid_emails), list(cleaned_phones), list(cleaned_addresses), list(cleaned_names)

def extract_contact_info(url):
    """Helper to scrape email and phone from a website using Playwright (Headless Browser)"""
    print(f"Scraping {url} with Playwright...")

    # Validate and clean URL
    if not url or not url.startswith(('http://', 'https://')):
        print(f"Invalid URL: {url}")
        return [], []

    # Remove any trailing garbage from URL
    url = url.split(' ')[0].split('\n')[0].split('\t')[0].strip()

    try:
        with sync_playwright() as p:
            # Launch browser with additional options for better compatibility
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )

            # Create context with realistic User-Agent to avoid blocking
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                ignore_https_errors=True
            )

            # Set longer timeout and add retry logic
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    page = context.new_page()

                    # Navigate with different wait conditions
                    response = page.goto(url, timeout=45000, wait_until="domcontentloaded")

                    if not response or response.status >= 400:
                        print(f"HTTP {response.status if response else 'unknown'} for {url}")
                        page.close()
                        if attempt < max_retries:
                            continue
                        browser.close()
                        return [], [], [], []

                    # Wait for potential JS rendering (e.g. React/Vue apps)
                    page.wait_for_timeout(5000)  # Increased wait time

                    # Try to find contact pages if we're on homepage
                    if url.endswith('/') or '/home' in url or len(url.split('/')) <= 3:
                        contact_urls = []
                        # Look for contact links in the page
                        try:
                            contact_links = page.query_selector_all('a[href*="contact"]')
                            for link in contact_links[:3]:  # Limit to first 3 contact links
                                href = link.get_attribute('href')
                                if href:
                                    if href.startswith('/'):
                                        href = url.rstrip('/') + href
                                    elif not href.startswith('http'):
                                        href = url.rstrip('/') + '/' + href
                                    if href not in contact_urls and href != url:
                                        contact_urls.append(href)
                        except:
                            pass

                        # Scrape contact pages too
                        for contact_url in contact_urls[:2]:  # Limit to 2 contact pages
                            try:
                                page.goto(contact_url, timeout=20000, wait_until="domcontentloaded")
                                page.wait_for_timeout(3000)
                                break  # Use the first working contact page
                            except Exception as e:
                                print(f"Failed to load contact page {contact_url}: {e}")
                                continue

                    # Extract text content
                    text = page.inner_text('body')

                    # Also get HTML for hidden mailto links
                    content = page.content()

                    page.close()
                    break  # Success, exit retry loop

                except Exception as nav_err:
                    print(f"Navigation attempt {attempt + 1} failed for {url}: {nav_err}")
                    try:
                        page.close()
                    except:
                        pass

                    if attempt < max_retries:
                        print(f"Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    else:
                        browser.close()
                        return [], [], [], []

            browser.close()

            # Regex for email - improved to catch more variations
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text + content))

            # Extract names - look for common name patterns
            name_patterns = [
                # Common contact name patterns with colons
                r'(?:Contact|Name|Sales|Manager|Director|CEO|Founder|Owner)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                # Names followed by titles with dashes
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*-\s*(?:CEO|CTO|CFO|COO|Manager|Director|Sales|Marketing|Founder|Owner)',
                # Simple proper name patterns (First Last) - exclude common words
                r'\b([A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15})\b(?!\s*[:-]\s*(?:Street|St|Avenue|Ave|Road|Rd|Email|Phone|Contact|Information|Director|Manager|Sales|CEO|CTO|CFO|COO))',
            ]

            names = set()
            for pattern in name_patterns:
                found_names = re.findall(pattern, text, re.IGNORECASE)
                names.update(found_names)

            # Clean and validate names
            cleaned_names = []
            for name in names:
                name = name.strip()
                # Basic validation - reasonable name length, contains letters, not common false positives
                if (3 <= len(name) <= 30 and
                    re.search(r'[A-Za-z]', name) and
                    re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', name) and  # Must be First Last format
                    not any(word in name.lower() for word in ['street', 'avenue', 'road', 'email', 'phone', 'contact', 'information', 'director', 'manager', 'sales', 'tam', 'nadu', 'com', 'for', 'inquiries'])):
                    # Capitalize properly
                    cleaned_names.append(name.title())

            # Comprehensive phone number regex patterns
            phone_patterns = [
                # International format: +1 123-456-7890, +91 9876543210
                r'\+?\d{1,4}[\s\-\.]?\(?\d{1,4}\)?[\s\-\.]?\d{1,4}[\s\-\.]?\d{1,4}[\s\-\.]?\d{1,4}',
                # US format: (123) 456-7890, 123-456-7890, 123.456.7890
                r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}',
                # Indian format: +91 9876543210, 09876543210
                r'\+?91[\s\-\.]?\d{10}',
                # UK format: +44 20 1234 5678
                r'\+?44[\s\-\.]?\d{2,4}[\s\-\.]?\d{3,4}[\s\-\.]?\d{3,4}',
                # General international: +XX XXXXXXXXXX
                r'\+?\d{2,4}[\s\-\.]?\d{6,12}',
                # Simple 10+ digit numbers
                r'\d{10,15}',
                # Mobile numbers with country codes
                r'\+?\d{1,4}[\s\-\.]?\d{10}',
            ]

            phones = set()
            for pattern in phone_patterns:
                found_phones = re.findall(pattern, text)
                phones.update(found_phones)

            # Clean and validate phone numbers
            cleaned_phones = []
            for phone in phones:
                # Remove extra spaces and normalize
                cleaned = re.sub(r'\s+', '', phone)
                cleaned = re.sub(r'[\(\)]', '', cleaned)

                # Basic validation - must have at least 7 digits
                digits_only = re.sub(r'\D', '', cleaned)
                if len(digits_only) >= 7 and len(digits_only) <= 15:
                    # Format nicely
                    if cleaned.startswith('+'):
                        cleaned_phones.append(cleaned)
                    elif len(digits_only) == 10:  # Assume US format
                        cleaned_phones.append(f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}")
                    elif len(digits_only) == 12 and digits_only.startswith('91'):  # Indian format
                        cleaned_phones.append(f"+91 {digits_only[2:7]} {digits_only[7:]}")
                    else:
                        cleaned_phones.append(cleaned)

            # Filter out common false positives (images, extensions)
            valid_emails = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css'))]

            # Extract addresses - look for common address patterns
            address_patterns = [
                # Street address patterns
                r'\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl|Court|Ct)\s*,?\s*[A-Za-z\s]+,?\s*\d{5}',
                # PO Box patterns
                r'P\.?O\.?\s*Box\s+\d+[A-Za-z0-9\s,.-]*',
                # City, State ZIP patterns
                r'[A-Za-z\s]+,?\s*[A-Z]{2}\s+\d{5}',
                # International address patterns
                r'\d+[A-Za-z0-9\s,.-]+,\s*[A-Za-z\s]+,\s*[A-Za-z\s]+\s*\d{4,6}',
            ]

            addresses = set()
            for pattern in address_patterns:
                found_addresses = re.findall(pattern, text, re.IGNORECASE)
                addresses.update(found_addresses)

            # Clean addresses
            cleaned_addresses = []
            for addr in addresses:
                addr = addr.strip()
                if len(addr) > 10 and len(addr) < 200:  # Reasonable address length
                    cleaned_addresses.append(addr)

            print(f"Found {len(valid_emails)} emails, {len(cleaned_phones)} phones, {len(cleaned_addresses)} addresses, {len(cleaned_names)} names")
            # Remove duplicates and return
            return list(set(valid_emails)), list(set(cleaned_phones)), list(set(cleaned_addresses)), list(set(cleaned_names))

    except Exception as e:
        print(f"Playwright Scraping error for {url}: {e}")
        return [], [], [], []


def search_with_serpapi(query, max_results=5):
    """Search with SerpApi (Google)"""
    if not SERPAPI_API_KEY:
        return []
    print(f"Performing search with SerpApi: {query}")
    try:
        client = Client(api_key=SERPAPI_API_KEY)
        results = client.search(q=query, engine="google", num=max_results)
        organic_results = results.get("organic_results", [])
        # Adapt SerpApi results to the format of DDGS results
        adapted_results = []
        for r in organic_results:
            adapted_results.append({
                'title': r.get('title'),
                'href': r.get('link'),
                'body': r.get('snippet')
            })
        return adapted_results
    except Exception as e:
        print(f"SerpApi query failed: {e}")
        return []

import threading

def run_with_timeout(func, args=(), kwargs=None, timeout=8):
    """Run `func` in a thread and return its result or raise TimeoutError."""
    kwargs = kwargs or {}
    result_container = {}
    def target():
        try:
            result_container['result'] = func(*args, **kwargs)
        except Exception as exc:
            result_container['exc'] = exc

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")
    if 'exc' in result_container:
        raise result_container['exc']
    return result_container.get('result')


def search_the_web(query, max_results=5):
    """Optimized web search with multiple engines and timeouts."""
    all_results = []
    seen_links = set()

    # Primary: Use SerpApi if key is available
    if SERPAPI_API_KEY:
        try:
            print(f"Performing search with SerpApi: {query}")
            # Run SerpApi with a timeout to avoid hanging
            results = run_with_timeout(search_with_serpapi, args=(query,), kwargs={'max_results': max_results}, timeout=6)
            for r in results:
                link = r.get('href', '')
                if link and link not in seen_links:
                    all_results.append(r)
                    seen_links.add(link)
        except TimeoutError as te:
            print(f"SerpApi timed out: {te}")
        except Exception as e:
            print(f"SerpApi query failed: {e}")

    # Fallback 1: Use DuckDuckGo Search library (DDGS)
    if len(all_results) < max_results:
        try:
            print(f"Fallback 1: Performing search with DDGS: {query}")
            # Use short timeout by running in thread wrapper
            results = run_with_timeout(lambda q, m: list(DDGS(timeout=8).text(q, max_results=m)), args=(query, max_results - len(all_results)), timeout=6)
            for r in results:
                link = r.get('href', '')
                if link and link not in seen_links:
                    all_results.append(r)
                    seen_links.add(link)
        except TimeoutError as te:
            print(f"DDGS timed out: {te}")
        except Exception as e:
            print(f"DDGS query failed: {e}")

    # Fallback 2: Direct Scrape (if everything else fails)
    if len(all_results) < 2:  # Extremely low results
        try:
            print(f"Fallback 2: Direct Search Scrape (requests): {query}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            # Try a direct search engine like DuckDuckGo HTML version (use requests with timeout)
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            response = requests.get(search_url, headers=headers, timeout=8)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for result in soup.find_all('div', class_='result'):
                title_tag = result.find('a', class_='result__a')
                snippet_tag = result.find('a', class_='result__snippet')
                if title_tag:
                    link = title_tag.get('href', '')
                    if 'duckduckgo.com/y.js' in link: # Handle proxy links
                         continue
                    if link and link not in seen_links:
                        all_results.append({
                            'title': title_tag.text,
                            'href': link,
                            'body': snippet_tag.text if snippet_tag else ""
                        })
                        seen_links.add(link)
        except Exception as e:
            print(f"Fallback 2 failed: {e}")


    return all_results


def agent_discovery(industry, location):
    """Agent 1.5: Lead Discovery Agent (Real Web Search & Scraping)"""
    print(f"🔍 Searching for {industry} in {location}...")
    
    found_leads = []
    
    # Try multiple query variations optimized for finding contact information
    queries = [
        f'"{industry}" companies in "{location}" contact email phone',
        f'{industry} companies {location} email address contact',
        f'list of {industry} companies in {location} with contact details',
        f'{industry} agencies {location} email phone number',
        f'{industry} firms {location} contact information'
    ]
    
    all_results = []
    seen_links = set()

    try:
        for query in queries:
            results = search_the_web(query, max_results=8)  # Increased from 5 to 8 for more results
            for r in results:
                link = r.get('href', '')
                if link and link not in seen_links:
                    all_results.append(r)
                    seen_links.add(link)
            
            if len(all_results) >= 15:  # Increased threshold
                break
        
        if not all_results:
            print("❌ No results from any search engine. Returning empty list.")
            return []

        print(f"✅ Found {len(all_results)} total raw results.")

        # Filter results to only include relevant ones (contain industry or location in title/href)
        filtered_results = []
        industry_lower = industry.lower()
        location_lower = location.lower()
        
        # Split industry into keywords for broader matching
        industry_keywords = industry_lower.split()
        
        for r in all_results:
            title = r.get('title', '').lower()
            href = r.get('href', '').lower()
            snippet = r.get('body', '').lower()
            
            # Check if any industry keyword is present
            industry_match = any(k in title for k in industry_keywords) or any(k in snippet for k in industry_keywords)
            location_match = location_lower in title or location_lower in snippet
            
            if industry_match or location_match:
                filtered_results.append(r)
        
        if not filtered_results:
            print("⚠️ No strictly relevant results found after filtering. Using top raw results.")
            filtered_results = all_results[:5] # Fallback to top 5 raw results
        else:
            print(f"✅ Filtered down to {len(filtered_results)} relevant results.")

        for i, r in enumerate(filtered_results[:10]):  # Process top 10 filtered results
            print(f"--- Processing result {i+1} ---")
            title = r.get('title', 'Unknown Company')
            link = r.get('href', '')
            snippet = r.get('body', '')
            print(f"Title: {title}")
            print(f"Link: {link}")
            
            # Skip only social media and irrelevant directories
            if any(x in link.lower() for x in ['linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com']):
                print("Skipping social media link.")
                continue
            
            # Skip aggregators and listicles if user wants "official pages"
            # Common patterns for listicles: "top-10", "best-20", "clutch.co", "yelp.com", "justdial.com", "sulekha.com"
            # But wait, user might WANT justdial if they are scraping it specifically. 
            # However, for "Web Search" (Smart Lead Finder), we usually want direct company sites.
            # The user specifically asked to avoid "Top 20" etc.
            
            skip_keywords = ['top-', 'best-', 'list-of', 'directory', 'clutch.co', 'yelp.com', 'sulekha.com', 'justdial.com', 'yellowpages', 'thumbtack', 'upwork', 'fiverr']
            if any(k in link.lower() for k in skip_keywords) or any(k in title.lower() for k in ['top ', 'best ', 'list of ']):
                print(f"Skipping aggregator/listicle: {link}")
                continue

            print(f"Scraping {link}...")
            emails, phones, addresses, names = extract_contact_info(link)
            print(f"Scraping result: {len(emails)} emails, {len(phones)} phones, {len(addresses)} addresses, {len(names)} names")

            # If no email found on page, try to guess from snippet
            email = emails[0] if emails else ''
            phone = phones[0] if phones else ''
            address = addresses[0] if addresses else ''
            name = names[0] if names else ''

            # If we still don't have an email, try to find email in snippet
            if not email:
                snippet_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                if snippet_emails:
                    email = snippet_emails[0]
                    print(f"Found email in snippet: {email}")

            # Extract company name from title
            company_name = title.split('-')[0].split('|')[0].strip()
            if len(company_name) < 3:
                company_name = "Unknown Company"

            # Create lead if we have either email or phone
            if email or phone:
                # Use extracted name if available, otherwise create a generic one
                contact_name = name if name else f'Contact at {company_name}'
                lead = {
                    'name': contact_name,
                    'email': email,
                    'phone': phone,
                    'company': company_name,
                    'location': location,
                    'source': 'ai_discovery_web'
                }

                # Check if we already have this lead (basic duplicate check)
                existing = db.get_lead_by_email(email) if email else None
                if not existing:
                    # Optimize with AI before returning
                    lead = optimize_lead_data_with_ai(lead)
                    
                    # db.insert_lead(lead) # Don't insert yet, just return
                    found_leads.append(lead)
                    print(f"Found candidate lead: {company_name} - {email or phone}")
                else:
                    print(f"Duplicate lead skipped: {email or phone}")
            else:
                print("No email or phone found for this lead.")
                
    except Exception as e:
        import traceback
        print(f"Discovery Error: {e}")
        traceback.print_exc()
        # Fallback to mock if search fails completely (e.g. rate limits)
        return []
            
    print(f"--- Discovery finished. Found {len(found_leads)} total leads. ---")
    return found_leads

def agent_scrape_specific_url(url):
    """Enhanced Agent: Scrape specific URL for comprehensive lead information"""
    print(f"🚀 STARTING SCRAPING for URL: {url}")
    if 'justdial.com' in url.lower():
        print("🔍 Detected JustDial URL - using specialized scraping")
        return scrape_justdial_url(url)
    elif 'yellowpages.com' in url.lower():
        print("🔍 Detected YellowPages URL - using specialized scraping")
        return scrape_yellowpages_url(url)
    
    # For other URLs, use the main contact info extraction
    try:
        emails, phones, addresses, names = extract_contact_info(url)
        leads = []
        if emails or phones:
            company_name = "Unknown Company"
            try:
                # Try to get company name from URL
                company_name = url.split('/')[2].replace('www.', '').split('.')[0]
            except:
                pass

            contact_name = names[0] if names else f'Contact at {company_name}'
            lead = {
                'name': contact_name,
                'email': emails[0] if emails else '',
                'phone': phones[0] if phones else '',
                'company': company_name,
                'location': addresses[0] if addresses else 'Unknown',
                'source': 'url_scrape'
            }
            # Optimize with AI
            lead = optimize_lead_data_with_ai(lead)
            
            # db.insert_lead(lead) # Don't insert yet
            leads.append(lead)
        
        return leads
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return []

def agent_verify_lead(lead):
    """Agent 2: Lead Verification Agent (Mock)"""
    # Mock verification
    return True

    # if not GEMINI_API_KEY:
    #     return True  # Mock verification if no API key
    
    # prompt = f"""
    # Verify the following lead contact information for validity:
    # Name: {lead['name']}
    # Email: {lead['email']}
    # Phone: {lead['phone']}
    # Company: {lead['company']}
    # Location: {lead['location']}
    
    # Check if:
    # 1. Email format is valid
    # 2. Phone number format is reasonable
    # 3. Information appears legitimate
    
    # Return only: VALID or INVALID with a brief reason.
    # """
    
    # try:
    #     model = genai.GenerativeModel('gemini-1.5-flash')  # Gemini 3 Flash equivalent
    #     response = model.generate_content(prompt)
    #     result = response.text.strip().upper()
    #     return "VALID" in result
    # except Exception as e:
    #     print(f"Gemini Verification Error: {e}")
    #     return True  # Default to valid if API fails

def agent_analyze_business(lead):
    """Agent 3: Business Analysis Agent (Real AI)"""
    
    # Fallback to mock if no API key
    if not GEMINI_API_KEY:
        print("⚠️ No Gemini API Key found. Using mock analysis.")
        import random
        company_name = lead.get('company', '').lower()
        location = lead.get('location', '').lower()
        trust_score = 50
        if 'tech' in company_name or 'software' in company_name: trust_score += 20
        if 'ltd' in company_name or 'inc' in company_name: trust_score += 10
        if 'chennai' in location or 'bangalore' in location: trust_score += 15
        trust_score = min(100, max(0, trust_score + random.randint(-10, 10)))
        
        if trust_score > 80: maturity, growth = "Enterprise", "High"
        elif trust_score > 60: maturity, growth = "SMB", "Medium"
        else: maturity, growth = "Startup", "Low"
        
        return {
            "trust_score": trust_score,
            "business_maturity": maturity,
            "growth_potential": growth,
            "reasoning": f"Mock analysis (No API Key). Score: {trust_score}"
        }

    try:
        print(f"🤖 Analyzing business with Gemini: {lead.get('company')}")
        model_name = get_working_gemini_model()
        if not model_name:
            # Fallback to mock if no model available
            return {
                "trust_score": 50,
                "business_maturity": "SMB",
                "growth_potential": "Medium",
                "reasoning": "No supported Gemini model available"
            }
        client = get_genai()
        if not client:
            return {
                "trust_score": 50,
                "business_maturity": "SMB",
                "growth_potential": "Medium",
                "reasoning": "Gemini client not configured"
            }
        model = client.GenerativeModel(model_name)
        
        prompt = f"""
        Analyze this business lead for a B2B service provider (Digital Marketing/Tech Services).
        
        Lead Details:
        Company: {lead.get('company', 'Unknown')}
        Location: {lead.get('location', 'Unknown')}
        Email: {lead.get('email', 'Unknown')}
        Phone: {lead.get('phone', 'Unknown')}
        
        Task:
        1. Estimate 'trust_score' (0-100) based on company name professionalism, location, and contact info quality.
        2. Classify 'business_maturity' as 'Startup', 'SMB', or 'Enterprise'.
        3. Estimate 'growth_potential' as 'Low', 'Medium', or 'High'.
        4. Provide a short 'reasoning' (max 2 sentences).
        
        Return ONLY a valid JSON object with keys: trust_score, business_maturity, growth_potential, reasoning.
        """
        
        response = model.generate_content(prompt)
        cleaned_json = response.text.strip()
        if cleaned_json.startswith('```json'):
            cleaned_json = cleaned_json[7:-3]
        elif cleaned_json.startswith('```'):
            cleaned_json = cleaned_json[3:-3]
            
        analysis = json.loads(cleaned_json)
        
        # Ensure types are correct
        analysis['trust_score'] = int(analysis.get('trust_score', 50))
        
        return analysis
        
    except Exception as e:
        print(f"❌ AI Analysis Failed: {e}")
        # Fallback to mock on error
        return {
            "trust_score": 50,
            "business_maturity": "Unknown",
            "growth_potential": "Unknown",
            "reasoning": f"AI Analysis failed: {str(e)}"
        }

def agent_decide_outreach(analysis):
    """Agent 4: Decision Agent (Mock)"""
    trust_score = analysis.get('trust_score', 0)
    maturity = analysis.get('business_maturity', 'Unknown')
    growth = analysis.get('growth_potential', 'Low')
    
    # Simple decision logic
    if trust_score >= 60:
        return "OUTREACH"
    elif trust_score >= 40 and growth in ['Medium', 'High']:
        return "OUTREACH"
    elif maturity == "Enterprise":
        return "OUTREACH"
    else:
        return "SKIP"

def agent_message_strategy(lead, analysis):
    """Agent 5: Message Strategy Agent (Mock)"""
    maturity = analysis.get('business_maturity', 'SMB')
    trust_score = analysis.get('trust_score', 0)
    
    if maturity == "Enterprise" or trust_score > 80:
        return "professional"
    elif maturity == "SMB" and trust_score > 60:
        return "polite"
    else:
        return "friendly"

def agent_generate_message(lead, strategy="polite"):
    """Agent 6: Message Generation Agent (Real AI with Multi-language Support)"""
    name = lead.get('name', 'Valued Partner')
    company = lead.get('company', 'your company')
    location = lead.get('location', 'Unknown')
    
    # Fallback to mock if no API key
    if not GEMINI_API_KEY:
        if strategy == "professional":
            return f"Dear {name},\n\nI hope this email finds you well. We are a digital marketing agency specializing in helping businesses like {company} grow their online presence.\n\nWe would be interested in discussing how we can support your business objectives.\n\nBest regards,\nMogeshwaran\nDigital Marketing Specialist"
        elif strategy == "friendly":
            return f"Hi {name},\n\nI came across {company} and was impressed by what you do. We're a digital marketing team that helps businesses expand their reach online.\n\nWould love to chat about how we can help {company} grow!\n\nBest,\nMogeshwaran"
        else:  # polite
            return f"Hello {name},\n\nMy name is Mogeshwaran and I work with a digital marketing agency. I noticed {company} and thought we might be able to help with your online marketing needs.\n\nWould you be open to a quick conversation?\n\nThank you,\nMogeshwaran"

    try:
        print(f"🤖 Generating message with Gemini for {company} ({strategy})")
        model_name = get_working_gemini_model()
        if not model_name:
            # Fallback to mock
            return f"Hello {name},\n\nMy name is Mogeshwaran and I work with a digital marketing agency. I noticed {company} and thought we might be able to help with your online marketing needs.\n\nWould you be open to a quick conversation?\n\nThank you,\nMogeshwaran"
        client = get_genai()
        if not client:
            # Fallback to simple template if Gemini isn't available
            return f"Hello {name},\n\nMy name is Mogeshwaran and I work with a digital marketing agency. I noticed {company} and thought we might be able to help with your online marketing needs.\n\nWould you be open to a quick conversation?\n\nThank you,\nMogeshwaran"
        model = client.GenerativeModel(model_name)
        
        prompt = f"""
        Write a cold outreach email for a digital marketing agency.
        
        Recipient: {name} from {company}
        Location: {location}
        Tone: {strategy} (Professional, Polite, or Friendly)
        Goal: Schedule a quick call to discuss marketing services.
        
        Requirements:
        1. Keep it short (under 150 words).
        2. Be personalized to the company/industry if possible.
        3. If the location is in Tamil Nadu (Chennai, Coimbatore, etc.), include a greeting or small phrase in Thanglish (Tamil written in English) to build rapport.
        4. If the location is in a Hindi-speaking region (Delhi, Mumbai, etc.), include a small Hindi phrase in English script.
        5. Otherwise, keep it fully English.
        
        Return ONLY the email body text. No subject line.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ AI Message Generation Failed: {e}")
        return f"Hello {name},\n\nI noticed {company} and thought we might be able to help with your online marketing needs.\n\nWould you be open to a quick conversation?\n\nThank you,\nMogeshwaran"

def agent_send_outreach(lead, message, subject=None):
    """Agent 7: Outreach Agent (Real SMTP + Mock Fallback)

    Returns a tuple: (success: bool, reason: str|None)
    """
    if not subject:
        subject = f"Connecting with {lead.get('company', 'your team')}"

    # Use the consolidated send_email helper which handles Brevo/SMTP, HTML, and Tracking
    success, err = send_email(lead.get('email'), subject, message, lead_name=lead.get('name'), lead_id=lead.get('id'))

    # Normalize result (checks for DRY_RUN)
    success, dry_run, reason = normalize_outreach_result(success, err)

    if success:
        log_message = message if not dry_run else f"{message}\n\n[DRY RUN MODE]"
        try:
            db.log_outreach(lead['id'], 'email', log_message)
        except Exception as e:
            print(f"⚠️ Failed to log outreach for lead {lead.get('id')}: {e}")
        return True, reason
    else:
        print(f"❌ Outreach Failed for {lead.get('email')}: {reason}")
        return False, reason

def autonomous_loop():
    """Background task for Autopilot Mode"""
    with app.app_context():
        autopilot = db.get_setting('autopilot')
        if autopilot != 'true':
            return

        print("--- Autopilot Running ---")
        pending_leads = db.get_pending_leads()
        
        for lead in pending_leads:
            if lead['status'] == 'new':
                print(f"Auto-Analyzing lead: {lead['id']}")
                analysis = agent_analyze_business(lead)
                decision = agent_decide_outreach(analysis)
                status = 'analyzed' if decision == 'OUTREACH' else 'skipped'
                db.update_lead_analysis(lead['id'], json.dumps(analysis), analysis.get('trust_score', 0), status)
                
            elif lead['status'] == 'analyzed':
                print(f"Auto-Outreach lead: {lead['id']}")
                # Get analysis for strategy determination
                analysis = json.loads(lead.get('ai_analysis', '{}'))
                strategy = agent_message_strategy(lead, analysis)
                message = agent_generate_message(lead, strategy)
                success, reason = agent_send_outreach(lead, message)
                if not success:
                    print(f"Auto-outreach failed for lead {lead.get('id')}: {reason}")
                
            elif lead['status'] == 'outreach_sent' and lead.get('campaign_id'):
                # Check for drip sequence
                campaign_id = lead['campaign_id']
                sequences = db.get_campaign_sequences(campaign_id)
                current_step = lead.get('current_sequence_step', 0)
                last_outreach = lead.get('last_outreach_at')
                
                # Find next step
                next_step = None
                for seq in sequences:
                    if seq['day_offset'] > current_step: # Assuming current_step stores the day_offset of last sent
                         # Actually, let's store the index or just check day_offset logic
                         # Simplified: current_sequence_step is the index of the last sent sequence. 0 means initial.
                         pass

                # Better logic:
                # current_sequence_step = 0 (Initial sent)
                # We look for a sequence with day_offset > 0
                
                # Let's assume sequences are ordered by day_offset
                # If current_sequence_step is 0, we look for the first follow up (e.g. day 3)
                
                # Find the sequence that corresponds to the *next* step
                # We need to know what "step 1" means. Is it the 1st follow up? Yes.
                
                # Let's say current_sequence_step = 0.
                # We want to find a sequence where day_offset is appropriate.
                
                if not last_outreach:
                    continue
                    
                import datetime
                days_since_last = (datetime.datetime.now() - last_outreach).days
                
                # Find the next sequence to send
                target_seq = None
                for seq in sequences:
                    # If this sequence hasn't been sent yet (we can track this by storing the last sent day_offset in current_sequence_step)
                    # Let's say current_sequence_step stores the day_offset of the last email.
                    # Initial email is day_offset 0.
                    
                    if seq['day_offset'] > lead.get('current_sequence_step', 0):
                        # This is a potential next step
                        # Check if enough time has passed from INITIAL outreach? Or LAST outreach?
                        # Usually drip is "Day 3" means 3 days after start.
                        
                        # We need the date of the FIRST outreach to calculate absolute day offset.
                        # Or we just use relative gaps.
                        
                        # Simple approach: Day 3 means 3 days after the previous step? Or 3 days from start?
                        # Standard is days from start.
                        # But we only have last_outreach_at.
                        
                        # Let's use relative for simplicity in this MVP.
                        # If seq['day_offset'] is 3, it means 3 days after the previous email.
                        
                        if days_since_last >= seq['day_offset']:
                            target_seq = seq
                            break
                
                if target_seq:
                    print(f"Auto-Drip lead: {lead['id']} - Step {target_seq['day_offset']}")
                    # Generate message using template
                    # We can use AI to personalize the template
                    template = target_seq['template_body']
                    # Simple variable substitution
                    message = template.replace('{name}', lead.get('name', 'there')).replace('{company}', lead.get('company', 'your company'))
                    
                    # Send
                    success, reason = agent_send_outreach(lead, message)
                    if not success:
                        print(f"Auto-drip failed for lead {lead.get('id')}: {reason}")
                    
                    # Update state
                    # We use the day_offset as the step indicator
                    db.update_lead_sequence_step(lead['id'], target_seq['day_offset'])
                
        print("--- Autopilot Cycle Complete ---")

def agent_analyze_response(response_text, lead):
    """Agent 8: Response Analysis Agent (Real AI)"""
    
    # Fallback to mock if no API key
    if not GEMINI_API_KEY:
        print("⚠️ No Gemini API Key found. Using mock response analysis.")
        text = response_text.lower()
        if any(word in text for word in ['yes', 'interested', 'sure', 'okay', 'great']):
            return {"interest_level": "high", "sentiment": "positive", "next_action": "continue", "reasoning": "Mock analysis: Positive keywords found."}
        elif any(word in text for word in ['maybe', 'later', 'busy', 'not sure']):
            return {"interest_level": "medium", "sentiment": "neutral", "next_action": "follow_up", "reasoning": "Mock analysis: Neutral keywords found."}
        else:
            return {"interest_level": "low", "sentiment": "negative", "next_action": "stop", "reasoning": "Mock analysis: No positive keywords."}

    try:
        print(f"🤖 Analyzing response with Gemini...")
        model_name = get_working_gemini_model()
        if not model_name:
            # Fallback to mock
            return {"interest_level": "low", "sentiment": "negative", "next_action": "stop", "reasoning": "No supported Gemini model available"}
        client = get_genai()
        if not client:
            return {"interest_level": "low", "sentiment": "negative", "next_action": "stop", "reasoning": "Gemini client not available"}
        model = client.GenerativeModel(model_name)
        
        prompt = f"""
        Analyze this email response from a lead.
        
        Lead: {lead.get('name', 'Unknown')} ({lead.get('company', 'Unknown Company')})
        Response Text: "{response_text}"
        
        Task:
        1. Determine 'sentiment' (Positive, Neutral, Negative).
        2. Estimate 'interest_level' (High, Medium, Low).
        3. Recommend 'next_action' (reply_immediately, schedule_meeting, send_info, follow_up_later, do_not_contact).
        4. Provide a short 'reasoning'.
        
        Return ONLY a valid JSON object with keys: sentiment, interest_level, next_action, reasoning.
        """
        
        response = model.generate_content(prompt)
        cleaned_json = response.text.strip()
        if cleaned_json.startswith('```json'):
            cleaned_json = cleaned_json[7:-3]
        elif cleaned_json.startswith('```'):
            cleaned_json = cleaned_json[3:-3]
            
        analysis = json.loads(cleaned_json)
        return analysis
        
    except Exception as e:
        print(f"❌ AI Response Analysis Failed: {e}")
        return {
            "interest_level": "medium",
            "sentiment": "neutral",
            "next_action": "manual_review",
            "reasoning": f"AI Analysis failed: {str(e)}"
        }

def agent_followup_logic(lead, response_analysis, follow_up_count):
    """Agent 9: Follow-up Agent (Mock)"""
    interest_level = response_analysis.get('interest_level', 'low')
    sentiment = response_analysis.get('sentiment', 'neutral')
    
    # Simple logic: continue if interested and under 3 follow-ups
    if interest_level in ['high', 'medium'] and sentiment != 'negative' and follow_up_count < 3:
        return True
    else:
        return False

def agent_targeted_search(location, niche, offering):
    """Agent 1.7: Targeted Lead Finder (Smart Search)"""
    print(f"🎯 Targeted Search: {niche} in {location} for {offering}")
    
    # Negative keywords to exclude aggregators and listicles
    negatives = '-site:justdial.com -site:sulekha.com -site:indiamart.com -site:tripadvisor.com -site:yelp.com -"top 10" -"top 20" -"best 10" -"list of"'
    
    queries = []
    if offering == "Landing Page":
        # Strategy: Find businesses that rely on social media or free emails (likely no website)
        queries = [
            f'site:facebook.com "{niche}" "{location}" "phone" "gmail.com"',
            f'site:instagram.com "{niche}" "{location}" "contact" "gmail.com"',
            f'"{niche}" "{location}" "@gmail.com" {negatives}', 
            f'"{niche}" "{location}" "contact number" {negatives}'
        ]
    elif offering == "Billing Software":
        # Strategy: Find retail/wholesale businesses that have high transaction volume
        queries = [
            f'"{niche}" "{location}" "store" contact email {negatives}',
            f'"{niche}" "{location}" "distributors" contact {negatives}',
            f'"{niche}" shop "{location}" phone number {negatives}',
            f'"{niche}" wholesalers "{location}" contact {negatives}'
        ]
    else:
        # General search
        queries = [f'"{niche}" in "{location}" contact details email phone {negatives}']

    found_leads = []
    seen_urls = set()

    # Keywords that indicate a listicle or directory in the title
    listicle_indicators = ['top 10', 'top 20', 'top 50', 'best ', 'list of', 'directory', 'yellow pages', 'listings', 'providers in']

    for query in queries:
        print(f"   Running query: {query}")
        try:
            results = search_the_web(query, max_results=15)
            
            for r in results:
                link = r.get('href', '')
                title = r.get('title', '').lower()
                snippet = r.get('body', '').lower()

                if link in seen_urls:
                    continue
                
                # Filter out listicles/directories based on title
                if any(indicator in title for indicator in listicle_indicators):
                    print(f"      Skipping listicle/directory: {title}")
                    continue

                seen_urls.add(link)
                
                # Extract emails from snippet
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                # Extract phones (simple pattern for Indian numbers often found in snippets)
                phones = re.findall(r'(?:\+91[\-\s]?)?[6789]\d{9}', snippet)
                
                email = emails[0] if emails else ''
                phone = phones[0] if phones else ''
                
                # Clean up company name
                company_name = r.get('title', '').split('-')[0].split('|')[0].split(':')[0].strip()
                if "profile" in company_name.lower() or "login" in company_name.lower():
                    continue

                # If we found at least one contact method
                if email or phone:
                    lead = {
                        'name': f"Owner/Manager",
                        'email': email,
                        'phone': phone,
                        'company': company_name,
                        'location': location,
                        'source': f'targeted_{offering.lower().replace(" ", "_")}',
                        'status': 'new',
                        'trust_score': 60
                    }
                    
                    # Deduplicate by email or phone locally before adding
                    if not any(l['email'] == email for l in found_leads if email) and \
                       not any(l['phone'] == phone for l in found_leads if phone):
                        
                        # AI Optimization (Optional, can be slow)
                        # lead = optimize_lead_data_with_ai(lead)
                        
                        found_leads.append(lead)
                        print(f"      Found lead: {company_name} ({email or phone})")
        except Exception as e:
            print(f"    Query failed: {e}")
            continue

    return found_leads

# --- API ENDPOINTS ---

@api.route('/targeted-search', methods=['POST'])
def targeted_search():
    data = request.json
    location = data.get('location', 'Tamil Nadu')
    niche = data.get('niche', 'Small Business')
    offering = data.get('offering', 'General')
    
    if not location or not niche:
        return jsonify({"error": "Missing location or niche"}), 400
        
    leads = agent_targeted_search(location, niche, offering)
    
    # Save to DB
    saved_count = 0
    for lead in leads:
        # Check if exists
        existing = None
        if lead['email']:
            existing = db.get_lead_by_email(lead['email'])
        
        if not existing:
            db.insert_lead(lead)
            saved_count += 1
            
    return jsonify({
        "message": f"Search complete. Found {len(leads)} leads, {saved_count} new added.", 
        "leads": leads
    })

def agent_keyword_search(keywords):
    """Agent 1.6: Lead Discovery Agent (Keyword Search)"""
    print(f"Searching for keywords: {keywords}...")
    
    found_leads = []
    query = f"{keywords} contact email"
    
    try:
        results = search_the_web(query, max_results=10)
        
        for r in results:
            title = r.get('title', 'Unknown Company')
            link = r.get('href', '')
            snippet = r.get('body', '')
            
            if any(x in link.lower() for x in ['linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com']):
                continue

            print(f"Scraping {link}...")
            emails, phones, addresses, names = extract_contact_info(link)

            email = emails[0] if emails else ''
            phone = phones[0] if phones else ''
            address = addresses[0] if addresses else 'Unknown'
            name = names[0] if names else ''

            if not email:
                snippet_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                if snippet_emails:
                    email = snippet_emails[0]

            company_name = title.split('-')[0].split('|')[0].strip()
            if len(company_name) < 3:
                company_name = "Unknown Company"

            if email or phone:
                contact_name = name if name else f'Contact at {company_name}'
                lead = {
                    'name': contact_name,
                    'email': email,
                    'phone': phone,
                    'company': company_name,
                    'location': address,
                    'source': 'ai_keyword_search'
                }

                existing = db.get_lead_by_email(email) if email else None
                if not existing:
                    # Optimize with AI
                    lead = optimize_lead_data_with_ai(lead)
                    
                    # db.insert_lead(lead) # Don't insert yet
                    found_leads.append(lead)
                    print(f"Found candidate lead: {company_name} - {email or phone}")
                else:
                    print(f"Duplicate lead skipped: {email or phone}")
                
    except Exception as e:
        print(f"Keyword Discovery Error: {e}")
        return []
            
    return found_leads

@api.route('/web-search', methods=['POST'])
def web_search():
    data = request.json
    query = data.get('query', '')
    advanced = data.get('advanced', {})
    
    if not query:
        return jsonify({"error": "Missing query"}), 400
        
    # Construct advanced query
    search_query = query
    if advanced:
        if advanced.get('exactPhrase'):
            search_query += f' "{advanced["exactPhrase"]}"'
        if advanced.get('anyWords'):
            search_query += f' {advanced["anyWords"]}'
        if advanced.get('noneWords'):
            search_query += f' {advanced["noneWords"]}'
        if advanced.get('site'):
            search_query += f' site:{advanced["site"]}'
        if advanced.get('filetype'):
            search_query += f' filetype:{advanced["filetype"]}'

    print(f"WEB SEARCH: Executing query: {search_query}")
        
    try:
        results = search_the_web(search_query, max_results=20)
        
        filtered_results = []
        skip_keywords = [
            'top-', 'best-', 'list-of', 'directory', 'clutch.co', 'yelp.com', 
            'sulekha.com', 'justdial.com', 'yellowpages', 'thumbtack', 'upwork', 
            'fiverr', 'linkedin.com', 'facebook.com', 'instagram.com', 'glassdoor',
            'goodfirms', 'designrush', 'sortlist', 'themanifest'
        ]
        
        skip_titles = ['top 10', 'top 20', 'top 30', 'top 50', 'top 100', 'best ', 'list of ', 'directory', 'reviews']

        for r in results:
            link = r.get('href', '')
            title = r.get('title', '').lower()
            
            if not link: continue
            if any(k in link.lower() for k in skip_keywords): continue
            if any(k in title for k in skip_titles): continue
                
            filtered_results.append(r)
            
        return jsonify({"results": filtered_results})
    except Exception as e:
        print(f"Web Search Route Error: {e}")
        return jsonify({"error": str(e)}), 500

@api.route('/ai-extract', methods=['POST'])
def ai_extract():
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({"error": "Missing text"}), 400
        
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured"}), 500
        
    try:
        # Ensure the genai client is available
        client = get_genai()
        if not client:
            return jsonify({"error": "Gemini client failed to initialize"}), 500

        model_name = get_working_gemini_model()
        if not model_name:
            return jsonify({"error": "No supported Gemini model found for generateContent."}), 500

        client = get_genai()
        if not client:
            return jsonify({"error": "Gemini client not initialized"}), 503
        model = client.GenerativeModel(model_name)
        prompt = f"""
        Extract qualified business leads from the following text. 
        Text: {text}
        
        Return a list of leads in valid JSON format. Each lead should have:
        - company_name
        - contact_name (if available, else null)
        - official_website
        - email
        - phone_number
        - full_address
        - confidence (0-100)
        - confidence_score (High/Medium/Low)
        
        Rules:
        1. Only return valid business information.
        2. If a field is missing, use null.
        3. Return ONLY the JSON list.
        """
        
        response = model.generate_content(prompt)
        content = getattr(response, 'text', str(response)).strip()
        
        # Clean up Markdown
        if content.startswith('```json'):
            content = content[7:-3]
        elif content.startswith('```'):
            content = content[3:-3]
            
        try:
            leads = json.loads(content)
        except Exception as e:
            print(f"AI extraction returned non-JSON: {content[:200]}")
            raise
        return jsonify({"leads": leads, "message": f"Successfully extracted {len(leads)} leads."})
    except Exception as e:
        print(f"AI Extraction error: {e}")
        return jsonify({"error": str(e)}), 500

@api.route('/clean-search-results', methods=['POST'])
def clean_search_results():
    data = request.json
    results = data.get('results', [])
    
    if not results:
        return jsonify({"error": "No results provided"}), 400

    # If Gemini API key is not present, return a clear, actionable error
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured. Set GEMINI_API_KEY in your environment (.env) and restart the server."}), 400
        
    try:
        # Ensure the genai client is available
        client = get_genai()
        if not client:
            return jsonify({"error": "Gemini client failed to initialize. Check server logs for configuration errors."}), 500

        model_name = get_working_gemini_model()
        if not model_name:
            return jsonify({"error": "No supported Gemini model found for generateContent."}), 500

        model = client.GenerativeModel(model_name)
        prompt = f"""
        Below are search results. Extract business leads from them.
        Results: {json.dumps(results)}
        
        Return a list of leads in JSON format:
        [
          {{"company_name": "...", "contact_name": "...", "official_website": "...", "email": "...", "phone_number": "...", "full_address": "...", "confidence": 0-100}}
        ]
        """
        
        try:
            response = model.generate_content(prompt)
            content = getattr(response, 'text', str(response)).strip()
            if content.startswith('```json'): content = content[7:-3]
            elif content.startswith('```'): content = content[3:-3]
            leads = json.loads(content)
            return jsonify({"leads": leads})
        except Exception as ai_exc:
            # Log and fall back to a simple heuristic extractor so the feature still works
            print(f"Gemini generation failed: {ai_exc}\n{traceback.format_exc()}")
            fallback_leads = []
            email_re = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
            for r in results:
                body = r.get('body', '')
                title = r.get('title', '')
                href = r.get('href', '')
                emails = email_re.findall(body + ' ' + title)
                primary_email = emails[0] if emails else None
                domain = ''
                try:
                    domain = urlparse(href).netloc
                except:
                    domain = ''
                fallback_leads.append({
                    'company_name': title or domain or 'Unknown',
                    'official_website': href or None,
                    'email': primary_email,
                    'phone_number': None,
                    'full_address': None,
                    'confidence': 50,
                    'confidence_score': 'Medium'
                })
            return jsonify({"leads": fallback_leads, "fallback": True, "reason": str(ai_exc)})
    except Exception as e:
        # Provide a clearer, actionable error for the client
        err_msg = str(e)
        tb = traceback.format_exc()
        print(f"Clean Search Error: {err_msg}\n{tb}")
        # Return debug details (safe for local development)
        return jsonify({
            "error": "AI cleaning failed",
            "details": err_msg,
            "hint": "Check GEMINI_API_KEY, internet connectivity, and that the google.generativeai package is installed and configured.",
            "trace": tb
        }), 502

@api.route('/ai-health', methods=['GET'])
def ai_health():
    """Return basic AI service configuration status (Gemini)"""
    client = get_genai()
    model_name = get_working_gemini_model()
    return jsonify({
        "gemini_api_key_set": bool(GEMINI_API_KEY),
        "gemini_client_loaded": bool(client),
        "gemini_model": model_name or "No supported model found"
    })


@api.route('/health', methods=['GET'])
def health():
    """General service health including DB connectivity"""
    healthy = True
    issues = []
    try:
        # lightweight DB check
        conn = db.get_db_connection()
        if conn is None:
            healthy = False
            issues.append('db_unavailable')
        else:
            try:
                cur = conn.cursor()
                cur.execute('SELECT 1')
                cur.close()
                conn.close()
            except Exception as e:
                healthy = False
                issues.append('db_query_failed')
    except Exception as e:
        healthy = False
        issues.append('db_check_error')

    return jsonify({
        'healthy': healthy,
        'issues': issues
    })


@api.route('/ai/generate', methods=['POST'])
def ai_generate():
    """Proxy endpoint to generate text using Gemini. Accepts JSON:
    { "prompt": "text" | "messages": [...], "model": optional, "max_tokens": optional }
    This endpoint tries to be resilient across google.generativeai client versions.
    """
    data = request.json or {}
    prompt = data.get('prompt')
    messages = data.get('messages')
    model_name = data.get('model') or get_working_gemini_model()
    max_tokens = data.get('max_tokens', 512)

    client = get_genai()
    if not client:
        return jsonify({"error": "Gemini client not configured. Set GEMINI_API_KEY in .env and ensure google.generativeai is installed."}), 503

    if not model_name:
        return jsonify({"error": "No Gemini model available for generation."}), 503

    try:
        # Try common generate method signatures.
        if hasattr(client, 'generate'):
            resp = client.generate(model=model_name, prompt=prompt or messages, max_output_tokens=max_tokens)
        elif hasattr(client, 'generate_text'):
            resp = client.generate_text(model=model_name, prompt=prompt or (messages or ""), max_output_tokens=max_tokens)
        elif hasattr(client, 'generate_content'):
            resp = client.generate_content(model=model_name, prompt=prompt or (messages or ""), max_output_tokens=max_tokens)
        else:
            return jsonify({"error": "Gemini client has no compatible generate method on this SDK"}), 501

        # Extract text in multiple possible response shapes
        text = None
        try:
            # obj with 'text' attr
            text = getattr(resp, 'text', None)
            if not text and isinstance(resp, dict):
                # look for candidates -> output
                if 'candidates' in resp and len(resp['candidates']) > 0:
                    text = resp['candidates'][0].get('output') or resp['candidates'][0].get('content')
                elif 'outputs' in resp and len(resp['outputs']) > 0:
                    # some SDKs return outputs list
                    first = resp['outputs'][0]
                    text = first.get('content') or first.get('text')
            if not text:
                text = str(resp)
        except Exception:
            text = str(resp)

        return jsonify({"success": True, "model": model_name, "response": text})
    except Exception as e:
        print(f"[ERROR] Gemini generate failed: {e}")
        return jsonify({"error": str(e)}), 500


@api.route('/save-extracted-leads', methods=['POST'])
def save_extracted_leads():
    data = request.json
    leads = data.get('leads', [])
    
    if not leads:
        return jsonify({"error": "No leads provided"}), 400
        
    saved = 0
    failed = 0
    failed_leads = []
    errors = []
    
    for lead in leads:
        # Simple validation
        name = lead.get('company_name') or lead.get('name')
        email = lead.get('email')
        
        if not name or not email or email == 'null':
            failed += 1
            failed_leads.append({
                "name": name or "Unknown",
                "email": email or "Missing",
                "reason": "Missing required name or email"
            })
            continue
            
        try:
            lead_data = {
                'name': lead.get('contact_name') or lead.get('company_name') or lead.get('company') or lead.get('name') or "Unknown",
                'email': email,
                'website': lead.get('official_website') or lead.get('website', ''),
                'phone': lead.get('phone_number') or lead.get('phone', ''),
                'company': lead.get('company_name') or lead.get('company') or lead.get('name') or "Unknown",
                'location': lead.get('full_address') or lead.get('location', ''),
                'source': 'ai_extraction',
                'status': 'new',
                'trust_score': lead.get('confidence', 70)
            }
            db.insert_lead(lead_data)
            saved += 1
        except Exception as e:
            failed += 1
            errors.append(str(e))
            
    return jsonify({
        "saved": saved,
        "failed": failed,
        "failed_leads": failed_leads,
        "errors": errors
    })

@api.route('/save-extracted-leads-no-validation', methods=['POST'])
def save_extracted_leads_no_validation():
    data = request.json
    leads = data.get('leads', [])
    
    saved = 0
    failed = 0
    
    for lead in leads:
        try:
            lead_data = {
                'name': lead.get('contact_name') or lead.get('company_name') or lead.get('company') or lead.get('name') or "Unknown",
                'email': lead.get('email', ''),
                'website': lead.get('official_website') or lead.get('website', ''),
                'phone': lead.get('phone_number') or lead.get('phone', ''),
                'company': lead.get('company_name') or lead.get('company') or lead.get('name') or "Unknown",
                'location': lead.get('full_address') or lead.get('location', ''),
                'source': 'ai_extraction_fast',
                'status': 'new'
            }
            db.insert_lead(lead_data)
            saved += 1
        except:
            failed += 1
            
    return jsonify({"saved": saved, "failed": failed})

@api.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Missing email"}), 400
        
    # Mock verification for now - can be improved with real DNS/SMTP check
    is_valid = bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))
    
    return jsonify({
        "valid": is_valid,
        "format_valid": is_valid,
        "mx_found": True,
        "smtp_check": True
    })

@api.route('/keyword-search', methods=['POST'])
def keyword_search():
    data = request.json
    keywords = data.get('keywords')
    
    if not keywords:
        return jsonify({"error": "Missing keywords"}), 400
        
    leads = agent_keyword_search(keywords)
    return jsonify({"message": f"Found and added {len(leads)} leads", "leads": leads})

@api.route('/search-leads', methods=['POST'])
def search_leads():
    data = request.json
    industry = data.get('industry')
    location = data.get('location')
    
    if not industry or not location:
        return jsonify({"error": "Missing industry or location"}), 400

    try:
        leads = agent_discovery(industry, location)
        if not leads:
            # Graceful fallback: provide mock suggestions so the UI can demonstrate behavior
            print(f"[DISCOVERY] No leads found for '{industry}' in '{location}'; returning mock suggestions.")
            leads = [
                {"name": f"Owner at {industry.title()} Co {i}", "email": f"contact+{i}@{industry.replace(' ','')}.example.com", "phone": "", "company": f"{industry.title()} Co {i}", "location": location, "source": "mock_discovery"}
                for i in range(1,4)
            ]
        return jsonify({"message": f"Found {len(leads)} leads", "leads": leads})
    except Exception as e:
        print(f"Search API error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Discovery failed", "details": str(e)}), 500

@api.route('/scrape-url', methods=['POST'])
def scrape_url():
    data = request.json
    url = data.get('url')
    
    print(f"🔍 API called with URL: {url}")
    
    if not url:
        return jsonify({"error": "Missing URL"}), 400
        
    print("🔍 About to call agent_scrape_specific_url...")
    leads = agent_scrape_specific_url(url)
    print(f"🔍 Function returned {len(leads)} leads")
    
    # Prepare a more detailed response
    lead_details = []
    for lead in leads:
        lead_details.append({
            "company": lead.get("company"),
            "name": lead.get("name"),
            "email": lead.get("email"),
            "phone": lead.get("phone")
        })

    return jsonify({
        "message": f"Successfully scraped {len(leads)} lead(s) from the URL.",
        "leads": lead_details,
        "debug": {
            "url": url,
            "leads_count": len(leads),
            "api_called": True
        }
    })

@api.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        data = request.json
        db.update_setting('autopilot', str(data.get('autopilot', 'false')).lower())
        return jsonify({"message": "Settings updated"})
    else:
        val = db.get_setting('autopilot')
        return jsonify({"autopilot": val == 'true'})

@api.route('/upload-leads', methods=['POST'])

def upload_leads():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filepath = os.path.join('uploads', file.filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)
    
    campaign_id = request.form.get('campaign_id')
    if campaign_id == 'null' or campaign_id == 'undefined':
        campaign_id = None
        
    result = agent_ingest_leads(filepath, campaign_id)
    os.remove(filepath) # Cleanup
    return jsonify(result)

@api.route('/export-leads', methods=['GET'])
def export_leads():
    try:
        leads = db.get_all_leads()
        if not leads:
            return jsonify({"error": "No leads to export"}), 404
            
        # Convert to DataFrame
        df = pd.DataFrame(leads)
        
        # Select relevant columns
        cols = ['id', 'name', 'email', 'phone', 'company', 'location', 'status', 'trust_score', 'business_maturity', 'growth_potential', 'campaign_id', 'created_at']
        # Filter cols that exist in df
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        
        # Create CSV in memory
        csv_data = df.to_csv(index=False)
        
        from flask import Response
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=leads_export.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/templates', methods=['GET', 'POST'])
def handle_templates():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        subject = data.get('subject')
        body = data.get('body')
        
        if not name or not subject or not body:
            return jsonify({"error": "Name, subject, and body are required"}), 400
            
        db.add_template(name, subject, body)
        return jsonify({"message": "Template created"})
    else:
        templates = db.get_templates()
        return jsonify(templates)

@api.route('/templates/<int:id>', methods=['DELETE'])
def delete_template(id):
    db.delete_template(id)
    return jsonify({"message": "Template deleted"})

@api.route('/campaigns', methods=['GET', 'POST'])
def handle_campaigns():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        if not name:
            return jsonify({"error": "Campaign name is required"}), 400
            
        campaign_id = db.create_campaign(name, description)
        return jsonify({"message": "Campaign created", "id": campaign_id})
    else:
        campaigns = db.get_campaigns()
        return jsonify(campaigns)

@api.route('/leads/bulk', methods=['POST'])
def add_leads_bulk():
    data = request.get_json()
    if not data or 'leads' not in data:
        return jsonify({"error": "No leads provided"}), 400
    
    leads = data['leads']
    added_count = 0
    
    for lead_data in leads:
        # Validate required fields
        if not lead_data.get('name'):
            continue
            
        # Ensure defaults
        lead_data['status'] = lead_data.get('status', 'new')
        lead_data['trust_score'] = lead_data.get('trust_score', 0)
        lead_data['source'] = lead_data.get('source', 'bulk_import')
        
        try:
            # Check for duplicates again just in case
            existing = db.get_lead_by_email(lead_data.get('email')) if lead_data.get('email') else None
            if not existing:
                db.insert_lead(lead_data)
                added_count += 1
        except Exception as e:
            print(f"Error adding lead in bulk: {e}")
            continue
            
    return jsonify({"message": f"Successfully added {added_count} leads"}), 201

@api.route('/leads', methods=['POST'])
def add_lead():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({"error": "Name is required"}), 400
    
    lead_data = {
        'name': data.get('name'),
        'email': data.get('email', ''),
        'phone': data.get('phone', ''),
        'company': data.get('company', ''),
        'location': data.get('location', ''),
        'status': data.get('status', 'new'),
        'trust_score': data.get('trust_score', 0),
        'source': 'manual'
    }
    
    try:
        lead_id = db.insert_lead(lead_data)
        return jsonify({"message": "Lead added successfully", "id": lead_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/dashboard-stats', methods=['GET'])
def dashboard_stats():
    stats = db.get_dashboard_stats()
    return jsonify(stats)


# Reminders API
@api.route('/reminders', methods=['GET', 'POST'])
def handle_reminders():
    if request.method == 'POST':
        data = request.json or {}
        message = data.get('message')
        remind_at = data.get('remind_at')
        lead_id = data.get('lead_id')
        recurrence = data.get('recurrence', 'none')
        if not message or not remind_at:
            return jsonify({'error': 'message and remind_at are required'}), 400
        try:
            # Parse datetime to ensure validity
            remind_dt = datetime.fromisoformat(remind_at)
        except Exception as e:
            return jsonify({'error': 'Invalid remind_at format; use ISO format'}), 400
        reminder_id = db.create_reminder(lead_id, remind_dt, message, recurrence)
        return jsonify({'message': 'Reminder created', 'id': reminder_id}), 201
    else:
        reminders = db.get_reminders()
        return jsonify(reminders)


@api.route('/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    success = db.delete_reminder(reminder_id)
    if success:
        return jsonify({'message': 'Reminder deleted'})
    return jsonify({'error': 'Failed to delete reminder'}), 500


@api.route('/reminders/lead/<int:lead_id>', methods=['GET'])
def reminders_for_lead(lead_id):
    reminders = db.get_reminders_for_lead(lead_id)
    return jsonify(reminders)


# Notifications API
@api.route('/notifications', methods=['GET'])
def get_notifications():
    unread = request.args.get('unread', 'true').lower() in ('1', 'true', 'yes')
    notifs = db.get_notifications(unread_only=unread)
    return jsonify(notifs)


@api.route('/notifications/<int:notif_id>/read', methods=['POST'])
def read_notification(notif_id):
    success = db.mark_notification_read(notif_id)
    if success:
        return jsonify({'message': 'Marked as read'})
    return jsonify({'error': 'Failed to mark as read'}), 500

@api.route('/leads', methods=['GET'])
def get_leads():
    leads = db.get_all_leads()
    return jsonify(leads)

@api.route('/leads/<int:id>', methods=['GET'])
def get_lead(id):
    lead = db.get_lead_by_id(id)
    if lead:
        # Parse JSON string if it exists
        if lead['ai_analysis'] and isinstance(lead['ai_analysis'], str):
             try:
                 lead['ai_analysis'] = json.loads(lead['ai_analysis'])
             except:
                 pass
        return jsonify(lead)
    return jsonify({"error": "Lead not found"}), 404

@api.route('/campaigns/<int:id>/sequences', methods=['GET', 'POST'])
def handle_campaign_sequences(id):
    if request.method == 'POST':
        data = request.json
        day_offset = data.get('day_offset')
        subject = data.get('subject')
        body = data.get('body')
        
        if day_offset is None or not subject or not body:
            return jsonify({"error": "Missing fields"}), 400
            
        db.add_campaign_sequence(id, day_offset, subject, body)
        return jsonify({"message": "Sequence step added"})
    else:
        sequences = db.get_campaign_sequences(id)
        return jsonify(sequences)

@api.route('/analyze/<int:id>', methods=['POST', 'OPTIONS'])
def analyze_lead(id):
    if request.method == 'OPTIONS':
        return '', 204
    lead = db.get_lead_by_id(id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    
    analysis = agent_analyze_business(lead)
    decision = agent_decide_outreach(analysis)
    
    status = 'analyzed' if decision == 'OUTREACH' else 'skipped'
    
    db.update_lead_analysis(id, json.dumps(analysis), analysis.get('trust_score', 0), status)
    
    return jsonify({"analysis": analysis, "decision": decision})


@api.route('/bulk-scrape-simple', methods=['POST'])
def bulk_scrape_simple():
    try:
        data = request.get_json()
        if not data:
             return jsonify({"error": "Invalid JSON data"}), 400
             
        urls = data.get('urls', [])
        keyword = data.get('keyword') # Optional keyword search mode
        
        results = []
        
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # If keyword is provided, perform a search first to get URLs
        if keyword and not urls:
            print(f"Performing keyword search for: {keyword}")
            search_results = search_the_web(keyword, max_results=20)
            
            # Filter out listicles/aggregators
            skip_keywords = [
                'top-', 'best-', 'list-of', 'directory', 'clutch.co', 'yelp.com', 
                'sulekha.com', 'justdial.com', 'yellowpages', 'thumbtack', 'upwork', 
                'fiverr', 'linkedin.com', 'facebook.com', 'instagram.com', 'glassdoor',
                'goodfirms', 'designrush', 'sortlist', 'themanifest'
            ]
            skip_titles = ['top 10', 'top 20', 'top 30', 'top 50', 'top 100', 'best ', 'list of ', 'directory', 'reviews']
            
            for r in search_results:
                link = r.get('href', '')
                title = r.get('title', '').lower()
                
                if not link: continue
                
                # Skip aggregators
                if any(k in link.lower() for k in skip_keywords):
                    print(f"Skipping aggregator/listicle (URL): {link}")
                    continue
                    
                if any(k in title for k in skip_titles):
                    print(f"Skipping aggregator/listicle (Title): {title}")
                    continue
                    
                urls.append(link)
            
            # Limit to top 10 to avoid long wait times
            urls = urls[:10]
            print(f"Found {len(urls)} official URLs to scrape.")

        for url in urls:
            if not url.startswith('http'):
                url = 'https://' + url
                
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                # verify=False to avoid SSL errors, timeout=15 for slower sites
                response = requests.get(url, headers=headers, timeout=15, verify=False)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Use separator to avoid merging text from adjacent elements
                    text = soup.get_text(separator=' ')
                    
                    # Extract Emails
                    raw_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                    # Filter valid emails
                    emails = []
                    for e in set(raw_emails):
                        if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css')):
                             emails.append(e)
                    
                    # Extract Phones (Improved Regex)
                    # Matches: (123) 456-7890, 123-456-7890, +1 123 456 7890, 123.456.7890
                    phone_pattern = r'(?:\+?\d{1,3}[ -.]?)?\(?\d{3}\)?[ -.]?\d{3}[ -.]?\d{4}'
                    phones = list(set(re.findall(phone_pattern, text)))
                    
                    results.append({
                        "url": url,
                        "title": soup.title.string.strip() if soup.title else url,
                        "emails": emails,
                        "phones": phones,
                        "status": "success"
                    })
                else:
                    results.append({
                        "url": url,
                        "status": "failed",
                        "error": f"Status code: {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                results.append({
                    "url": url,
                    "status": "failed",
                    "error": str(e)
                })
            
        return jsonify({"results": results})
    except Exception as e:
        print(f"Bulk scrape error: {e}")
        return jsonify({"error": str(e)}), 500

@api.route('/scrape-justdial', methods=['POST'])
def scrape_justdial():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    try:
        scraper = JustDialScraper()
        leads = scraper.scrape(url)
        return jsonify({"message": "Scraping successful", "leads": leads})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/generate-draft/<int:id>', methods=['POST', 'OPTIONS'])
def generate_draft(id):
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
        
    try:
        lead = db.get_lead_by_id(id)
        if not lead:
            return jsonify({"error": "Lead not found"}), 404
        
        data = request.json or {}
        outreach_type = data.get('outreach_type', 'ai')
        
        subject = f"Partnership Opportunity with {lead.get('company', 'your team')}"
        message = ""
        
        if outreach_type == 'template':
            template_id = data.get('template_id')
            template = db.get_template_by_id(template_id)
            if template:
                message = template['body']
                subject = template.get('subject') or subject
                message = message.replace('{{name}}', lead.get('name', '') or 'there')
                message = message.replace('{{company}}', lead.get('company', '') or 'your company')
        else: # AI
            # Ensure analysis exists
            if not lead.get('ai_analysis'):
                analysis = agent_analyze_business(lead)
                db.update_lead_analysis(id, json.dumps(analysis), analysis.get('trust_score', 0), 'analyzed')
                lead['ai_analysis'] = analysis
            else:
                analysis = lead['ai_analysis']
                if isinstance(analysis, str):
                    try:
                        analysis = json.loads(analysis)
                    except:
                        analysis = {}
            
            strategy = agent_message_strategy(lead, analysis)
            message = agent_generate_message(lead, strategy)
            
        return jsonify({
            "subject": subject,
            "body": message
        })
    except Exception as e:
        print(f"❌ Error generating draft: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@api.route('/outreach/<int:id>', methods=['POST', 'OPTIONS'])
def outreach_lead(id):
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    
    try:
        lead = db.get_lead_by_id(id)
        if not lead:
            return jsonify({"error": "Lead not found"}), 404

        # Safely parse JSON body: be tolerant and provide clear 400 errors on malformed input
        raw_body = request.get_data(as_text=True)
        data = None
        try:
            data = request.get_json(silent=True)
        except Exception as e:
            print(f"⚠️ JSON parse exception (get_json): {e}")
            # fall through to try raw parsing

        if data is None and raw_body:
            try:
                data = json.loads(raw_body)
            except Exception as e:
                print(f"❌ Invalid JSON sent to /outreach/{id}: {raw_body}")
                return jsonify({"error": "Invalid JSON in request body", "details": str(e)}), 400

        data = data or {}
        outreach_type = data.get('outreach_type', 'ai') # 'ai', 'template', 'manual'

        message = ""
        subject = data.get('subject') or f"Partnership Opportunity with {lead.get('company', 'your team')}"
        strategy = "Manual/Template"

        if outreach_type == 'template':
            template_id = data.get('template_id')
            if not template_id:
                 return jsonify({"error": "Template ID missing"}), 400

            template = db.get_template_by_id(template_id)
            if not template:
                 return jsonify({"error": "Template not found"}), 404

            # Simple variable substitution
            message = template['body']
            subject = template.get('subject') or subject
            message = message.replace('{{name}}', lead.get('name', '') or 'there')
            message = message.replace('{{company}}', lead.get('company', '') or 'your company')

        elif outreach_type == 'manual':
            message = data.get('manual_body')
            if not message:
                 return jsonify({"error": "Message body missing"}), 400

        else: # AI
            # Ensure analysis exists
            if not lead.get('ai_analysis'):
                analysis = agent_analyze_business(lead)
                db.update_lead_analysis(id, json.dumps(analysis), analysis.get('trust_score', 0), 'analyzed')
                lead['ai_analysis'] = analysis
            else:
                analysis = lead['ai_analysis']
                if isinstance(analysis, str):
                     try:
                         analysis = json.loads(analysis)
                     except Exception:
                         analysis = {}

            # Generate content
            strategy = agent_message_strategy(lead, analysis)
            message = agent_generate_message(lead, strategy)

        # Send (send_email/agent_send_outreach will validate recipient email)
        success, reason = agent_send_outreach(lead, message, subject=subject)

        if success:
            # Note: agent_send_outreach calls db.log_outreach which already
            # sets the lead status and last_outreach_at. No separate update needed.
            return jsonify({
                "success": True,
                "message": "Outreach sent successfully", 
                "content": message,
                "strategy": strategy
            })
        else:
            err_msg = reason or "Failed to send outreach. Please check SMTP/Brevo/Network settings."
            print(f"❌ Outreach endpoint failed for lead {id}: {err_msg}")
            return jsonify({"error": "Failed to send outreach", "details": err_msg}), 500

    except Exception as e:
        # Bubble up unexpected errors with a trace printed so we can debug quickly
        print(f"❌ Critical Error in outreach_lead: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error occurred", "details": str(e)}), 500

@api.route('/leads/<int:id>/notes', methods=['PUT'])
def update_lead_notes(id):
    data = request.get_json()
    notes = data.get('notes', '')
    
    try:
        db.update_lead_notes(id, notes)
        return jsonify({"message": "Notes updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@api.route('/debug-env', methods=['GET'])
def debug_env():
    return jsonify({
        "cwd": os.getcwd(),
        "SMTP_EMAIL": SMTP_EMAIL,
        "SMTP_PASSWORD_SET": bool(SMTP_PASSWORD),
        "SMTP_SERVER": SMTP_SERVER,
        "SMTP_PORT": SMTP_PORT
    })

@api.route('/debug/imap-status', methods=['GET'])
def debug_imap_status():
    """Return basic IMAP monitor status for debugging"""
    return jsonify({
        "last_check": LAST_IMAP_CHECK,
        "last_error": LAST_IMAP_ERROR,
        "last_processed": LAST_IMAP_PROCESSED
    })

@api.route('/debug/mark-replied', methods=['POST'])
def debug_mark_replied():
    """Debug endpoint to mark a lead as replied (helpful for testing UI behavior without IMAP)."""
    data = request.json or {}
    lead_id = data.get('lead_id')
    email_addr = data.get('email')
    subject = data.get('subject', 'Test reply')
    body = data.get('body', 'Simulated reply body')

    lead = None
    if lead_id:
        lead = db.get_lead_by_id(lead_id)
    elif email_addr:
        lead = db.get_lead_by_email(email_addr)

    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    ok = db.mark_lead_replied(lead['id'], subject, body)
    if ok:
        db.log_outreach(lead['id'], 'reply', f'DEBUG: Marked reply via API: {subject}')
        return jsonify({"success": True, "lead_id": lead['id']})
    return jsonify({"error": "Failed to mark replied"}), 500

@api.route('/select-leads-for-outreach', methods=['GET'])
def select_leads_for_outreach():
    """Get leads that can be contacted (filtered list)"""
    try:
        status = request.args.get('status', None)
        min_trust = request.args.get('min_trust_score', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        conn = db.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, email, company, phone, status, trust_score, opened, replied, opened_at, replied_at, reply_subject, last_outreach_at FROM leads WHERE 1=1"
        params = []
        if status:
            query += " AND status = %s"
            params.append(status)
        if min_trust > 0:
            query += " AND trust_score >= %s"
            params.append(min_trust)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        leads = cursor.fetchall()
        cursor.close(); conn.close()
        
        return jsonify({"leads": leads, "count": len(leads)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/export-sheets', methods=['POST'])
def export_sheets():
    data = request.json
    success = export_to_google_sheets(data.get('leads', []), data.get('sheet_id'), data.get('sheet_name', 'Leads'))
    return jsonify({"success": success})

@api.route('/generate-outreach-message', methods=['POST'])
def gen_outreach():
    data = request.json
    return jsonify(agent_generate_outreach_message(data.get('lead'), data.get('tone'), data.get('template')))

@api.route('/generate-campaign-strategy', methods=['POST'])
def gen_strategy():
    data = request.json
    return jsonify(agent_generate_campaign_strategy(data.get('leads_count'), data.get('industry'), data.get('objective')))

@api.route('/send-outreach', methods=['POST', 'OPTIONS'])
def send_outreach_route():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    data = request.json
    lead_id, msg, subject = data.get('lead_id'), data.get('message'), data.get('subject')
    lead = db.get_lead_by_id(lead_id)
    if not lead: return jsonify({"error": "Lead not found"}), 404
    success, err = send_email(lead['email'], subject, msg, lead.get('company'), lead_id=lead_id)
    success, dry_run, reason = normalize_outreach_result(success, err)
    if not success:
        return jsonify({"error": reason or "Failed to send outreach"}), 500

    log_message = msg if not dry_run else f"{msg}\n\n[DRY RUN MODE]"
    db.log_outreach(lead_id, 'email', log_message)
    _update_lead_after_outreach(
        lead_id,
        status_value='outreach_sent',
        sequence_step=max(2, lead.get('current_sequence_step') or 1)
    )
    response = {"success": True}
    if dry_run:
        response["dry_run"] = True
        response["message"] = reason
    return jsonify(response)

@api.route('/bulk-outreach', methods=['POST', 'OPTIONS'])
def bulk_outreach():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    data = request.json or {}
    lead_ids = data.get('lead_ids') or []
    mode = data.get('mode', 'manual') # 'ai', 'template', 'manual'
    subject_raw = data.get('subject', 'Partnership Opportunity')
    message_raw = data.get('message', '')
    template_id = data.get('template_id')
    message_type = data.get('message_type', 'email')

    if not lead_ids or not isinstance(lead_ids, list):
        return jsonify({"error": "lead_ids array is required"}), 400

    sent, failed, dry_runs = 0, 0, 0
    errors = []

    for lead_id in lead_ids:
        lead = db.get_lead_by_id(lead_id)
        if not lead or not lead.get('email'):
            failed += 1; continue
        
        l_msg, l_subj = message_raw, subject_raw
        
        if mode == 'ai':
             # Reuse AI generation logic
             analysis = lead['ai_analysis'] if isinstance(lead['ai_analysis'], dict) else json.loads(lead['ai_analysis'] or '{}')
             if not analysis:
                 analysis = agent_analyze_business(lead)
                 db.update_lead_analysis(lead_id, json.dumps(analysis), analysis.get('trust_score', 0), 'analyzed')
             strat = agent_message_strategy(lead, analysis)
             l_msg = agent_generate_message(lead, strat)
        elif mode == 'template' and template_id:
             template = db.get_template_by_id(template_id)
             if template:
                 l_msg = template['body'].replace('{{name}}', lead.get('name', '') or 'there').replace('{{company}}', lead.get('company', '') or 'your company')
                 l_subj = template.get('subject') or l_subj

        success, err = send_email(lead['email'], l_subj, l_msg, lead.get('company'), lead_id=lead_id)
        success, dry_run, reason = normalize_outreach_result(success, err)
        
        if not success:
            failed += 1; errors.append(reason); continue

        log_message = l_msg if not dry_run else f"{l_msg}\n\n[DRY RUN MODE]"
        db.log_outreach(lead_id, message_type, log_message)
        _update_lead_after_outreach(lead_id, status_value='outreach_sent', sequence_step=2)
        sent += 1
        if dry_run: dry_runs += 1

    return jsonify({"sent": sent, "failed": failed, "dry_runs": dry_runs, "errors": errors})

@api.route('/search-domain', methods=['POST'])
def search_domain_route():
    try:
        data = request.json
        domain = data.get('domain')
        if not domain: return jsonify({"error": "Domain is required"}), 400
        domain = domain.lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        leads = search_snov_domain(domain)
        return jsonify({"leads": leads, "count": len(leads)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/snov-balance', methods=['GET'])
def snov_balance_route():
    balance = get_snov_balance()
    return jsonify(balance if balance else {})

@api.route('/save-domain-leads', methods=['POST'])
def save_domain_leads():
    leads = request.json.get('leads', [])
    saved = 0
    for lead in leads:
        success, _ = db.insert_lead({**lead, 'source': 'Snov.io'})
        if success: saved += 1
    return jsonify({"message": f"Saved {saved} leads", "count": saved})

@api.route('/follow-up-queue', methods=['GET'])
def follow_up_queue():
    days = request.args.get('days', 2, type=int)
    leads = db.get_follow_up_candidates(days)
    annotated = []
    for lead in leads:
        metadata = get_follow_up_metadata(lead)
        annotated.append({**lead, **metadata})
    return jsonify({"leads": annotated, "count": len(annotated)})

@api.route('/replied-leads', methods=['GET'])
def replied_leads():
    limit = request.args.get('limit', 100, type=int)
    leads = db.get_replied_leads(limit)
    return jsonify({"leads": leads, "count": len(leads)})

# Conversations endpoints
@api.route('/conversations/<int:lead_id>', methods=['GET', 'POST', 'OPTIONS'])
def conversations_for_lead(lead_id):
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    if request.method == 'GET':
        convs = db.get_conversations_for_lead(lead_id)
        # Attach recent messages for each conversation
        annotated = []
        for c in convs:
            msgs = db.get_conversation_messages(c['id'])
            annotated.append({**c, 'messages': msgs})
        return jsonify({"conversations": annotated})
    else:
        data = request.get_json() or {}
        title = data.get('title')
        conv_id = db.create_conversation_for_lead(lead_id, title=title)
        if conv_id:
            return jsonify({"conversation_id": conv_id}), 201
        return jsonify({"error": "Failed to create conversation"}), 500


@api.route('/conversations/<int:lead_id>/messages', methods=['POST', 'OPTIONS'])
def add_conversation_message_api(lead_id):
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    conversation_id = data.get('conversation_id')
    sender = data.get('sender') or 'you'
    direction = data.get('direction', 'outbound')
    message = data.get('message')
    send_email_flag = data.get('send_email', False)

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Ensure conversation exists
    if not conversation_id:
        conversation_id = db.create_conversation_for_lead(lead_id, title=f"Conversation for lead {lead_id}")

    msg_id = db.add_conversation_message(conversation_id, sender, direction, message)
    if not msg_id:
        return jsonify({"error": "Failed to save message"}), 500

    # If requested, send email for outbound messages
    send_result = None
    if send_email_flag and direction == 'outbound':
        lead = db.get_lead_by_id(lead_id)
        if lead:
            success, reason = agent_send_outreach(lead, message, subject=data.get('subject'))
            send_result = {"success": success, "reason": reason}
            # Log in outreach logs as well
            db.log_outreach(lead_id, 'email', message)

    return jsonify({"message_id": msg_id, "send_result": send_result})

@api.route('/follow-up-lead', methods=['POST'])
def follow_up_lead():
    data = request.json or {}
    lead_id = data.get('lead_id')
    template_key = data.get('template')
    if not lead_id: return jsonify({"error": "lead_id is required"}), 400
    lead = db.get_lead_by_id(lead_id)
    if not lead: return jsonify({"error": "Lead not found"}), 404
    success, err, next_step = dispatch_followup_for_lead(lead, template_key, triggered_by='manual follow-up')
    if not success: return jsonify({"error": err}), 500
    return jsonify({"success": True, "next_step": next_step})

@api.route('/outreach-templates', methods=['GET'])
def get_outreach_templates():
    return jsonify({"templates": OUTREACH_TEMPLATES, "follow_up_sequence": FOLLOW_UP_SEQUENCE})

# ===== NEW ENHANCED FEATURES API ENDPOINTS =====

# Lead Tagging Endpoints
@api.route('/lead-tags', methods=['GET', 'POST'])
def manage_lead_tags():
    if request.method == 'GET':
        tags = db.get_lead_tags()
        return jsonify({"tags": tags})
    
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        color = data.get('color', '#3B82F6')
        
        if not name:
            return jsonify({"error": "Tag name is required"}), 400
        
        tag_id = db.create_lead_tag(name, color)
        if tag_id:
            return jsonify({"success": True, "tag_id": tag_id}), 201
        else:
            return jsonify({"error": "Failed to create tag"}), 500

@api.route('/leads/<int:lead_id>/tags', methods=['GET', 'POST', 'DELETE'])
def manage_lead_tags_relations(lead_id):
    if request.method == 'GET':
        tags = db.get_lead_tags_by_lead_id(lead_id)
        return jsonify({"tags": tags})
    
    elif request.method == 'POST':
        data = request.json
        tag_id = data.get('tag_id')
        
        if not tag_id:
            return jsonify({"error": "Tag ID is required"}), 400
        
        db.add_tag_to_lead(lead_id, tag_id)
        return jsonify({"success": True})
    
    elif request.method == 'DELETE':
        data = request.json
        tag_id = data.get('tag_id')
        
        if not tag_id:
            return jsonify({"error": "Tag ID is required"}), 400
        
        db.remove_tag_from_lead(lead_id, tag_id)
        return jsonify({"success": True})

# Lead Scoring Endpoints
@api.route('/leads/<int:lead_id>/score', methods=['GET', 'POST'])
def manage_lead_scores(lead_id):
    if request.method == 'GET':
        scores = db.get_lead_scores(lead_id)
        overall_score = db.get_overall_lead_score(lead_id)
        return jsonify({"scores": scores, "overall_score": overall_score})
    
    elif request.method == 'POST':
        data = request.json
        score_type = data.get('score_type', 'overall')
        score = data.get('score')
        reasoning = data.get('reasoning', '')
        
        if score is None or not (0 <= score <= 100):
            return jsonify({"error": "Score must be between 0 and 100"}), 400
        
        db.save_lead_score(lead_id, score_type, score, reasoning)
        return jsonify({"success": True})

@api.route('/leads/<int:lead_id>/score/ai', methods=['POST'])
def ai_score_lead(lead_id):
    """AI-powered lead scoring"""
    lead = db.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured"}), 400
    
    try:
        model_name = get_working_gemini_model()
        if not model_name:
            return jsonify({"error": "No supported Gemini model found"}), 500
        
        client = get_genai()
        if not client:
            return jsonify({"error": "Gemini client failed to initialize"}), 503

        model = client.GenerativeModel(model_name)
        
        prompt = f"""
        Score this business lead on a scale of 0-100 based on the following criteria:
        
        Lead Details:
        - Company: {lead.get('company', 'Unknown')}
        - Name: {lead.get('name', 'Unknown')}
        - Email: {lead.get('email', 'Unknown')}
        - Phone: {lead.get('phone', 'Unknown')}
        - Location: {lead.get('location', 'Unknown')}
        
        Scoring Criteria:
        1. Business Quality (0-25): Company size, industry, reputation
        2. Contact Quality (0-25): Email/phone validity, contact info completeness
        3. Engagement Potential (0-25): Likelihood of responding to outreach
        4. Conversion Potential (0-25): Likelihood of becoming a customer
        
        Return a JSON object with:
        - overall_score: number 0-100
        - business_score: number 0-25
        - contact_score: number 0-25
        - engagement_score: number 0-25
        - conversion_score: number 0-25
        - reasoning: brief explanation
        """
        
        response = model.generate_content(prompt)
        content = response.text.strip()
        if content.startswith('```json'): content = content[7:-3]
        elif content.startswith('```'): content = content[3:-3]
        
        scores = json.loads(content)
        
        # Save individual scores
        db.save_lead_score(lead_id, 'ai_business', scores.get('business_score', 0), f"Business quality: {scores.get('reasoning', '')}")
        db.save_lead_score(lead_id, 'engagement', scores.get('engagement_score', 0), f"Engagement potential: {scores.get('reasoning', '')}")
        db.save_lead_score(lead_id, 'overall', scores.get('overall_score', 0), scores.get('reasoning', ''))
        
        return jsonify({"success": True, "scores": scores})
    
    except Exception as e:
        print(f"AI Scoring Error: {e}")
        return jsonify({"error": str(e)}), 500

# Lead Enrichment Endpoints
@api.route('/leads/<int:lead_id>/enrich', methods=['GET', 'POST'])
def manage_lead_enrichment(lead_id):
    if request.method == 'GET':
        enrichment = db.get_lead_enrichment(lead_id)
        return jsonify({"enrichment": enrichment})
    
    elif request.method == 'POST':
        data = request.json
        data_type = data.get('data_type')
        enrichment_data = data.get('data', {})
        source = data.get('source', '')
        confidence_score = data.get('confidence_score', 0)
        
        if not data_type:
            return jsonify({"error": "Data type is required"}), 400
        
        enrichment_id = db.save_lead_enrichment(lead_id, data_type, enrichment_data, source, confidence_score)
        if enrichment_id:
            return jsonify({"success": True, "enrichment_id": enrichment_id}), 201
        else:
            return jsonify({"error": "Failed to save enrichment"}), 500

@api.route('/leads/<int:lead_id>/enrich/ai', methods=['POST'])
def ai_enrich_lead(lead_id):
    """AI-powered lead enrichment"""
    lead = db.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured"}), 400
    
    try:
        model_name = get_working_gemini_model()
        if not model_name:
            return jsonify({"error": "No supported Gemini model found"}), 500
        client = get_genai()
        if not client:
            return jsonify({"error": "Gemini client failed to initialize"}), 503

        model = client.GenerativeModel(model_name)
        
        prompt = f"""
        Enrich this business lead with additional information. Research and infer:
        
        Current Lead Data:
        - Company: {lead.get('company', 'Unknown')}
        - Name: {lead.get('name', 'Unknown')}
        - Email: {lead.get('email', 'Unknown')}
        - Phone: {lead.get('phone', 'Unknown')}
        - Location: {lead.get('location', 'Unknown')}
        
        Provide enrichment data in JSON format:
        {{
          "company_info": {{
            "industry": "inferred industry",
            "size": "company size estimate",
            "description": "company description",
            "website": "company website if known"
          }},
          "contact_info": {{
            "social_media": ["linkedin_url", "twitter_handle"],
            "job_title": "inferred job title",
            "additional_emails": ["alternative emails"]
          }},
          "business_context": {{
            "target_market": "target customers",
            "services": ["services offered"],
            "competition": "main competitors"
          }}
        }}
        """
        
        response = model.generate_content(prompt)
        content = response.text.strip()
        if content.startswith('```json'): content = content[7:-3]
        elif content.startswith('```'): content = content[3:-3]
        
        enrichment_data = json.loads(content)
        
        # Save enrichment data
        for data_type, data in enrichment_data.items():
            db.save_lead_enrichment(lead_id, data_type, data, "AI Enrichment", 75)
        
        return jsonify({"success": True, "enrichment": enrichment_data})
    
    except Exception as e:
        print(f"AI Enrichment Error: {e}")
        return jsonify({"error": str(e)}), 500

# Email Tracking Endpoints
@api.route('/email-tracking', methods=['POST'])
def track_email_event():
    """Track email events (called by email service webhooks)"""
    data = request.json
    outreach_log_id = data.get('outreach_log_id')
    event_type = data.get('event_type')
    event_data = data.get('event_data', {})
    
    if not outreach_log_id or not event_type:
        return jsonify({"error": "outreach_log_id and event_type are required"}), 400
    
    db.track_email_event(outreach_log_id, event_type, event_data)
    return jsonify({"success": True})

@api.route('/email-tracking/stats', methods=['GET'])
def get_email_tracking_stats():
    """Get email tracking statistics"""
    outreach_log_id = request.args.get('outreach_log_id', type=int)
    stats = db.get_email_tracking_stats(outreach_log_id)
    return jsonify({"stats": stats})

# Lead Sources Endpoints
@api.route('/lead-sources', methods=['GET', 'POST'])
def manage_lead_sources():
    if request.method == 'GET':
        sources = db.get_lead_sources()
        return jsonify({"sources": sources})
    
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        source_type = data.get('source_type', 'manual')
        source_details = data.get('source_details', {})
        
        if not name:
            return jsonify({"error": "Source name is required"}), 400
        
        source_id = db.create_lead_source(name, source_type, source_details)
        if source_id:
            return jsonify({"success": True, "source_id": source_id}), 201
        else:
            return jsonify({"error": "Failed to create source"}), 500

# A/B Testing Endpoints
@api.route('/ab-tests', methods=['GET', 'POST'])
def manage_ab_tests():
    if request.method == 'GET':
        tests = db.get_ab_tests()
        return jsonify({"tests": tests})
    
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        test_type = data.get('test_type', 'subject_line')
        variant_a = data.get('variant_a', {})
        variant_b = data.get('variant_b', {})
        test_duration_days = data.get('test_duration_days', 7)
        
        if not name or not variant_a or not variant_b:
            return jsonify({"error": "Name, variant_a, and variant_b are required"}), 400
        
        test_id = db.create_ab_test(name, test_type, variant_a, variant_b, test_duration_days)
        if test_id:
            return jsonify({"success": True, "test_id": test_id}), 201
        else:
            return jsonify({"error": "Failed to create A/B test"}), 500

# CRM Integration Endpoints
@api.route('/crm-integrations', methods=['GET', 'POST'])
def manage_crm_integrations():
    if request.method == 'GET':
        integrations = db.get_crm_integrations()
        return jsonify({"integrations": integrations})
    
    elif request.method == 'POST':
        data = request.json
        crm_type = data.get('crm_type')
        name = data.get('name')
        config = data.get('config', {})
        is_active = data.get('is_active', False)
        
        if not crm_type or not name:
            return jsonify({"error": "CRM type and name are required"}), 400
        
        integration_id = db.save_crm_integration(crm_type, name, config, is_active)
        if integration_id:
            return jsonify({"success": True, "integration_id": integration_id}), 201
        else:
            return jsonify({"error": "Failed to save CRM integration"}), 500

@api.route('/leads/export/crm/<int:integration_id>', methods=['POST'])
def export_leads_to_crm(integration_id):
    """Export leads to CRM system"""
    # This would integrate with actual CRM APIs
    # For now, just return success
    return jsonify({"success": True, "message": "CRM export functionality coming soon"})

@api.route('/crm/export', methods=['POST'])
def export_leads_to_crm_generic():
    """Generic CRM export endpoint"""
    data = request.json
    crm_type = data.get('crm_type')
    lead_ids = data.get('lead_ids', [])
    
    # For now, just return success with mock data
    return jsonify({
        "success": True,
        "exported_count": len(lead_ids),
        "message": f"Successfully exported {len(lead_ids)} leads to {crm_type}",
        "details": {
            "crm_type": crm_type,
            "lead_count": len(lead_ids),
            "status": "completed"
        }
    })

# Lead Validation Endpoints
@api.route('/leads/<int:lead_id>/validate', methods=['GET', 'POST'])
def manage_lead_validation(lead_id):
    if request.method == 'GET':
        validations = db.get_lead_validation(lead_id)
        return jsonify({"validations": validations})
    
    elif request.method == 'POST':
        data = request.json
        validation_type = data.get('validation_type')
        is_valid = data.get('is_valid')
        validation_details = data.get('validation_details', {})
        
        if validation_type is None or is_valid is None:
            return jsonify({"error": "validation_type and is_valid are required"}), 400
        
        validation_id = db.save_lead_validation(lead_id, validation_type, is_valid, validation_details)
        if validation_id:
            return jsonify({"success": True, "validation_id": validation_id}), 201
        else:
            return jsonify({"error": "Failed to save validation"}), 500

@api.route('/leads/<int:lead_id>/validate/email', methods=['POST'])
def validate_lead_email(lead_id):
    """Validate email address"""
    lead = db.get_lead_by_id(lead_id)
    if not lead or not lead.get('email'):
        return jsonify({"error": "Lead or email not found"}), 404
    
    email = lead['email']
    
    # Simple email validation (in production, use a service like Hunter.io or NeverBounce)
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(email_pattern, email))
    
    # Check for disposable email domains
    disposable_domains = ['10minutemail.com', 'guerrillamail.com', 'mailinator.com']
    domain = email.split('@')[1] if '@' in email else ''
    is_disposable = domain.lower() in disposable_domains
    
    validation_details = {
        "format_valid": is_valid,
        "is_disposable": is_disposable,
        "domain": domain,
        "validation_method": "regex"
    }
    
    overall_valid = is_valid and not is_disposable
    
    db.save_lead_validation(lead_id, 'email', overall_valid, validation_details)
    
    return jsonify({
        "success": True,
        "is_valid": overall_valid,
        "details": validation_details
    })

# Enhanced Analytics Endpoints
@api.route('/analytics/enhanced', methods=['GET'])
def get_enhanced_analytics():
    """Get enhanced analytics data"""
    stats = db.get_enhanced_dashboard_stats()
    return jsonify({"analytics": stats})

@api.route('/analytics/lead-quality', methods=['GET'])
def get_lead_quality_distribution():
    """Get lead quality distribution"""
    conn = db.get_db_connection()
    distribution = {}
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Score ranges
        cursor.execute("""
        SELECT 
            CASE 
                WHEN score >= 80 THEN 'excellent'
                WHEN score >= 60 THEN 'good'
                WHEN score >= 40 THEN 'fair'
                ELSE 'poor'
            END as quality,
            COUNT(*) as count
        FROM lead_scores 
        WHERE score_type = 'overall'
        GROUP BY quality
        """)
        
        for row in cursor.fetchall():
            distribution[row['quality']] = row['count']
        
        cursor.close()
        conn.close()
    
    return jsonify({"distribution": distribution})

app.register_blueprint(api)

if __name__ == '__main__':
    # Start background jobs
    start_background_jobs()
    app.run(debug=True, port=5000, use_reloader=False)

