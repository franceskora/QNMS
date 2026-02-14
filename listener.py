from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import threading

# 1. Start the Simulation App (MUST BE FIRST)
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})


# 2. Correct 5.1 Imports
from isaacsim.core.api import World
# Using the dedicated Franka class handles the /panda vs /Franka pathing automatically
from isaacsim.robot.manipulators.examples.franka import Franka 
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.storage.native import get_assets_root_path
from isaacsim.core.utils.types import ArticulationAction

# 3. Setup the World
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

# 4. Add the Robot using the specialized class
# This class knows exactly where the articulation root and joints are.
robot = world.scene.add(
    Franka(prim_path="/World/Franka", name="franka_arm")
)

# 5. Initialize Physics
world.reset()
# We take one step to ensure the physics 'Articulation View' is actually built in memory
world.step(render=True)

# -------------------------
# FLASK SERVER
# -------------------------
app = Flask(__name__)
CORS(app)

@app.route('/telemetry', methods=['GET'])
def get_telemetry():
    try:
        # Specialized Franka class has better internal joint tracking
        joints = robot.get_joint_positions().tolist()
    except Exception as e:
        joints = []
        print(f"Telemetry Error: {e}")

    return jsonify({
        "status": "LIVE_ISAAC_SIM",
        "temperature": 52.1,
        "robot_state": "IDLE",
        "cosmos_environment": "Orbital_Satellite_Bay",
        "joint_positions": joints
    })

def execute_repair():
    """Background task to run physics without blocking the web server."""
    for _ in range(60): 
        world.step(render=True)

@app.route('/command', methods=['POST'])
def handle_command():
    data = request.json
    cmd = data.get('command')

    if cmd == "deploy_nano_agent":
        repair_pose = ArticulationAction(
            joint_positions=np.array([0.0, -0.6, 0.0, -2.1, 0.0, 1.5, 0.7, 0.04, 0.04])
        )
        robot.apply_action(repair_pose)

        # 🚀 THE FIX: Start the 60 steps in a separate thread
        thread = threading.Thread(target=execute_repair)
        thread.start()

        # IMMEDIATELY tell Vultr success so the dashboard doesn't time out
        return jsonify({"status": "success", "message": "Repair initiated in background"})

    return jsonify({"status": "error", "message": "Unknown command"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)