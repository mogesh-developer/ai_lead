#!/usr/bin/env python3
"""Test web search extraction and saving"""

import os
import sys
import json
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

from agents import agent_ai_clean_search_results
from routes import save_extracted_leads
from flask import Flask

def test_web_search_save():
    """Test the full web search -> extract -> save flow"""

    print("🔍 TESTING WEB SEARCH EXTRACTION AND SAVING")
    print("=" * 60)

    # Simulate search results (like what would come from SerpAPI)
    mock_search_results = [
        {
            'title': 'Ellen Crichton - Professional Profile',
            'href': 'https://example.com/ellen-crichton',
            'body': 'Ellen Crichton is a marketing specialist at TechCorp Inc. Contact: ellencrichton11@gmail.com, Phone: +1-555-0123, Location: New York, NY'
        },
        {
            'title': 'Nila Elite Solutions',
            'href': 'https://nilaelite.com',
            'body': 'Nila Elite provides software solutions. Email: nilaelite@gmail.com, Phone: +1-555-0456, Based in San Francisco, CA'
        }
    ]

    print(f"Mock search results: {len(mock_search_results)} items")

    # Step 1: AI Clean the search results
    print("\n🤖 Step 1: AI Cleaning search results...")
    cleaned_leads = agent_ai_clean_search_results(mock_search_results, ai_service="gemini")

    if isinstance(cleaned_leads, dict) and "error" in cleaned_leads:
        print(f"❌ AI Cleaning failed: {cleaned_leads['error']}")
        return

    print(f"✅ AI extracted {len(cleaned_leads)} leads:")
    for i, lead in enumerate(cleaned_leads):
        print(f"  {i+1}. {json.dumps(lead, indent=2)}")

    # Step 2: Save the leads (simulate the API call)
    print("\n💾 Step 2: Saving leads to database...")

    app = Flask(__name__)

    with app.test_request_context(
        '/api/save-extracted-leads',
        method='POST',
        json={'leads': cleaned_leads}
    ):
        response = save_extracted_leads()
        result = response.get_json()
        print(f"Save result: {json.dumps(result, indent=2)}")

    # Step 3: Check what was actually saved
    print("\n📊 Step 3: Checking database contents...")
    import db
    conn = db.get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, company, website, phone, location, confidence FROM leads ORDER BY id DESC LIMIT 5")
        recent_leads = cursor.fetchall()
        cursor.close()
        conn.close()

        print("Recent leads in database:")
        for lead in recent_leads:
            print(f"  ID {lead['id']}: {lead.get('company', 'Unknown')} <{lead['email']}>")
            print(f"    Company: {lead.get('company', 'NULL')}")
            print(f"    Website: {lead.get('website', 'NULL')}")
            print(f"    Phone: {lead.get('phone', 'NULL')}")
            print(f"    Location: {lead.get('location', 'NULL')}")
            print(f"    Confidence: {lead.get('confidence', 'NULL')}")

if __name__ == "__main__":
    test_web_search_save()