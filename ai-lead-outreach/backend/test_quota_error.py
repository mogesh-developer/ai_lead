import os
import sys
sys.path.append('.')

# Temporarily override the API key to test quota handling
original_groq_key = os.environ.get('GROQ_API_KEY')
os.environ['GROQ_API_KEY'] = 'invalid_key_for_testing'

from app import agent_analyze_business

# Test with a lead
lead = {'name': 'Test', 'company': 'Tech Corp', 'location': 'Chennai'}

print('Testing AI analysis with invalid API key (simulating quota/error)...')
result = agent_analyze_business(lead)
print('Result:', result)
print('Has error key:', 'error' in result)
if 'error' in result:
    print('Error message:', result['error'])

# Restore original key
if original_groq_key:
    os.environ['GROQ_API_KEY'] = original_groq_key