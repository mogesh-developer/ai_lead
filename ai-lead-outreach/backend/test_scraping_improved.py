import sys
import os
sys.path.append(r'c:\Users\Code_redx.exe\Downloads\AI AGENTS\ai-lead-outreach\backend')

from app import extract_contact_info, extract_contacts_from_text

# Test the scraping functions
test_urls = [
    "https://www.justdial.com/Chennai/Computer-Repair-Services/nct-101928",
    "https://www.yellowpages.com/search?search_terms=plumbers&geo_location_terms=Los%20Angeles%2C%20CA",
    "https://www.example.com"  # This might not work but let's test
]

print("Testing contact extraction functions...")
print("=" * 60)

# Test extract_contacts_from_text with sample text
sample_text = """
Contact us at:
Email: info@techcorp.com
Phone: +91 9876543210
Address: 123 Tech Street, Chennai, Tamil Nadu 600001

Call us: (555) 123-4567
Or email: support@techcorp.com

Our office is located at:
456 Business Avenue, Suite 200
Bangalore, Karnataka 560001

Phone: +1 234 567 8901
"""

print("1. Testing extract_contacts_from_text with sample text:")
emails, phones, addresses = extract_contacts_from_text(sample_text)
print(f"   Emails found: {emails}")
print(f"   Phones found: {phones}")
print(f"   Addresses found: {addresses}")
print()

# Test extract_contact_info with a real URL (if possible)
print("2. Testing extract_contact_info with URLs:")
for url in test_urls[:1]:  # Test only first URL to avoid rate limits
    try:
        print(f"   Testing URL: {url}")
        emails, phones, addresses = extract_contact_info(url)
        print(f"   Emails: {emails}")
        print(f"   Phones: {phones}")
        print(f"   Addresses: {addresses}")
        print()
    except Exception as e:
        print(f"   Error testing {url}: {e}")
        print()

print("Testing completed!")