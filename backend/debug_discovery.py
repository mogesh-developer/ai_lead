import sys
import os
sys.path.append(r'c:\Users\Code_redx.exe\Downloads\AI AGENTS\ai-lead-outreach\backend')

from app import agent_discovery, extract_contact_info, search_the_web

print("Testing Lead Discovery...")
print("=" * 50)

industry = "digital marketing"
location = "chennai"
query = f"{industry} companies in {location} contact email"

print(f"Query: {query}")

try:
    print("1. Testing Web Search...")
    results = search_the_web(query, max_results=5)
    print(f"Found {len(results)} results.")
    for i, r in enumerate(results):
        print(f"Result {i+1}: {r.get('title')} - {r.get('href')}")
    
    if results:
        print("\n2. Testing Scraping on first result...")
        test_url = results[0].get('href')
        print(f"Scraping: {test_url}")
        try:
            emails, phones, addresses, names = extract_contact_info(test_url)
            print(f"Emails: {emails}")
            print(f"Phones: {phones}")
            print(f"Addresses: {addresses}")
            print(f"Names: {names}")
        except Exception as e:
            print(f"Scraping failed: {e}")
    else:
        print("No results found to scrape.")

except Exception as e:
    print(f"Error: {e}")

print("\n3. Running full agent_discovery...")
leads = agent_discovery(industry, location)
print(f"Total leads found: {len(leads)}")
for lead in leads:
    print(f" - {lead['name']} ({lead['company']}): {lead['email']} / {lead['phone']}")
