import requests
import json

# Test with different URLs
test_urls = [
    'https://www.justdial.com/Chennai/Nursery-Gardens/nct-10263637',
    'https://www.yellowpages.com/search?search_terms=nursery&geo_location_terms=chennai',
    'https://www.google.com/search?q=nursery+gardens+in+chennai',
    'https://www.indiamart.com/search.html?keyword=nursery+plants'
]

for url in test_urls:
    print(f'\n🔍 Testing: {url}')
    try:
        response = requests.post('http://localhost:5000/api/scrape-url',
                                json={'url': url},
                                headers={'Content-Type': 'application/json'},
                                timeout=30)

        if response.status_code == 200:
            result = response.json()
            print(f'✅ Success! Found {len(result["leads"])} leads')
            if result["leads"]:
                for lead in result['leads'][:2]:  # Show first 2 leads
                    print(f'  - {lead["company"]}: {lead["phone"] or "No phone"}')
        else:
            print(f'❌ Failed: {response.status_code} - {response.text}')
    except requests.exceptions.Timeout:
        print('⏰ Timeout after 30 seconds')
    except Exception as e:
        print(f'❌ Error: {e}')