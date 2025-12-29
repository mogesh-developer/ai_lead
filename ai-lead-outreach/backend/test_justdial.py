import requests
import json

# Test with a JustDial nursery garden URL
url = 'https://www.justdial.com/Chennai/Nursery-Gardens/nct-10263637'

print('Testing scraping with JustDial nursery URL:', url)
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