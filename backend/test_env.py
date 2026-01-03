import os
from dotenv import load_dotenv
load_dotenv()

print('Environment variables loaded:')
print(f'SMTP_EMAIL: {os.getenv("SMTP_EMAIL")}')
print(f'SMTP_PASSWORD: {bool(os.getenv("SMTP_PASSWORD"))}')
print(f'SMTP_SERVER: {os.getenv("SMTP_SERVER")}')
print(f'SMTP_PORT: {os.getenv("SMTP_PORT")}')

print('\nTesting config import:')
from config import SMTP_EMAIL, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
print(f'Config SMTP_EMAIL: {SMTP_EMAIL}')
print(f'Config SMTP_PASSWORD: {bool(SMTP_PASSWORD)}')
print(f'Config SMTP_SERVER: {SMTP_SERVER}')
print(f'Config SMTP_PORT: {SMTP_PORT}')