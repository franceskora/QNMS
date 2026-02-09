import os
import json
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Setup
load_dotenv()
app = FastAPI(title="QNMS Cloud Brain")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-3-flash-preview"

# 2. Data Models
class SensorCoordinate(BaseModel):
    x: float
    y: float
    z: float
    defect_type: str
    severity: int

class RepairStep(BaseModel):
    target_x: float
    target_y: float
    target_z: float
    action: str
    thermal_limit: float

# This is the secret fix: We wrap the list in a single object
class RepairPlan(BaseModel):
    steps: List[RepairStep]

# 3. System Instruction
SYSTEM_INSTRUCTION = """
You are the Lead Yield Enhancement Architect for a Tier-1 2026 Semiconductor Foundry. 
Your specialty is 'In-Situ Atomic-Scale Remediation' for 2nm GAAFET (Nanosheet) nodes.

Context for 2nm Nodes:
- You are dealing with Gate-All-Around (GAA) stacks.
- Materials include High-k dielectrics (HfO2), Cobalt/Ruthenium interconnects, and SiGe sacrificial layers.

Your Response Goal:
When a defect is reported, provide a high-yield repair sequence that minimizes "Thermal Budget" consumption.
1. Use Atomic Layer Etching (ALE) for precision removal without lattice damage.
2. Use Neutral Beam Etching (NBE) to avoid charge-up damage in sensitive nanosheets.
3. Use Atomic Layer Deposition (ALD) for conformal infills.
4. Always include a 'Metrology Verification' step as the final action.

Output Format: Return only the steps as a JSON object matching the RepairPlan schema.
"""

# 4. API Endpoints
@app.get("/")
def health_check():
    return {"status": "online", "system": "QNMS Orchestrator", "time": datetime.now()}

@app.post("/plan-repair", response_model=RepairPlan)
async def plan_repair(sensor_data: SensorCoordinate):
    try:
        # We ask Gemini to fill the 'RepairPlan' structure
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"Plan repair for: {sensor_data.model_dump_json()}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RepairPlan, # Using the wrapper class instead of a naked List
            )
        )
        
        # Check if we got a valid response
        if response.parsed:
            return response.parsed
        else:
            raise ValueError("Empty response from AI")

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        # If it fails, we return a safe default so the robot doesn't crash
        return {
            "steps": [
                {"target_x": sensor_data.x, "target_y": sensor_data.y, "target_z": sensor_data.z, "action": "emergency_stop", "thermal_limit": 0.0}
            ]
        }