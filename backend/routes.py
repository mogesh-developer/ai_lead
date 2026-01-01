"""API Routes for the Flask application"""
from flask import Blueprint, request, jsonify
from agents import agent_ai_extract_leads, agent_ai_clean_search_results, agent_generate_outreach_message, agent_generate_campaign_strategy
from scrapers import search_the_web, search_snov_domain, extract_contact_info
from helpers import (agent_ingest_leads, export_to_google_sheets, verify_email_rapid,
                     create_outreach_campaign, log_outreach_attempt, track_outreach_response,
                     get_campaign_analytics, send_bulk_outreach_emails)
import db
import json

# Create blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api')


# ============= Web Search Routes =============
@api.route('/web-search', methods=['POST'])
def web_search():
    """Web search with SerpAPI"""
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    
    results = search_the_web(query, max_results=10)
    return jsonify({"results": results})


@api.route('/clean-search-results', methods=['POST'])
def clean_search_results():
    """Clean search results with AI
    
    Request JSON:
        - results: list of search results
        - ai_service: 'gemini' (default) or 'groq' (optional)
    """
    data = request.json
    results = data.get('results')
    ai_service = data.get('ai_service', 'gemini')  # Default to Gemini
    
    if not results or not isinstance(results, list):
        return jsonify({"error": "Missing or invalid results list"}), 400
        
    cleaned_leads = agent_ai_clean_search_results(results, ai_service=ai_service)
    
    if isinstance(cleaned_leads, dict) and "error" in cleaned_leads:
        return jsonify(cleaned_leads), 500
        
    return jsonify({"leads": cleaned_leads, "ai_service": ai_service})


# ============= Lead Extraction Routes =============
@api.route('/ai-extract', methods=['POST'])
def ai_extract():
    """Extract leads from pasted text with AI
    
    Request JSON:
        - text: text to extract leads from
        - ai_service: 'gemini' (default) or 'groq' (optional)
    """
    data = request.json
    text = data.get('text')
    ai_service = data.get('ai_service', 'gemini')  # Default to Gemini
    
    if not text:
        return jsonify({"error": "Missing text"}), 400
        
    leads = agent_ai_extract_leads(text, ai_service=ai_service)
    
    if isinstance(leads, dict) and "error" in leads:
        return jsonify(leads), 500
        
    return jsonify({
        "message": f"Extracted {len(leads)} leads",
        "leads": leads,
        "ai_service": ai_service
    })


