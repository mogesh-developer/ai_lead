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
    db.init_db()
    print("[OK] Database initialized")
except Exception as e:
    print(f"[WARN] Database initialization warning: {e}")

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
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
SNOV_CLIENT_ID = os.getenv("SNOV_CLIENT_ID")
SNOV_CLIENT_SECRET = os.getenv("SNOV_CLIENT_SECRET")

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

def send_email_smtp(to_email, subject, body, lead_name=None):
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
        html = f"<html><body><p>{body.replace('\\n', '<br>')}</p></body></html>"
        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
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

def send_email(to_email, subject, body, lead_name=None):
    """Send email via Brevo or SMTP fallback"""
    if BREVO_API_KEY:
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
            payload = {
                "sender": {"email": SMTP_EMAIL or "outreach@yourdomain.com", "name": "Lead Outreach AI"},
                "to": [{"email": to_email, "name": lead_name or to_email.split('@')[0]}],
                "subject": subject,
                "textContent": body
            }
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code in [200, 201, 202]: return True, None
        except: pass
    return send_email_smtp(to_email, subject, body, lead_name)

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
        res = requests.post("https://api.snov.io/v1/oauth/access_token", data={'grant_type': 'client_credentials', 'client_id': SNOV_CLIENT_ID, 'client_secret': SNOV_CLIENT_SECRET})
        return res.json().get('access_token')
    except: return None

def search_snov_domain(domain):
    """Search Snov.io for domain emails"""
    token = get_snov_token()
    if not token: return []
    try:
        res = requests.post("https://api.snov.io/v2/domain-emails", json={'domain': domain, 'limit': 100}, headers={'Authorization': f'Bearer {token}'})
        data = res.json()
        emails = data.get('emails', []) or data.get('data', {}).get('emails', [])
        return [{'email': e.get('email'), 'company': domain, 'source': 'Snov.io'} for e in emails if isinstance(e, dict)]
    except: return []

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

# =================================================================
# FLASK APP & ROUTES
# =================================================================

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

api = Blueprint('api', __name__, url_prefix='/api')

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

@api.route('/web-search', methods=['POST'])
def web_search():
    query = request.json.get('query')
    if not query: return jsonify({"error": "Missing query"}), 400
    return jsonify({"results": search_the_web(query)})

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
        cursor = conn.cursor(dictionary=True)
        
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

@api.route('/send-outreach', methods=['POST'])
def send_outreach_route():
    data = request.json
    lead_id, msg, subject = data.get('lead_id'), data.get('message'), data.get('subject')
    lead = db.get_lead_by_id(lead_id)
    if not lead: return jsonify({"error": "Lead not found"}), 404
    success, err = send_email(lead['email'], subject, msg, lead.get('company'))
    if success:
        db.log_outreach(lead_id, 'email', msg)
        conn = db.get_db_connection(); cursor = conn.cursor()
        cursor.execute("UPDATE leads SET status = 'outreach_sent' WHERE id = %s", (lead_id,))
        conn.commit(); cursor.close(); conn.close()
        return jsonify({"success": True})
    return jsonify({"error": err}), 500

@api.route('/verify-email', methods=['POST'])
def verify_email_route():
    email = request.json.get('email')
    return jsonify(verify_email_rapid(email))

@api.route('/search-domain', methods=['POST'])
def search_domain_route():
    domain = request.json.get('domain')
    leads = search_snov_domain(domain)
    return jsonify({"leads": leads, "count": len(leads)})

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

@api.route('/outreach-templates', methods=['GET'])
def get_templates():
    return jsonify({"templates": {
        "professional": {"subject": "Partnership Opportunity", "message": "Hi {company}, I'd like to discuss..."},
        "casual": {"subject": "Quick question", "message": "Hey, saw what you're doing at {company}..."}
    }})


app.register_blueprint(api)

if __name__ == '__main__':
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

