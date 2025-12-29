import requests
import json

# First, let's add a test lead
test_lead = {
    'name': 'Test User',
    'email': 'test@example.com',
    'phone': '1234567890',
    'company': 'Test Company',
    'location': 'Chennai'
}

print('Adding test lead...')
response = requests.post('http://localhost:5000/api/leads', json=test_lead, timeout=10)
print(f'Response status: {response.status_code}')
print(f'Response data: {response.json()}')
if response.status_code == 201:
    lead_data = response.json()
    if 'id' in lead_data:
        lead_id = lead_data['id']
        print(f'Lead added with ID: {lead_id}')
    else:
        print('No ID in response, trying to get last lead...')
        # Try to get the last added lead
        get_response = requests.get('http://localhost:5000/api/leads', timeout=10)
        if get_response.status_code == 200:
            leads = get_response.json()
            if leads:
                lead_id = leads[-1]['id']  # Get the last lead
                print(f'Using last lead ID: {lead_id}')
            else:
                print('No leads found')
                exit(1)
        else:
            print('Failed to get leads')
            exit(1)

    # Now analyze the lead
    print('Analyzing lead...')
    analyze_response = requests.post(f'http://localhost:5000/api/analyze/{lead_id}', json={}, timeout=10)
    if analyze_response.status_code == 200:
        analyze_data = analyze_response.json()
        print('Analysis successful!')
        print('Analysis result:', json.dumps(analyze_data, indent=2))

        # Check if the lead data was updated
        print('Fetching updated lead data...')
        get_response = requests.get(f'http://localhost:5000/api/leads/{lead_id}', timeout=10)
        if get_response.status_code == 200:
            lead = get_response.json()
            print('Updated lead data:')
            print(f'  Status: {lead.get("status")}')
            print(f'  Trust Score: {lead.get("trust_score")}')
            print(f'  AI Analysis: {lead.get("ai_analysis")}')
        else:
            print('Failed to fetch updated lead')
    else:
        print(f'Analysis failed: {analyze_response.status_code} - {analyze_response.text}')
else:
    print(f'Failed to add lead: {response.status_code} - {response.text}')