@api.route('/save-extracted-leads', methods=['POST'])
def save_extracted_leads():
    """Save extracted leads to database"""
    data = request.json
    leads = data.get('leads')
    
    print(f"\n[SAVE-LEADS] ========== SAVE REQUEST ==========")
    print(f"[SAVE-LEADS] Received request to save {len(leads) if leads else 0} leads")
    
    if not leads or not isinstance(leads, list):
        print(f"[SAVE-LEADS] ✗ Invalid leads format")
        return jsonify({"error": "Missing or invalid leads"}), 400
    
    try:
        saved_count = 0
        failed_count = 0
        errors = []
        failed_leads = []
        
        for i, lead in enumerate(leads):
            try:
                # Log raw extracted data
                print(f"\n[SAVE-LEADS] [{i+1}/{len(leads)}] Raw lead data: {json.dumps(lead)}")
                
                # Prepare lead data for database insertion
                # Support both 'location' and 'position' fields from AI extraction
                location_val = (lead.get('location', '') or lead.get('position', '')).strip()
                
                # Clean and prepare fields
                # Try multiple sources for name: name → company → position → website domain → email prefix
                name = (lead.get('name', '') or '').strip()
                if not name:
                    name = (lead.get('company', '') or '').strip()
                if not name:
                    name = (lead.get('position', '') or '').strip()
                if not name:
                    website = (lead.get('website', '') or '').strip()
                    if website:
                        # Extract domain name from website
                        name = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
                if not name:
                    email = (lead.get('email', '') or '').strip()
                    if email and '@' in email:
                        # Extract email prefix as name
                        name = email.split('@')[0].replace('.', ' ').title()
                
                email = (lead.get('email', '') or '').strip()
                phone = (lead.get('phone', '') or '').strip() if lead.get('phone') else None
                company = (lead.get('company', '') or '').strip() if lead.get('company') else None
                
                lead_data = {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'company': company,
                    'location': location_val if location_val else None,
                    'status': 'new',
                    'trust_score': 0,
                    'source': 'web_extract'
                }
                
                print(f"[SAVE-LEADS] [{i+1}/{len(leads)}] Cleaned data: name='{name}', email='{email}', company='{company}'")
                
                # Validate required fields
                validation_errors = []
                if not name:
                    validation_errors.append("no name source available")
                if not email:
                    validation_errors.append("empty email")
                if email and '@' not in email:
                    validation_errors.append("invalid email format")
                
                if validation_errors:
                    error_msg = f"Lead #{i+1} ({name or 'NO NAME'}, {email or 'NO EMAIL'}): {', '.join(validation_errors)}"
                    print(f"[SAVE-LEADS]   ✗ Validation failed: {error_msg}")
                    failed_count += 1
                    errors.append(error_msg)
                    failed_leads.append({
                        'index': i+1,
                        'name': name or 'EMPTY',
                        'email': email or 'EMPTY',
                        'reason': ', '.join(validation_errors)
                    })
                    continue
                
                # Insert lead into database
                print(f"[SAVE-LEADS]   → Inserting: {name} ({email})")
                result = db.insert_lead(lead_data)
                
                if result:
                    saved_count += 1
                    print(f"[SAVE-LEADS]   ✓ Saved successfully")
                else:
                    failed_count += 1
                    error_msg = f"Lead #{i+1} ({name}, {email}): Database insertion failed (duplicate or constraint violation)"
                    print(f"[SAVE-LEADS]   ✗ {error_msg}")
                    errors.append(error_msg)
                    failed_leads.append({
                        'index': i+1,
                        'name': name,
                        'email': email,
                        'reason': 'Database insertion failed'
                    })
                    
            except Exception as e:
                error_msg = f"Lead #{i+1}: Exception - {str(e)}"
                print(f"[SAVE-LEADS]   ✗ {error_msg}")
                failed_count += 1
                errors.append(error_msg)
                failed_leads.append({
                    'index': i+1,
                    'name': lead.get('name', lead.get('company', lead.get('website', 'ERROR'))),
                    'email': lead.get('email', 'ERROR'),
                    'reason': str(e)
                })
                continue
        
        message = f"Saved {saved_count} leads"
        if failed_count > 0:
            message += f" ({failed_count} failed)"
        
        print(f"\n[SAVE-LEADS] ========== RESULT ==========")
        print(f"[SAVE-LEADS] Saved: {saved_count}, Failed: {failed_count}")
        
        if failed_leads:
            print(f"[SAVE-LEADS] Failed leads details:")
            for fl in failed_leads:
                print(f"[SAVE-LEADS]   - #{fl['index']}: {fl['name']} ({fl['email']}) - {fl['reason']}")
        
        print(f"[SAVE-LEADS] ==========================================\n")
        
        return jsonify({
            "message": message,
            "saved": saved_count,
            "failed": failed_count,
            "errors": errors if failed_count > 0 else [],
            "failed_leads": failed_leads if failed_count > 0 else []
        })
    except Exception as e:
        error_msg = f"Database save failed: {str(e)}"
        print(f"[SAVE-LEADS] ✗ {error_msg}")
        return jsonify({"error": error_msg}), 500


