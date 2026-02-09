import os
from dotenv import load_dotenv
from google import genai

# 1. Load your secret key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 2. Initialize the 2026 Client
# The new SDK automatically picks up the 'v1' stable API
client = genai.Client(api_key=api_key)

# 3. Use a 2026 model (gemini-2.5-flash is currently the most stable for robotics)
# If you specifically want Pro, use 'gemini-2.0-pro'
MODEL_ID = "gemini-2.5-flash" 

print(f"🧠 Sending pulse check to Gemini using {MODEL_ID}...")

try:
    response = client.models.generate_content(
        model=MODEL_ID, 
        contents="You are the QNMS Orchestrator. Provide one sample 2nm defect coordinate in JSON format: {x, y, z}."
    )
    print("\n✅ Connection Successful!")
    print("--- Gemini's Response ---")
    print(response.text)
except Exception as e:
    print(f"\n❌ Connection Failed: {e}")