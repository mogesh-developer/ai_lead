import sys
sys.path.append('.')
from helpers import send_email

# Test direct email sending
success, error = send_email('mogeshwaran09@gmail.com', 'Direct Test', 'This is a direct email test')
if success:
    print('✅ Direct email test successful!')
else:
    print(f'❌ Direct email test failed: {error}')