@api.route('/save-extracted-leads-no-validation', methods=['POST'])
def save_extracted_leads_no_validation():
    """Save extracted leads to database WITHOUT validation - saves all leads as-is"""
    data = request.json
    leads = data.get('leads')
    
    print(f"\n[SAVE-LEADS-NO-VAL] ========== SAVE REQUEST (NO VALIDATION) ==========")
    print(f"[SAVE-LEADS-NO-VAL] Received request to save {len(leads) if leads else 0} leads (without validation)")
    
    if not leads or not isinstance(leads, list):
        print(f"[SAVE-LEADS-NO-VAL] ✗ Invalid leads format")
        return jsonify({"error": "Missing or invalid leads"}), 400
    
    try:
        saved_count = 0
        failed_count = 0
        errors = []
        
        for i, lead in enumerate(leads):
            try:
                # Use lead data as-is, with minimal cleaning
                location_val = (lead.get('location', '') or lead.get('position', '')).strip()
                
                lead_data = {
                    'name': (lead.get('name', '') or 'Unknown').strip() or 'Unknown',
                    'email': (lead.get('email', '') or 'noemail@unknown.com').strip() or 'noemail@unknown.com',
                    'phone': (lead.get('phone', '') or '').strip() or None,
                    'company': (lead.get('company', '') or '').strip() or None,
                    'location': location_val or None,
                    'status': 'new',
                    'trust_score': 0,
                    'source': 'web_extract'
                }
                
                print(f"[SAVE-LEADS-NO-VAL] [{i+1}/{len(leads)}] Inserting: {lead_data['name']} ({lead_data['email']})")
                
                # Insert lead into database (no strict validation)
                result = db.insert_lead(lead_data)
                
                if result:
                    saved_count += 1
                    print(f"[SAVE-LEADS-NO-VAL]   ✓ Saved")
                else:
                    failed_count += 1
                    error_msg = f"Lead #{i+1}: Database constraint violation (likely duplicate)"
                    print(f"[SAVE-LEADS-NO-VAL]   ✗ {error_msg}")
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Lead #{i+1}: {str(e)}"
                print(f"[SAVE-LEADS-NO-VAL]   ✗ {error_msg}")
                failed_count += 1
                errors.append(error_msg)
                continue
        
        message = f"Saved {saved_count} leads (no validation)"
        if failed_count > 0:
            message += f" ({failed_count} failed)"
        
        print(f"\n[SAVE-LEADS-NO-VAL] ========== RESULT ==========")
        print(f"[SAVE-LEADS-NO-VAL] Saved: {saved_count}, Failed: {failed_count}")
        print(f"[SAVE-LEADS-NO-VAL] ==========================================\n")
        
        return jsonify({
            "message": message,
            "saved": saved_count,
            "failed": failed_count,
            "errors": errors if failed_count > 0 else []
        })
    except Exception as e:
        error_msg = f"Database save failed: {str(e)}"
        print(f"[SAVE-LEADS-NO-VAL] ✗ {error_msg}")
        return jsonify({"error": error_msg}), 500
        print(f"[SAVE-LEADS] Message: {message}\n")
        
        return jsonify({
            "message": message,
            "saved": saved_count,
            "failed": failed_count,
            "errors": errors if failed_count > 0 else []
        })
    except Exception as e:
        error_msg = f"Database save failed: {str(e)}"
        print(f"[SAVE-LEADS] ✗ {error_msg}")
        return jsonify({"error": error_msg}), 500


# ============= Domain Search Routes =============
@api.route('/search-domain', methods=['POST'])
def search_domain():
    """Search for emails in a domain using Snov.io
    
    Request body:
    {
        "domain": "example.com"  // or "https://example.com"
    }
    
    Response:
    {
        "success": true,
        "domain": "example.com",
        "leads_found": 5,
        "leads": [
            {
                "email": "john@example.com",
                "name": "John Smith",
                "position": "CTO",
                "company": "example.com",
                "source": "Snov.io"
            }
        ]
    }
    """
    try:
        data = request.json
        domain = data.get('domain', '').strip()
        
        if not domain:
            return jsonify({"error": "Missing domain parameter"}), 400
        
        print(f"\n🔍 API: Domain search request for: {domain}")
        
        leads = search_snov_domain(domain)
        
        # leads is now always a list (empty or with items)
        return jsonify({
            "success": True,
            "domain": domain,
            "leads_found": len(leads),
            "leads": leads,
            "message": f"Found {len(leads)} emails in {domain}" if leads else f"No emails found for {domain}. This might mean: 1) No emails indexed by Snov, 2) API rate limit, 3) Credentials issue. Check logs for details."
        })
    except Exception as e:
        print(f"❌ Domain search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Domain search failed. Check backend logs for details."
        }), 500


# ============= Verification Routes =============
@api.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email address with multiple validation methods
    
    Request JSON:
    {
        "email": "john@example.com"
    }
    
    Response:
    {
        "valid": true,
        "email": "john@example.com",
        "reason": "Valid domain with MX records",
        "method": "mx_check",
        "details": "Detailed verification information"
    }
    """
    try:
        data = request.json
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({
                "error": "Missing email parameter",
                "valid": False
            }), 400
        
        print(f"\n📨 Email verification request: {email}")
        result = verify_email_rapid(email)
        
        if not result:
            return jsonify({
                "error": "Verification failed",
                "valid": False,
                "email": email
            }), 500
        
        # Ensure response has required fields
        response = {
            "valid": result.get('valid', False),
            "email": result.get('email', email),
            "reason": result.get('reason', 'Unknown'),
            "method": result.get('method', 'unknown'),
        }
        
        # Include additional details if available
        if 'details' in result:
            response['details'] = result['details']
        if 'mx_records' in result:
            response['mx_records'] = result['mx_records']
        if 'warning' in result:
            response['warning'] = result['warning']
        if 'full_response' in result:
            response['full_response'] = result['full_response']
        
        status_code = 200 if result.get('valid') else 200  # Return 200 for both valid/invalid
        return jsonify(response), status_code
        
    except Exception as e:
        print(f"❌ Error in email verification: {e}")
        return jsonify({
            "error": str(e),
            "valid": False
        }), 500


# ============= Upload Routes =============
@api.route('/upload-leads', methods=['POST'])
def upload_leads():
    """Upload leads from CSV/Excel file"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Save file temporarily
    file_path = f"/tmp/{file.filename}"
    file.save(file_path)
    
    # Ingest leads from file
    result = agent_ingest_leads(file_path)
    
    return jsonify(result)


