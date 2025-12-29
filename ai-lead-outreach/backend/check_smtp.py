import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SMTP_EMAIL = os.getenv('SMTP_EMAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

print('=== SMTP Configuration Check ===')
print(f'📧 Email: {SMTP_EMAIL}')
print(f'🔑 Password: {"*" * len(SMTP_PASSWORD) if SMTP_PASSWORD else "Not set"}')
print(f'📏 Password Length: {len(SMTP_PASSWORD) if SMTP_PASSWORD else 0} characters')
print()

if not SMTP_EMAIL or not SMTP_PASSWORD:
    print('❌ ERROR: SMTP credentials are missing!')
    print('Please add SMTP_EMAIL and SMTP_PASSWORD to your .env file.')
else:
    print('✅ Credentials are configured.')
    print()

    if len(SMTP_PASSWORD.replace(' ', '')) == 16:
        print('✅ Password appears to be a valid 16-character App Password.')
    else:
        print('⚠️  WARNING: Password should be a 16-character Gmail App Password.')
        print('   Current password length (without spaces):', len(SMTP_PASSWORD.replace(' ', '')))

print()
print('=== Gmail App Password Setup Instructions ===')
print('To generate a Gmail App Password:')
print('1. Go to https://myaccount.google.com/security')
print('2. Enable 2-Step Verification if not already enabled')
print('3. Go to "Security" > "App passwords"')
print('4. Select "Mail" and "Other (custom name)"')
print('5. Enter "AI Lead Outreach" as the custom name')
print('6. Copy the 16-character password (ignore spaces)')
print('7. Replace SMTP_PASSWORD in .env with this password')
print()
print('Example .env entry:')
print('SMTP_PASSWORD=abcd1234efgh5678')