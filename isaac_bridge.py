import requests
import time
import sqlite3 
import json
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

# --- CONFIGURATION ---
BREV_IP = "13.220.232.5"
PORT = 5000
BASE_URL = f"http://{BREV_IP}:{PORT}"

@dataclass
class WorldState:
    defect_density: float
    thermal_map: Dict[str, float]
    active_agents: int
    environment: str
    timestamp: float

class RobotAction(Enum):
    SCAN_SECTOR = "scan_sector"
    DEPLOY_AGENT = "deploy_nano_agent"
    ACTIVATE_COOLING = "activate_cooling"
    EMERGENCY_STOP = "emergency_stop"

@dataclass
class IsaacEvent:
    event_type: str
    severity: str
    payload: Dict[str, Any]
    timestamp: float = time.time()

# --- THE ENHANCED BRIDGE ---
class IsaacBridge:
    def __init__(self, db_path="isaac_persistence.db", simulation_mode=False): # FLIPPED TO FALSE
        self.db_path = db_path
        self.simulation_mode = simulation_mode
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    severity TEXT,
                    payload TEXT,
                    timestamp REAL
                )
            """)

    def log_event(self, event: IsaacEvent):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO event_log (event_type, severity, payload, timestamp) VALUES (?, ?, ?, ?)",
                (event.event_type, event.severity, str(event.payload), event.timestamp)
            )

    def get_world_state(self) -> WorldState:
        """Fetches live state from Brev or falls back to simulation."""
        if not self.simulation_mode:
            try:
                response = requests.get(f"{BASE_URL}/telemetry", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Grab the live array from Isaac Sim, default to 7 zeros if empty
                    live_joints = data.get('joint_positions', [0.0]*7)
                    # Convert to comma-separated string for the dashboard
                    joint_str = ", ".join([str(j) for j in live_joints])
                    
                    return WorldState(
                        defect_density=0.04, 
                        thermal_map={
                            "Core": data.get('temperature', 0),
                            "Joint_Data": joint_str  # <-- Sending live kinematics
                        },
                        active_agents=1,
                        environment=data.get('cosmos_environment', 'Unknown'),
                        timestamp=time.time()
                    )
            except Exception as e:
                print(f"⚠️ Connection to Brev failed, using fallback state.")

        # Fallback Simulation State
        # Fallback Simulation State
        return WorldState(
            defect_density=0.04,
            thermal_map={
                "Core_A": 45.2, 
                "SRAM_1": 38.9,
                "Joint_Data": "0.0, -0.78, 0.0, -2.35, 0.0, 1.57, 0.78" # <-- Default standby pose
            },
            active_agents=1,
            environment="Simulated_Environment",
            timestamp=time.time()
        )

    def send_command(self, action: RobotAction, params: Dict = None):
        """Sends physical command to Brev."""
        payload = {"command": action.value, "params": params, "timestamp": time.time()}
        
        if not self.simulation_mode:
            try:
                resp = requests.post(f"{BASE_URL}/command", json=payload, timeout=10)
                return resp.json()
            except Exception as e:
                print(f"⚠️ Failed to send command to Brev: {e}")

        print(f"📡 [SIMULATION] Sending {action.value} with params {params}")
        return {"status": "dispatched_simulated"}

    def get_visual_context(self):
        """Standardizes the visual feed metadata."""
        return type('obj', (object,), {
            "image_url": f"{BASE_URL}/video_feed",
            "camera_id": "Main_Camera_Brev",
            "sector_focus": "Primary_Die"
        })

# --- SINGLETON ---
# This is where you control the switch for the whole project
bridge = IsaacBridge(simulation_mode=False) 

if __name__ == "__main__":
    print(f"Testing connection to Brev at {BASE_URL}...")
    state = bridge.get_world_state()
    print(f"🌍 Live World State: {state.environment}")