"""
AI Lead Outreach Backend - Consolidated Flask Application
All-in-one backend logic (except database interactions in db.py)
"""
import os
import sys
import json
import re
import requests
import pandas as pd
import html
import threading
import time
import imaplib
import email
from email.utils import parseaddr
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from ddgs import DDGS
from serpapi import Client
from urllib.parse import urlparse
import mysql.connector
from datetime import datetime

# Optional imports
try:
    from google.oauth2.service_account import Credentials
    import gspread
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("⚠️  gspread not available - Google Sheets export disabled")

# Import database module (kept separate as requested)
try:
    import db
    # Skip db init on startup to avoid MySQL connector issues
    # db.init_db()
    print("[OK] Database module loaded")
except Exception as e:
    print(f"[WARN] Database module warning: {e}")

# =================================================================
# CONFIGURATION & INITIALIZATION
# =================================================================
load_dotenv()

# API Keys and Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_KEY")
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

# Initialize AI Clients (lazy loaded)
genai_client = None
groq_client = None

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
    html_body = build_html_body(body, lead_id)
    if BREVO_API_KEY:
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
            payload = {
                "sender": {"email": SMTP_EMAIL or "outreach@yourdomain.com", "name": "Lead Outreach AI"},
                "to": [{"email": to_email, "name": lead_name or to_email.split('@')[0]}],
                "subject": subject,
                "textContent": body,
                "htmlContent": html_body
            }
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code in [200, 201, 202]: return True, None
        except: pass
    return send_email_smtp(to_email, subject, body, html_body, lead_name)

# =================================================================
# SCRAPING FUNCTIONS
# =================================================================

def extract_contacts_from_text(text_content, html_content=""):
    """Extract email and phone from text"""
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content + html_content))
    phone_patterns = [r'\+?\d{1,4}[\s\-\.]?\(?\d{1,4}\)?[\s\-\.]?\d{1,4}[\s\-\.]?\d{1,4}', r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}']
    phones = set()
    for p in phone_patterns: phones.update(re.findall(p, text_content))
    valid_emails = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css'))]
    return list(valid_emails), list(phones), []

