import requests

# Test manual lead addition with all fields
test_lead = {
    'name': 'Test User Full',
    'email': 'testfull@example.com',
    'phone': '123-456-7890',
    'company': 'Test Company Inc',
    'location': 'Test City, State',
    'status': 'analyzed',
    'trust_score': 85
}

try:
    response = requests.post('http://localhost:5000/api/leads', json=test_lead, timeout=10)
    print('Status:', response.status_code)
    print('Response:', response.json())
except Exception as e:
    print('Error:', e)