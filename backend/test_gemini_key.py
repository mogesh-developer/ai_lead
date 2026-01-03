import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"Testing API Key: {api_key}")

try:
    genai.configure(api_key=api_key)
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello, are you working?")
    print(f"Response: {response.text}")
    print("✅ Gemini API is working!")
except Exception as e:
    print(f"❌ Gemini API failed: {e}")
