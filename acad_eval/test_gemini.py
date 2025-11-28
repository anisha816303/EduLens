import google.generativeai as genai
from app.core.config import GEMINI_API_KEY

print(f"API Key: {GEMINI_API_KEY[:20]}...")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini configured successfully!")
    
    # Test simple query
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Say 'Hello' if you can hear me")
    print(f"✅ Response: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