def extract_contact_info(url):
    """Scrape website using Playwright"""
    if not url or not url.startswith(('http://', 'https://')): return [], [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0", viewport={'width': 1280, 'height': 720})
            page = context.new_page()
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            text = page.text_content()
            content = page.content()
            browser.close()
            return extract_contacts_from_text(text, content)
    except: return [], [], []

def search_the_web(query, max_results=5):
    """Web search using SerpApi or DDGS"""
    results = []
    if SERPAPI_API_KEY:
        try:
            client = Client(api_key=SERPAPI_API_KEY)
            search = client.search(q=query, engine="google", num=max_results)
            for r in search.get("organic_results", []):
                results.append({'title': r.get('title'), 'href': r.get('link'), 'body': r.get('snippet')})
        except: pass
    if len(results) < max_results:
        try:
            ddgs_results = DDGS().text(query, max_results=max_results - len(results))
            for r in ddgs_results: results.append(r)
        except: pass
    return results

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
        # Endpoint: https://api.snov.io/v2/domain-emails-with-info
        params = {
            'domain': domain,
            'type': 'all',
            'limit': 100,
            'lastId': 0
        }
        headers = {'Authorization': f'Bearer {token}'}
        
        res = requests.get("https://api.snov.io/v2/domain-emails-with-info", params=params, headers=headers, verify=False, timeout=10)
        print(f"[SNOV] API Response Status: {res.status_code}")
        print(f"[SNOV] Raw Response Text: {res.text}")
        
        if res.status_code != 200:
            print(f"[SNOV] API Error Response: {res.text}")
            return []

        try:
            data = res.json()
            print(f"[SNOV] Raw Data: {json.dumps(data)}")
        except json.JSONDecodeError as e:
            print(f"[SNOV] JSON Decode Error: {e}")
            print(f"[SNOV] Response text that failed to decode: {res.text}")
            return []
        
        emails = []
        if isinstance(data, dict):
            if 'emails' in data:
                emails = data['emails']
            elif 'data' in data and isinstance(data['data'], list):
                emails = data['data']
        
        print(f"[SNOV] Extracted {len(emails)} raw email records")
                
        results = []
        for e in emails:
            if not isinstance(e, dict): continue
            
            # Construct a useful name/company representation
            first = e.get('first_name', '')
            last = e.get('last_name', '')
            full_name = f"{first} {last}".strip()
            
            results.append({
                'email': e.get('email'),
                'company': full_name if full_name else (e.get('company_name') or domain), # Use name if available, else company
                'position': e.get('position'),
                'source': 'Snov.io'
            })
            
        return results
    except Exception as e:
        print(f"[SNOV] Search error: {e}")
        import traceback
        traceback.print_exc()
        return []

# =================================================================
# AI AGENT FUNCTIONS
# =================================================================

def call_ai_service(prompt, ai_service="gemini", temperature=0.1):
    """Call Gemini or Groq with fallback"""
    services = [ai_service, "groq" if ai_service == "gemini" else "gemini"]
    for s in services:
        try:
            if s == "gemini":
                _genai = get_genai()
                if _genai:
                    model = _genai.GenerativeModel('gemini-2.0-flash')
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
    prompt = f"Extract business leads from these search results. Return ONLY a JSON array of objects with keys: company, website, email, phone, location, confidence_score, ai_analysis (reasoning, business_maturity, growth_potential), notes.\n\nINPUT:\n{text}"
    res, _ = call_ai_service(prompt, ai_service)
    return extract_json_from_text(res) or []

def agent_ai_extract_leads(text, ai_service="gemini"):
    """Extract leads from text with AI"""
    prompt = f"Extract business leads from this text. Return ONLY a JSON array of objects with keys: company, website, email, phone, location, confidence_score, ai_analysis (reasoning, business_maturity, growth_potential), notes.\n\nINPUT:\n{text}"
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

# =================================================================
# FLASK APP & ROUTES
# =================================================================

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.after_request
def apply_cors(response):
    response.headers.setdefault('Access-Control-Allow-Origin', '*')
    response.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.setdefault('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
    return response

api = Blueprint('api', __name__, url_prefix='/api')


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
    db.log_outreach(lead_id, 'open', 'Tracking pixel detected', update_status=False)
    return '', 204

@api.route('/health', methods=['GET'])
def health(): return jsonify({"status": "healthy", "gemini": bool(GEMINI_API_KEY)})

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
        db.log_outreach(lead['id'], 'reply', f'DEBUG: Marked reply via API: {subject}', update_status=False)
        return jsonify({"success": True, "lead_id": lead['id']})
    return jsonify({"error": "Failed to mark replied"}), 500

@api.route('/web-search', methods=['POST'])
def web_search():
    query = request.json.get('query')
    if not query: return jsonify({"error": "Missing query"}), 400
    return jsonify({"results": search_the_web(query)})

@api.route('/scrape-url', methods=['POST'])
def scrape_url_route():
    data = request.json or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    emails, phones, extras = extract_contact_info(url)
    unique_emails = list(dict.fromkeys([e for e in emails if e]))
    unique_phones = list(dict.fromkeys([p for p in phones if p]))
    scraped_leads = [
        {"email": email, "source": url, "type": "web_scrape"}
        for email in unique_emails
    ]

    return jsonify({
        "url": url,
        "leads": scraped_leads,
        "emails": unique_emails,
        "phones": unique_phones,
        "extras": extras,
        "count": len(unique_emails),
        "message": f"Scraped {len(unique_emails)} emails and {len(unique_phones)} phones"
    })

@api.route('/keyword-search', methods=['POST'])
def keyword_search_route():
    data = request.json or {}
    raw_keywords = data.get('keywords', '')
    keywords = [kw.strip() for kw in raw_keywords.split(',') if kw.strip()]
    max_results = data.get('max_results', 6)

    if not keywords:
        return jsonify({"error": "Provide at least one keyword"}), 400

    aggregated = []
    total_leads = 0
    for keyword in keywords:
        query = f"{keyword} business leads"
        search_results = search_the_web(query, max_results=max_results)
        leads = agent_ai_clean_search_results(search_results)
        aggregated.append({
            "keyword": keyword,
            "query": query,
            "results": search_results,
            "leads": leads,
            "count": len(leads)
        })
        total_leads += len(leads)

    return jsonify({
        "keywords": aggregated,
        "total_keywords": len(aggregated),
        "total_leads": total_leads,
        "message": f"Generated {total_leads} leads from {len(aggregated)} keywords"
    })

@api.route('/search-leads', methods=['POST'])
def search_leads():
    data = request.json
    industry, location = data.get('industry'), data.get('location')
    if not industry or not location: return jsonify({"error": "Missing industry/location"}), 400
    results = search_the_web(f"{industry} leads {location}", max_results=15)
    leads = agent_ai_clean_search_results(results)
    return jsonify({"leads": leads, "count": len(leads)})

@api.route('/clean-search-results', methods=['POST'])
def clean_search_results():
    results = request.json.get('results')
    if not results: return jsonify({"error": "Missing results"}), 400
    leads = agent_ai_clean_search_results(results)
    return jsonify({"leads": leads})

@api.route('/ai-extract', methods=['POST'])
def ai_extract():
    text = request.json.get('text')
    if not text: return jsonify({"error": "Missing text"}), 400
    leads = agent_ai_extract_leads(text)
    return jsonify({"leads": leads, "count": len(leads)})

@api.route('/save-extracted-leads', methods=['POST'])
def save_leads():
    leads = request.json.get('leads', [])
    print(f"[SAVE-LEADS] Received {len(leads)} leads to save: {json.dumps(leads, indent=2)}")
    saved, failed = 0, 0
    for lead in leads:
        success, _ = db.insert_lead(lead)
        if success: saved += 1
        else: failed += 1
    return jsonify({"message": f"Saved {saved}, failed {failed}", "saved": saved, "failed": failed})

@api.route('/save-extracted-leads-no-validation', methods=['POST'])
def save_leads_no_val():
    return save_leads()

@api.route('/leads', methods=['GET', 'POST'])
def manage_leads():
    if request.method == 'POST':
        data = request.json
        success, msg = db.insert_lead(data)
        return jsonify({"success": success, "message": msg}), 201 if success else 400
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        search = request.args.get('search')
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM leads WHERE 1=1"
        params = []
        if status: query += " AND status = %s"; params.append(status)
        if search: query += " AND (email LIKE %s OR company LIKE %s)"; p = f"%{search}%"; params.extend([p, p])
        
        cursor.execute(query.replace("SELECT *", "SELECT COUNT(*)"), params)
        total = cursor.fetchone()['COUNT(*)']
        
        query += f" ORDER BY created_at DESC LIMIT {per_page} OFFSET {(page-1)*per_page}"
        cursor.execute(query, params)
        leads = cursor.fetchall()
        
        for l in leads:
            for k, v in l.items():
                if hasattr(v, 'isoformat'): l[k] = v.isoformat()
        
        cursor.close(); conn.close()
        return jsonify({"leads": leads, "total": total, "pages": (total + per_page - 1) // per_page})
    except Exception as e: return jsonify({"error": str(e)}), 500

@api.route('/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    lead = db.get_lead_by_id(lead_id)
    if not lead: return jsonify({"error": "Not found"}), 404
    for k, v in lead.items():
        if hasattr(v, 'isoformat'): lead[k] = v.isoformat()
    return jsonify(lead)

@api.route('/select-leads-for-outreach', methods=['GET'])
def select_leads_for_outreach():
    """Get leads that can be contacted (filtered list)
    
    Query parameters:
    - status: Filter by status (optional)
    - min_trust_score: Minimum trust score (optional)
    - limit: Maximum results (default 50)
    """
    try:
        status = request.args.get('status', None)
        min_trust = request.args.get('min_trust_score', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        conn = db.get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT id, email, company, phone, status, trust_score, opened, replied, opened_at, replied_at, reply_subject, last_outreach_at FROM leads WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if min_trust > 0:
            query += " AND trust_score >= %s"
            params.append(min_trust)
        
        query += " ORDER BY created_at DESC LIMIT %s" % limit
        
        cursor.execute(query, params)
        leads = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "leads": leads,
            "count": len(leads),
            "filters": {
                "status": status,
                "min_trust_score": min_trust,
                "limit": limit
            }
        })
        
    except Exception as e:
        print(f"Error selecting leads: {e}")
        return jsonify({"error": str(e)}), 500

@api.route('/export-sheets', methods=['POST'])
def export_sheets():
    data = request.json
    success = export_to_google_sheets(data.get('leads', []), data.get('sheet_id'), data.get('sheet_name', 'Leads'))
    return jsonify({"success": success})

@api.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST': return jsonify({"message": "Settings updated"})
    return jsonify({"autopilot": False, "email_template": "", "api_keys": {}})

@api.route('/generate-outreach-message', methods=['POST'])
def gen_outreach():
    data = request.json
    return jsonify(agent_generate_outreach_message(data.get('lead'), data.get('tone'), data.get('template')))

@api.route('/generate-campaign-strategy', methods=['POST'])
def gen_strategy():
    data = request.json
    return jsonify(agent_generate_campaign_strategy(data.get('leads_count'), data.get('industry'), data.get('objective')))

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

    db.log_outreach(lead['id'], 'email', f"{triggered_by} follow-up: {template.get('name')}", update_status=False)
    next_step = min((lead.get('current_sequence_step') or 1) + 1, len(FOLLOW_UP_SEQUENCE) + 1)
    _update_lead_after_outreach(lead['id'], status_value='followup_sent', sequence_step=next_step)
    return True, None, next_step

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
    subject = data.get('subject')
    message = data.get('message')
    message_type = data.get('message_type', 'email')

    if not lead_ids or not isinstance(lead_ids, list):
        return jsonify({"error": "lead_ids array is required"}), 400
    if not subject or not message:
        return jsonify({"error": "subject and message are required"}), 400

    sent = 0
    failed = 0
    errors = []
    dry_runs = 0

    for lead_id in lead_ids:
        lead = db.get_lead_by_id(lead_id)
        if not lead:
            failed += 1
            errors.append(f"Lead {lead_id} not found")
            continue

        email = lead.get('email')
        if not email:
            failed += 1
            errors.append(f"Lead {lead_id} missing email")
            continue

        success, err = send_email(email, subject, message, lead.get('company'), lead_id=lead_id)
        success, dry_run, reason = normalize_outreach_result(success, err)
        if not success:
            failed += 1
            errors.append(reason or f"Failed to send to lead {lead_id}")
            continue

        log_message = message if not dry_run else f"{message}\n\n[DRY RUN MODE]"
        db.log_outreach(lead_id, message_type, log_message)
        _update_lead_after_outreach(
            lead_id,
            status_value='outreach_sent',
            sequence_step=max(2, lead.get('current_sequence_step') or 1)
        )
        sent += 1
        if dry_run:
            dry_runs += 1

    return jsonify({
        "sent": sent,
        "failed": failed,
        "errors": errors,
        "dry_runs": dry_runs,
        "message": f"Sent {sent} messages, {failed} failed"
    })

@api.route('/verify-email', methods=['POST'])
def verify_email_route():
    email = request.json.get('email')
    return jsonify(verify_email_rapid(email))

@api.route('/search-domain', methods=['POST'])
def search_domain_route():
    print("\n[DOMAIN SEARCH] Request received")
    try:
        data = request.json
        print(f"[DOMAIN SEARCH] Payload: {data}")
        domain = data.get('domain')
        
        if not domain:
            print("[DOMAIN SEARCH] Error: Domain is required")
            return jsonify({"error": "Domain is required"}), 400
            
        # Clean domain (remove protocol, www, trailing slashes)
        original_domain = domain
        domain = domain.lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        print(f"[DOMAIN SEARCH] Cleaned domain: '{original_domain}' -> '{domain}'")
            
        print(f"[DOMAIN SEARCH] Searching for: {domain}")
        leads = search_snov_domain(domain)
        print(f"[DOMAIN SEARCH] Found {len(leads)} leads")
        
        message = ""
        if not leads:
            message = f"No emails found for {domain}. Try another domain."
        else:
            message = f"Found {len(leads)} emails for {domain}"
            
        return jsonify({"leads": leads, "count": len(leads), "message": message})
    except Exception as e:
        print(f"[DOMAIN SEARCH] Critical Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@api.route('/snov-balance', methods=['GET'])
def snov_balance_route():
    balance = get_snov_balance()
    return jsonify(balance if balance else {})

@api.route('/save-domain-leads', methods=['POST'])
def save_domain_leads():
    leads = request.json.get('leads', [])
    saved = 0
    errors = []
    for lead in leads:
        success, msg = db.insert_lead({**lead, 'source': 'Snov.io'})
        if success:
            saved += 1
        else:
            errors.append(msg)
    return jsonify({"message": f"Saved {saved} leads", "count": saved, "errors": errors})

@api.route('/dashboard-stats', methods=['GET'])
def dashboard_stats():
    try:
        conn = db.get_db_connection(); cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'outreach_sent'")
        sent = cursor.fetchone()[0]
        cursor.close(); conn.close()
        return jsonify({"total": total, "outreach_sent": sent, "analyzed": total, "converted": 0})
    except: return jsonify({"total": 0, "outreach_sent": 0, "analyzed": 0, "converted": 0})


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


@api.route('/follow-up-lead', methods=['POST'])
def follow_up_lead():
    data = request.json or {}
    lead_id = data.get('lead_id')
    template_key = data.get('template')
    if not lead_id:
        return jsonify({"error": "lead_id is required"}), 400

    lead = db.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    success, err, next_step = dispatch_followup_for_lead(lead, template_key, triggered_by='manual follow-up')
    if not success:
        return jsonify({"error": err or "Failed to send follow-up"}), 500
    return jsonify({"success": True, "next_step": next_step})

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
                            db.log_outreach(lead['id'], 'reply', f'Incoming reply: {subject or sender}', update_status=False)
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


def start_background_jobs():
    start_reply_monitor()
    start_auto_followups()

@api.route('/outreach-templates', methods=['GET'])
def get_templates():
    return jsonify({"templates": OUTREACH_TEMPLATES, "follow_up_sequence": FOLLOW_UP_SEQUENCE})


app.register_blueprint(api)
start_background_jobs()

if __name__ == '__main__':
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

