import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print("API KEY length:", len(api_key) if api_key else 0)

client = genai.Client(api_key=api_key)

try:
    print("Testing gemini-3.6-flash...")
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="Hola"
    )
    print("Success 3.6-flash:", response.text[:40])
except Exception as e:
    print(f"Error 3.6-flash: {e}")
