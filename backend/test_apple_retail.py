import requests
import json

# Test with a page that definitely has phone numbers
url = 'https://www.apple.com/retail/'

print('Testing scraping with Apple retail page:', url)
try:
    response = requests.post('http://localhost:5000/api/scrape-url',
                            json={'url': url},
                            headers={'Content-Type': 'application/json'},
                            timeout=60)

    if response.status_code == 200:
        result = response.json()
        print('✅ Success!')
        print(f'Message: {result["message"]}')
        print(f'Found {len(result["leads"])} leads')
        for lead in result['leads']:
            print(f'  - Company: {lead["company"]}')
            print(f'    Email: {lead["email"] or "None"}')
            print(f'    Phone: {lead["phone"] or "None"}')
            print(f'    Location: {lead["location"] or "None"}')
            print()
    else:
        print('❌ Failed:', response.status_code, response.text)
except Exception as e:
    print('❌ Error:', e)