# ============= Analytics Routes =============
@api.route('/dashboard-stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics"""
    stats = {
        "total": 0,
        "analyzed": 0,
        "outreach_sent": 0,
        "converted": 0
    }
    
    # TODO: Fetch stats from database
    
    return jsonify(stats)


@api.route('/leads', methods=['GET', 'POST'])
def manage_leads():
    """Get all leads (GET) or add a new lead (POST)"""
    
    # Handle POST - Add a new lead manually
    if request.method == 'POST':
        try:
            data = request.json
            
            # Validate required fields
            if not data.get('name') or not data.get('name').strip():
                return jsonify({"error": "Name is required"}), 400
            
            if not data.get('email') or not data.get('email').strip():
                return jsonify({"error": "Email is required"}), 400
            
            # Validate email format
            email = data.get('email', '').strip()
            if '@' not in email:
                return jsonify({"error": "Invalid email format"}), 400
            
            # Prepare lead data
            lead_data = {
                'name': data.get('name', '').strip(),
                'email': email,
                'phone': data.get('phone', '').strip() if data.get('phone') else None,
                'company': data.get('company', '').strip() if data.get('company') else None,
                'location': data.get('location', '').strip() if data.get('location') else None,
                'status': data.get('status', 'new'),
                'trust_score': int(data.get('trust_score', 0)),
                'source': 'manual'  # Mark as manually added
            }
            
            # Insert lead
            result = db.insert_lead(lead_data)
            
            if result:
                return jsonify({
                    "success": True,
                    "message": f"Lead '{lead_data['name']}' added successfully!"
                }), 201
            else:
                return jsonify({
                    "error": "Failed to add lead. Please check for duplicates or try again."
                }), 400
                
        except Exception as e:
            print(f"Error adding manual lead: {e}")
            return jsonify({"error": f"Failed to add lead: {str(e)}"}), 500
    
    # Handle GET - Retrieve all leads with filtering and pagination
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', None)
        search = request.args.get('search', None)
        
        conn = db.get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM leads WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if search:
            query += " AND (name LIKE %s OR email LIKE %s OR company LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # Count total
        count_query = "SELECT COUNT(*) FROM leads WHERE 1=1"
        count_params = []
        
        if status:
            count_query += " AND status = %s"
            count_params.append(status)
        
        if search:
            count_query += " AND (name LIKE %s OR email LIKE %s OR company LIKE %s)"
            search_param = f"%{search}%"
            count_params.extend([search_param, search_param, search_param])
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        # Pagination
        offset = (page - 1) * per_page
        query += f" ORDER BY created_at DESC LIMIT {per_page} OFFSET {offset}"
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        leads = []
        
        for row in cursor.fetchall():
            lead_dict = dict(zip(columns, row))
            # Convert datetime objects to strings
            for key, value in lead_dict.items():
                if hasattr(value, 'isoformat'):
                    lead_dict[key] = value.isoformat()
            leads.append(lead_dict)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "leads": leads,
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        })
    except Exception as e:
        print(f"Error fetching leads: {e}")
        return jsonify({"error": str(e)}), 500


