import requests
import json

# Test the improved scraping with a working URL
url = 'https://www.apple.com/contact/'

print('Testing improved scraping with:', url)
try:
    response = requests.post('http://localhost:5000/api/scrape-url',
                            json={'url': url},
                            headers={'Content-Type': 'application/json'})

    if response.status_code == 200:
        result = response.json()
        print('✅ Success!')
        print(f'Found {len(result["leads"])} leads')
        for lead in result['leads']:
            print(f'  - {lead["company"]}: {lead["email"]} / {lead["phone"]}')
    else:
        print('❌ Failed:', response.status_code, response.text)
except Exception as e:
    print('❌ Error:', e)