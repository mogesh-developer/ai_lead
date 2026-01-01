"""
Lightweight backend server for testing save leads fix
Skips heavy imports (pandas, groq) and provides essential endpoints only
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
sys.path.insert(0, '.')

import db

# Create Flask app
app = Flask(__name__)
CORS(app)

# ============= Health Check =============
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


# ============= Save Extracted Leads with Validation =============
@app.route('/api/save-extracted-leads', methods=['POST'])
def save_extracted_leads():
    """Save extracted leads with strict validation"""
    data = request.json
    leads = data.get('leads', [])
    
    print("\n" + "[SAVE-LEADS] ========== SAVE REQUEST ==========")
    print(f"[SAVE-LEADS] Received request to save {len(leads)} leads")
    
    saved_count = 0
    failed_count = 0
    failed_leads = []
    errors = []
    
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
    
    print("\n[SAVE-LEADS] ========== RESULT ==========")
    print(f"[SAVE-LEADS] Saved: {saved_count}, Failed: {failed_count}")
    print(f"[SAVE-LEADS] Message: Saved {saved_count} leads ({failed_count} failed)\n")
    
    return jsonify({
        "saved": saved_count,
        "failed": failed_count,
        "message": f"Saved {saved_count} leads ({failed_count} failed)",
        "failed_leads": failed_leads,
        "errors": errors
    })


# ============= Get Leads =============
@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all leads with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get leads from database
    leads = db.get_leads(page=page, per_page=per_page)
    total = db.get_total_leads()
    
    return jsonify({
        "leads": leads,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    })


if __name__ == '__main__':
    print("Starting lightweight backend for testing...")
    app.run(debug=False, host='localhost', port=5000, use_reloader=False)