@api.route('/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    """Get single lead details"""
    try:
        conn = db.get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
        
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not row:
            return jsonify({"error": "Lead not found"}), 404
        
        lead = dict(zip(columns, row))
        # Convert datetime objects to strings
        for key, value in lead.items():
            if hasattr(value, 'isoformat'):
                lead[key] = value.isoformat()
        
        return jsonify(lead)
    except Exception as e:
        print(f"Error fetching lead: {e}")
        return jsonify({"error": str(e)}), 500


# ============= Export Routes =============
@api.route('/export-sheets', methods=['POST'])
def export_sheets():
    """Export leads to Google Sheets"""
    data = request.json
    leads = data.get('leads', [])
    sheet_id = data.get('sheet_id')
    sheet_name = data.get('sheet_name', 'Leads')
    
    if not sheet_id:
        return jsonify({"error": "Missing sheet_id"}), 400
    
    success = export_to_google_sheets(leads, sheet_id, sheet_name)
    
    if success:
        return jsonify({"message": "Successfully exported to Google Sheets"})
    else:
        return jsonify({"error": "Failed to export"}), 500


# ============= Settings Routes =============
@api.route('/settings', methods=['GET'])
def get_settings():
    """Get user settings"""
    # TODO: Fetch from database
    return jsonify({
        "autopilot": False,
        "email_template": "",
        "api_keys": {}
    })


@api.route('/settings', methods=['POST'])
def update_settings():
    """Update user settings"""
    data = request.json
    
    # TODO: Save to database
    
    return jsonify({"message": "Settings updated"})


# ============= OUTREACH ROUTES =============

@api.route('/generate-outreach-message', methods=['POST'])
def generate_outreach_message():
    """Generate a personalized outreach message for a single lead
    
    Request body:
    {
        "lead": {
            "name": "John Doe",
            "company": "Acme Inc",
            "email": "john@acme.com",
            "position": "CTO",
            "industry": "SaaS",
            "pain_points": "Scaling infrastructure"
        },
        "tone": "professional",  // professional, casual, urgent, friendly
        "template": "email",     // email, linkedin, whatsapp, default
        "ai_service": "gemini"   // gemini or groq (optional, default: gemini)
    }
    """
    try:
        data = request.json
        lead = data.get('lead')
        tone = data.get('tone', 'professional')
        template = data.get('template', 'email')
        ai_service = data.get('ai_service', 'gemini')
        
        if not lead or not lead.get('name'):
            return jsonify({"error": "Missing lead information"}), 400
        
        result = agent_generate_outreach_message(lead, tone=tone, template=template, ai_service=ai_service)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route('/generate-campaign-strategy', methods=['POST'])
def generate_campaign_strategy():
    """Generate a campaign strategy for outreach
    
    Request body:
    {
        "leads_count": 50,
        "industry": "SaaS",
        "objective": "Schedule demos",
        "ai_service": "gemini"  // gemini or groq (optional, default: gemini)
    }
    """
    try:
        data = request.json
        leads_count = data.get('leads_count', 10)
        industry = data.get('industry', 'General')
        objective = data.get('objective', 'Generate qualified leads')
        ai_service = data.get('ai_service', 'gemini')
        
        result = agent_generate_campaign_strategy(leads_count, industry, objective, ai_service=ai_service)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route('/create-campaign', methods=['POST'])
def create_campaign():
    """Create a complete outreach campaign with personalized messages
    
    Request body:
    {
        "campaign_name": "Q1 2024 SaaS Outreach",
        "leads": [
            {
                "name": "John Doe",
                "email": "john@acme.com",
                "company": "Acme Inc",
                "position": "CTO",
                "industry": "SaaS",
                "pain_points": "Scaling infrastructure"
            },
            ...
        ],
        "tone": "professional",
        "template": "email"
    }
    """
    try:
        data = request.json
        campaign_name = data.get('campaign_name')
        leads = data.get('leads', [])
        tone = data.get('tone', 'professional')
        template = data.get('template', 'email')
        
        if not campaign_name or not leads:
            return jsonify({"error": "Missing campaign_name or leads"}), 400
        
        if not isinstance(leads, list) or len(leads) == 0:
            return jsonify({"error": "Leads must be a non-empty array"}), 400
        
        result = create_outreach_campaign(campaign_name, leads, tone=tone, template=template)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route('/send-bulk-outreach', methods=['POST'])
def send_bulk_outreach():
    """Send bulk outreach emails to multiple leads
    
    Request body:
    {
        "campaign_id": "campaign_123",
        "leads": [...],
        "messages": [...]
    }
    """
    try:
        data = request.json
        campaign_id = data.get('campaign_id')
        leads = data.get('leads', [])
        messages = data.get('messages', [])
        
        if not campaign_id:
            return jsonify({"error": "Missing campaign_id"}), 400
        
        result = send_bulk_outreach_emails(campaign_id, leads, messages)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route('/log-outreach', methods=['POST'])
def log_outreach():
    """Log an outreach attempt
    
    Request body:
    {
        "lead_id": 123,
        "campaign_id": "campaign_123",
        "message_content": "Hey John...",
        "channel": "email",  // email, linkedin, whatsapp
        "status": "sent"     // sent, failed, bounced
    }
    """
    try:
        data = request.json
        lead_id = data.get('lead_id')
        campaign_id = data.get('campaign_id')
        message_content = data.get('message_content')
        channel = data.get('channel', 'email')
        status = data.get('status', 'sent')
        
        if not lead_id or not campaign_id:
            return jsonify({"error": "Missing lead_id or campaign_id"}), 400
        
        success = log_outreach_attempt(lead_id, campaign_id, message_content, channel, status)
        
        return jsonify({
            "success": success,
            "message": "Outreach logged successfully" if success else "Failed to log outreach"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route('/track-response', methods=['POST'])
def track_response():
    """Track a response to outreach
    
    Request body:
    {
        "lead_id": 123,
        "campaign_id": "campaign_123",
        "response_type": "opened"  // opened, clicked, replied, unsubscribed
    }
    """
    try:
        data = request.json
        lead_id = data.get('lead_id')
        campaign_id = data.get('campaign_id')
        response_type = data.get('response_type', 'opened')
        
        if not lead_id or not campaign_id:
            return jsonify({"error": "Missing lead_id or campaign_id"}), 400
        
        result = track_outreach_response(lead_id, campaign_id, response_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route('/campaign-analytics/<campaign_id>', methods=['GET'])
def campaign_analytics(campaign_id):
    """Get analytics for a campaign
    
    URL: /api/campaign-analytics/campaign_123
    """
    try:
        if not campaign_id:
            return jsonify({"error": "Missing campaign_id"}), 400
        
        result = get_campaign_analytics(campaign_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route('/campaigns', methods=['GET'])
def get_campaigns():
    """Get all campaigns with statistics"""
    try:
        # TODO: Fetch from database
        campaigns = []
        return jsonify({
            "campaigns": campaigns,
            "total": len(campaigns)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/campaigns/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get details of a specific campaign"""
    try:
        # TODO: Fetch from database
        return jsonify({
            "error": "Campaign not found"
        }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/outreach-history', methods=['GET'])
def get_outreach_history():
    """Get history of all outreach attempts"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # TODO: Fetch from database with pagination
        history = []
        
        return jsonify({
            "history": history,
            "page": page,
            "per_page": per_page,
            "total": 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= SIMPLE OUTREACH (NO AI ANALYSIS REQUIRED) =============

@api.route('/send-outreach', methods=['POST'])
def send_outreach():
    """Send outreach message to a single lead without AI analysis
    
    Request body:
    {
        "lead_id": 1,
        "message": "Hi John, we have a solution for your company...",
        "subject": "Solution for Acme Inc",
        "message_type": "email"  // email, whatsapp, linkedin
    }
    """
    try:
        data = request.json
        lead_id = data.get('lead_id')
        message = data.get('message', '').strip()
        subject = data.get('subject', 'Interested in connecting').strip()
        message_type = data.get('message_type', 'email')
        
        if not lead_id:
            return jsonify({"error": "lead_id is required"}), 400
        
        if not message:
            return jsonify({"error": "message is required"}), 400
        
        # Get lead from database
        lead = db.get_lead_by_id(lead_id)
        if not lead:
            return jsonify({"error": "Lead not found"}), 404
        
        # Send email if message_type is email
        email_sent = False
        send_error = None
        if message_type == 'email':
            from helpers import send_email
            email_sent, send_error = send_email(
                to_email=lead['email'],
                subject=subject,
                body=message,
                lead_name=lead['name']
            )
        
        # Log outreach attempt
        db.log_outreach(lead_id, message_type, message)
        
        # Mark lead as outreach_sent
        import mysql.connector
        conn = db.get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE leads SET status = 'outreach_sent' WHERE id = %s", (lead_id,))
            conn.commit()
            cursor.close()
            conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Outreach sent to {lead['name']} ({lead['email']})",
            "lead_id": lead_id,
            "lead_name": lead['name'],
            "lead_email": lead['email'],
            "email_sent": email_sent,
            "email_error": send_error
        }), 201
        
    except Exception as e:
        print(f"Error sending outreach: {e}")
        return jsonify({"error": f"Failed to send outreach: {str(e)}"}), 500


@api.route('/bulk-outreach', methods=['POST'])
def bulk_outreach():
    """Send outreach to multiple leads without AI analysis
    
    Request body:
    {
        "lead_ids": [1, 2, 3, 4, 5],
        "message": "Hi {name}, we have a solution for {company}...",
        "subject": "Solution for {company}",
        "message_type": "email"  // email, whatsapp, linkedin
    }
    
    Message supports template variables:
    - {name}: Lead name
    - {company}: Company name
    - {email}: Email address
    """
    try:
        data = request.json
        lead_ids = data.get('lead_ids', [])
        message_template = data.get('message', '').strip()
        subject_template = data.get('subject', 'Interested in connecting').strip()
        message_type = data.get('message_type', 'email')
        
        if not lead_ids:
            return jsonify({"error": "lead_ids array is required"}), 400
        
        if not message_template:
            return jsonify({"error": "message is required"}), 400
        
        sent_count = 0
        failed_leads = []
        
        for lead_id in lead_ids:
            try:
                # Get lead
                lead = db.get_lead_by_id(lead_id)
                if not lead:
                    failed_leads.append({"lead_id": lead_id, "reason": "Lead not found"})
                    continue
                
                # Replace template variables
                message = message_template.format(
                    name=lead.get('name', 'there'),
                    company=lead.get('company', 'your company'),
                    email=lead.get('email', '')
                )
                subject = subject_template.format(
                    name=lead.get('name', ''),
                    company=lead.get('company', ''),
                    email=lead.get('email', '')
                )
                
                # Send email if message_type is email
                if message_type == 'email':
                    from helpers import send_email
                    email_sent, send_error = send_email(
                        to_email=lead['email'],
                        subject=subject,
                        body=message,
                        lead_name=lead['name']
                    )
                    if not email_sent:
                        print(f"[OUTREACH] Email failed for {lead['name']}: {send_error}")
                
                # Log outreach
                db.log_outreach(lead_id, message_type, message)
                
                # Update lead status
                import mysql.connector
                conn = db.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE leads SET status = 'outreach_sent' WHERE id = %s", (lead_id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                
                sent_count += 1
                print(f"[OUTREACH] Sent message to {lead['name']} ({lead['email']})")
                
            except Exception as e:
                print(f"[OUTREACH] Error sending to lead {lead_id}: {e}")
                failed_leads.append({"lead_id": lead_id, "reason": str(e)})
        
        return jsonify({
            "success": True,
            "sent_count": sent_count,
            "failed_count": len(failed_leads),
            "total": len(lead_ids),
            "message": f"Sent {sent_count} outreach messages ({len(failed_leads)} failed)",
            "failed_leads": failed_leads
        }), 200
        
    except Exception as e:
        print(f"Error in bulk outreach: {e}")
        return jsonify({"error": f"Bulk outreach failed: {str(e)}"}), 500


@api.route('/outreach-templates', methods=['GET'])
def get_outreach_templates():
    """Get pre-built professional outreach message templates"""
    templates = {
        "executive_intro": {
            "name": "Executive Introduction - Value Focus",
            "subject": "Quick insight for {company}'s growth strategy",
            "message": "Hi {name},\n\nI've been following {company}'s recent growth trajectory, and I believe there's a significant opportunity we should discuss.\n\nOur work with similar companies in your industry has helped them achieve a 40% improvement in operational efficiency. Given {company}'s strategic position, I think you'd find the insights valuable.\n\nWould you have 20 minutes this week for a brief conversation?\n\nBest regards"
        },
        "problem_aware": {
            "name": "Problem-Aware Approach",
            "subject": "{company} - Addressing key challenges in your industry",
            "message": "Hi {name},\n\nCompanies like {company} often face challenges with resource optimization and market positioning. We specialize in solving these exact issues.\n\nOur proprietary framework has helped industry leaders like yourself reduce costs while improving output quality. I'd love to share a relevant case study.\n\nCould we schedule 15 minutes next week?\n\nBest regards"
        },
        "personalized_research": {
            "name": "Personalized Research Deep-Dive",
            "subject": "Opportunity aligned with {company}'s objectives",
            "message": "Hi {name},\n\nAfter researching {company}'s recent announcements and market position, I identified a specific opportunity that aligns perfectly with your growth goals.\n\nSpecifically, we help companies like yours in [industry] generate qualified leads at 3x the current rate while reducing acquisition costs by 50%.\n\nI'd like to share our findings and see if this is relevant for your team. Are you open to a quick call?\n\nBest regards"
        },
        "scarcity_urgency": {
            "name": "Limited-Time Opportunity",
            "subject": "Exclusive offer for {company} - This week only",
            "message": "Hi {name},\n\nWe're launching a limited beta program with only 5 spots available for companies in your sector.\n\nBased on {company}'s profile and growth stage, you'd be an ideal fit. The program includes:\n• Complimentary strategy consultation\n• Competitive analysis against peers\n• Custom roadmap aligned with your goals\n\nSpots fill quickly. Are you available for a brief conversation this week?\n\nBest regards"
        },
        "social_proof": {
            "name": "Social Proof & Case Study",
            "subject": "How companies like {company} are achieving 3x results",
            "message": "Hi {name},\n\nI wanted to share something that might be valuable for your team at {company}.\n\nWe recently helped a company with a similar profile increase their market reach by 3x in 6 months. The strategy is straightforward and applicable across your industry.\n\nI've attached a brief case study. If it resonates, I'd be happy to discuss how this could work for {company}.\n\nWould you be open to a short call?\n\nBest regards"
        },
        "referral_based": {
            "name": "Warm Referral Introduction",
            "subject": "Introduced by [Referral Name] - Quick opportunity",
            "message": "Hi {name},\n\n[Referral Name] recently suggested I reach out to you at {company}. They mentioned you're driving strategic initiatives around growth and efficiency.\n\nGiven your focus, I think there's a relevant conversation to be had. We help companies scale revenue while maintaining quality, and I've got proven solutions in your space.\n\nWould you be open to a brief 15-minute call to explore?\n\nBest regards"
        },
        "milestone_triggered": {
            "name": "Milestone-Based Opportunity",
            "subject": "Congrats on {company}'s recent milestone - Quick opportunity inside",
            "message": "Hi {name},\n\nCongratulations on {company}'s recent expansion! That's fantastic news.\n\nWith growth comes new scaling challenges. Many companies in your position are currently focused on operational efficiency and market expansion. We specialize in helping organizations like yours navigate this transition successfully.\n\nI'd love to share insights from companies we've worked with through similar growth phases.\n\nCould we grab 20 minutes this week?\n\nBest regards"
        },
        "question_based": {
            "name": "Question-Based Curiosity",
            "subject": "Question about {company}'s approach to [topic]",
            "message": "Hi {name},\n\nI've been researching how companies in {company}'s space approach [specific challenge], and I noticed some interesting patterns.\n\nI'm curious about your perspective - how is {company} currently handling [challenge]? \n\nI might have some benchmark data and insights that could be valuable for your strategy.\n\nWould you have 15 minutes for a quick conversation?\n\nBest regards"
        },
        "value_stack": {
            "name": "Value Stacking Approach",
            "subject": "{company} - Multiple ways we can help",
            "message": "Hi {name},\n\nI see several opportunities where we can immediately add value to {company}:\n\n1. Revenue acceleration - Proven to increase qualified pipeline by 2.5x\n2. Cost optimization - On average, 35-40% reduction in customer acquisition costs\n3. Market positioning - Strategic insights to differentiate from competitors\n\nEach of these is worth exploring individually, but the combination creates significant competitive advantage.\n\nWould a brief conversation make sense?\n\nBest regards"
        },
        "exclusive_access": {
            "name": "Exclusive Access / VIP Treatment",
            "subject": "{company} - Exclusive access to our new platform",
            "message": "Hi {name},\n\nWe're offering exclusive early access to [new feature/platform] for a select group of industry leaders.\n\nBased on {company}'s profile and market position, I'd like to personally invite you to be part of this exclusive group.\n\nBenefits include:\n• Priority support and custom implementation\n• Direct access to our executive team\n• Competitive advantage before public launch\n\nI'd love to discuss this with you. Are you available for a brief call?\n\nBest regards"
        },
        "educational_value": {
            "name": "Educational / Thought Leadership",
            "subject": "Industry insights for {company}'s leadership team",
            "message": "Hi {name},\n\nI've put together a research report on emerging trends in [industry] that's generating significant interest among forward-thinking leaders.\n\nGiven {company}'s position and vision, I think your leadership team would find it invaluable. It includes:\n• Market forecasts for 2025-2027\n• Competitive positioning analysis\n• Strategic recommendations for your segment\n\nI'd like to share this with you personally and discuss implications for {company}.\n\nWould you be open to that?\n\nBest regards"
        },
        "roi_focused": {
            "name": "ROI-Focused Pitch",
            "subject": "How {company} can achieve 5x ROI this year",
            "message": "Hi {name},\n\nWe've developed a model showing how companies like {company} can achieve 5x return on marketing investment within 12 months.\n\nThe strategy involves three key components, all of which are within {company}'s capability to implement. I've worked with [similar company] through this exact process.\n\nThe potential upside for {company} is substantial. Are you interested in exploring this?\n\nBest regards"
        },
        "challenge_based": {
            "name": "Challenge-Focused Inquiry",
            "subject": "Solving [specific challenge] for {company}",
            "message": "Hi {name},\n\nMost companies in {company}'s space struggle with [specific challenge]. It's one of the top 3 issues keeping executives awake at night.\n\nWe've developed a proven framework to address this, and we've documented the results with companies like yours.\n\nSpecifically, we help reduce [metric] by 45% while improving [outcome] by 60%.\n\nWould it make sense to discuss how this could work for {company}?\n\nBest regards"
        }
    }
    
    return jsonify({"templates": templates})


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
        
        cursor = conn.cursor(dictionary=True)
        
        # Build query
        query = "SELECT id, name, email, company, phone, status, trust_score FROM leads WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if min_trust > 0:
            query += " AND trust_score >= %s"
            params.append(min_trust)
        
        query += f" ORDER BY created_at DESC LIMIT {limit}"
        
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
