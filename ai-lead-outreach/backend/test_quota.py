import os
import sys
sys.path.append('.')

from app import agent_analyze_business

# Test with a lead
lead = {'name': 'Test', 'company': 'Tech Corp', 'location': 'Chennai'}

print('Testing AI analysis with current API keys...')
result = agent_analyze_business(lead)
print('Result:', result)
print('Has error key:', 'error' in result)
print('Trust score:', result.get('trust_score', 'N/A'))