import requests
import time
import sqlite3 # Added for Persistence
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

# --- CONFIGURATION ---
BREV_IP = "13.220.232.5"
PORT = 5000
BASE_URL = f"http://{BREV_IP}:{PORT}"

# --- 1. WORLD STATE OBJECT (The Digital Twin State) ---
@dataclass
class WorldState:
    """Represents the complete 'Physical Truth' of the simulation."""
    defect_density: float
    thermal_map: Dict[str, float]
    active_agents: int
    environment: str
    timestamp: float

# --- 2. ACTION SEMANTICS ---
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
    def __init__(self, db_path="isaac_persistence.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Creates the persistence layer for Replayable Experiments."""
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
        """Persists an event to the DB (Event Queue Persistence)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO event_log (event_type, severity, payload, timestamp) VALUES (?, ?, ?, ?)",
                (event.event_type, event.severity, str(event.payload), event.timestamp)
            )

    def get_world_state(self) -> WorldState:
        """Fetches the current 'State Machine' snapshot."""
        # Conceptually: This pulls from the Brev Isaac Sim instance
        return WorldState(
            defect_density=0.04,
            thermal_map={"Core_A": 45.2, "SRAM_1": 38.9},
            active_agents=1,
            environment="Cosmos_Orbit_Alpha",
            timestamp=time.time()
        )

    def send_command(self, action: RobotAction, params: Dict = None):
        """Standard Perception-Action command."""
        print(f"📡 Sending {action.value} with params {params}")
        # In production: requests.post(f"{BASE_URL}/command", json=...)
        return {"status": "dispatched"}

# --- SINGLETON ---
bridge = IsaacBridge()

if __name__ == "__main__":
    # Test Persistence
    e = IsaacEvent(event_type="FAULT_DETECTED", severity="CRITICAL", payload={"temp": 95})
    bridge.log_event(e)
    print("✅ Event Persisted to SQLite.")
    
    # Test World State
    state = bridge.get_world_state()
    print(f"🌍 Current World State: {state.environment} (Defects: {state.defect_density})")