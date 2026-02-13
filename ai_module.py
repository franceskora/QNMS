# Save this as: ai_module.py
import os
from dotenv import load_dotenv
from google import genai

# Load Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
MODEL_ID = "gemini-2.0-flash" 

def get_gemini_decision(freq_ghz, current_uA, temp_k):
    """
    Real-time Inference Function.
    Takes telemetry -> Returns Engineering Decision.
    """
    prompt = f"""
    SYSTEM: You are a Reliability Engineer for a 2nm Ring Oscillator.
    TELEMETRY:
    - Frequency: {freq_ghz:.3f} GHz (Target: >2.0 GHz)
    - Drive Current: {current_uA:.1f} uA
    - Temperature: {temp_k:.1f} K
    
    
    TASK: If Frequency < 2.5 GHz, recommend 'REPAIR'. 
    If Temp > 350K, recommend 'THROTTLE'.
    Otherwise, say 'NOMINAL'.
    
    RESPONSE FORMAT: Just the single word command.
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_ID, 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"AI_ERROR: {str(e)}"