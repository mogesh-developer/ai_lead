import requests
import json

# Test with specific nursery business pages instead of directories
test_urls = [
    'https://www.justdial.com/Chennai/Sai-Nursery/044PXX44-XX44-150318195509-K8K8_BZDET',
    'https://www.google.com/maps/place/Sai+Nursery/@13.0827,80.2707,15z',
    'https://www.facebook.com/pages/Sai-Nursery/123456789',  # This might not exist, just testing
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