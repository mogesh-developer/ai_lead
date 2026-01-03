import db

leads = db.get_all_leads()
print(f'Found {len(leads)} leads in database')
for lead in leads[:5]:  # Show first 5 leads
    print(f'ID: {lead["id"]}, Company: {lead.get("company", "N/A")}, Email: {lead["email"]}, Status: {lead.get("status", "unknown")}')