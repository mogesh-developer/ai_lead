"""Configuration and initialization for AI Lead Outreach Backend"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys and Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
SNOV_CLIENT_ID = os.getenv("SNOV_CLIENT_ID")
SNOV_CLIENT_SECRET = os.getenv("SNOV_CLIENT_SECRET")

# Initialize AI Clients (lazy loaded to avoid import issues)
genai = None
groq_client = None

def get_genai():
    """Lazy load Gemini API"""
    global genai
    if genai is None and GEMINI_API_KEY:
        try:
            import google.generativeai as _genai
            _genai.configure(api_key=GEMINI_API_KEY)
            genai = _genai
            print("[OK] Gemini API configured")
        except Exception as e:
            print(f"[ERROR] Gemini configuration error: {e}")
    return genai

def get_groq():
    """Lazy load Groq API"""
    global groq_client
    if groq_client is None and GROQ_API_KEY:
        try:
            from groq import Groq
            groq_client = Groq(api_key=GROQ_API_KEY)
            print("[OK] Groq API configured")
        except Exception as e:
            print(f"[WARN] Groq initialization error: {e}")
    return groq_client

# Check configuration
print(f"[CONFIG] Configuration Status:")
print(f"   - GEMINI_API_KEY: {'OK' if GEMINI_API_KEY else 'MISSING'}")
print(f"   - GROQ_API_KEY: {'OK' if GROQ_API_KEY else 'MISSING'}")
print(f"   - SERPAPI_API_KEY: {'OK' if SERPAPI_API_KEY else 'MISSING'}")
print(f"   - SMTP_EMAIL: {'OK' if SMTP_EMAIL else 'MISSING'}")
print(f"   - SNOV Credentials: {'OK' if (SNOV_CLIENT_ID and SNOV_CLIENT_SECRET) else 'MISSING'}")

# Lazy-load Groq on first use
def get_groq_client():
    """Get Groq client, lazy-loading if needed"""
    global groq_client
    if groq_client is None and GROQ_API_KEY:
        try:
            from groq import Groq
            groq_client = Groq(api_key=GROQ_API_KEY)
        except Exception as e:
            print(f"Error initializing Groq: {e}")
            return None
    return groq_client

