import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time
import math
import sqlite3
import uuid
from datetime import datetime
from ai_module import get_gemini_decision 
from isaac_bridge import bridge, RobotAction 

# --- 1. SYSTEM STATE OBJECT (Architecture A) ---
class SystemState:
    """Wraps the entire Digital Twin state for serialization and replay."""
    def __init__(self, experiment_id, seed=42):
        self.experiment_id = experiment_id
        self.timestep = 0
        self.seed = seed
        self.oscillator = []
        self.freq_history = []
        self.logs = [f">> SURGE OS BOOTED | ID: {experiment_id}"]
        
        # Initialize 5-stage Ring Oscillator DNA
        np.random.seed(seed)
        W_sheet, L_gate, A_vt = 30e-9, 12e-9, 3.5e-3
        sigma_vth = A_vt / math.sqrt(W_sheet * L_gate * 1e12) 
        
        for i in range(5):
            self.oscillator.append({
                'defects': 0.0, 
                'temp': 300.0,
                'vth_personality': np.random.normal(0, sigma_vth),
                'last_current': 10e-6
            })

# --- 2. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="FICKS LABS | SURGE OS v1.1", layout="wide")

st.markdown("""
    <style>
    .main { background: #000; color: #00FF41; font-family: 'Courier New', monospace; }
    .ficks-header { font-size: 2rem; font-weight: 800; color: #7000FF; border-bottom: 2px solid #7000FF; margin-bottom: 20px; letter-spacing: 2px; }
    .stMetric { background: rgba(112, 0, 255, 0.05); border: 1px solid #333; padding: 10px; }
    .terminal { background: #000; border: 1px solid #7000FF; padding: 15px; height: 380px; overflow-y: auto; font-size: 0.75rem; color: #00FF41; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Database Schema
if 'db_ready' not in st.session_state:
    with sqlite3.connect('factory_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS experiments (experiment_id TEXT PRIMARY KEY, timestamp_start TEXT, mission_profile TEXT, chip_seed INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS device_states (experiment_id TEXT, timestep INTEGER, stage_id INTEGER, vth_personality REAL, temperature REAL, defect_density REAL, current REAL, region TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ai_decisions (experiment_id TEXT, timestep INTEGER, frequency REAL, temperature REAL, current REAL, ai_action TEXT, ai_reasoning TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS performance_metrics (experiment_id TEXT, timestep INTEGER, frequency REAL, power REAL, avg_temperature REAL, health_index REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS interventions (experiment_id TEXT, timestep INTEGER, action_type TEXT, parameter_changed TEXT, old_value REAL, new_value REAL)''')
    st.session_state.db_ready = True

# --- 3. HELPER: DB Persistence ---
def log_to_db(query, params):
    """Optimized DB handler to prevent file locks."""
    try:
        with sqlite3.connect('factory_data.db', timeout=10) as conn:
            conn.execute(query, params)
    except Exception as e:
        print(f"DB Error: {e}")

# --- 4. PHYSICS KERNEL ---
def calculate_mosfet_current(v_gs, v_ds, defect_density, temp_kelvin, variation):
    V_th_actual = 0.22 + (0.15 * defect_density) + variation - (0.0005 * (temp_kelvin - 300))
    mobility = 1.0 / (1 + (defect_density * 2.0) + ((temp_kelvin-300)*0.002))
    Kn = 0.0015 * mobility
    if v_gs < V_th_actual:
        I_ds = 1e-10 * (10 ** ((v_gs - V_th_actual) / 0.065))
        return I_ds, "CUTOFF", V_th_actual
    elif v_ds < (v_gs - V_th_actual):
        I_ds = Kn * ((v_gs - V_th_actual) * v_ds - (v_ds**2)/2)
        return I_ds, "TRIODE", V_th_actual
    else:
        I_ds = 0.5 * Kn * (v_gs - V_th_actual)**2 * (1 + 0.04 * v_ds) 
        return I_ds, "SATURATION", V_th_actual

# --- 5. INITIALIZATION ---
if 'state' not in st.session_state:
    st.session_state.state = SystemState(str(uuid.uuid4()))

# --- 6. ORCHESTRATION ---
with st.sidebar:
    st.markdown("<div class='ficks-header'>FICKS LABS</div>", unsafe_allow_html=True)
    run_mode = st.radio("Run Mode", ["Live", "Replay"]) # Architecture D
    mission = st.radio("Cosmos Environment", ["Terrestrial_Lab", "Orbital_Satellite"])
    
    if 'mission_logged' not in st.session_state:
        log_to_db("INSERT INTO experiments VALUES (?, ?, ?, ?)", 
                  (st.session_state.state.experiment_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), mission, st.session_state.state.seed))
        st.session_state.mission_logged = True
        
    v_gs = st.slider("Gate Voltage (V_gs)", 0.0, 1.0, 0.75)
    auto_repair = st.toggle("Autonomous Repair Agent", value=True)

@st.fragment(run_every="2s")
def solver_loop():
    if run_mode == "Replay":
        st.warning("Replay Mode Active: Step-through enabled.")
        return

    s = st.session_state.state
    s.timestep += 1
    
    # PERCEPTION
    world_state = bridge.get_world_state()
    ambient_temp = 310 if mission == "Terrestrial_Lab" else 240
    
    total_delay, total_power, avg_temp = 0, 0, 0
    stage_currents = []
    
    # --- CLOSED-LOOP PHYSICS ---
    for i in range(5):
        # A. Fault Injection (Architecture B)
        if np.random.rand() < 0.005: # Cosmic Event
            s.oscillator[i]['defects'] += 0.25
            s.logs.append(f">> COSMIC EVENT: SEU detected in Stage {i}.")

        # B. Thermal & Physics
        power = s.oscillator[i]['last_current'] * 0.8
        s.oscillator[i]['temp'] = ambient_temp + (power * 50000)
        
        ids, reg, vth = calculate_mosfet_current(v_gs, 0.8, s.oscillator[i]['defects'], s.oscillator[i]['temp'], s.oscillator[i]['vth_personality'])
        
        s.oscillator[i]['last_current'] = ids
        stage_currents.append(ids)
        total_power += power
        avg_temp += s.oscillator[i]['temp']
        total_delay += (1e-15 * 0.8) / max(ids, 1e-12)
        
        # C. Aging
        mult = 1.5 if mission == "Orbital_Satellite" else 1.0
        rate = mult * 0.02 * math.exp(-0.15 / (8.617e-5 * s.oscillator[i]['temp']))
        if reg == "SATURATION": s.oscillator[i]['defects'] += (rate * 0.01)

        # Log Device State
        log_to_db("INSERT INTO device_states VALUES (?,?,?,?,?,?,?,?)", 
                  (s.experiment_id, s.timestep, i, s.oscillator[i]['vth_personality'], s.oscillator[i]['temp'], s.oscillator[i]['defects'], ids, reg))

    freq_ghz = (1.0 / (2 * total_delay)) / 1e9
    s.freq_history.append(freq_ghz)
    avg_temp /= 5
    
    # D. Improved Health Model (Architecture C)
    healths = [1.0 - stage['defects'] for stage in s.oscillator]
    avg_health = sum(healths) / len(healths)
    
    log_to_db("INSERT INTO performance_metrics VALUES (?,?,?,?,?,?)", (s.experiment_id, s.timestep, freq_ghz, total_power, avg_temp, avg_health))

    # --- UI RENDER ---
    st.markdown(f"### ⚡ SURGE MONITOR | {world_state.environment}", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Frequency", f"{freq_ghz:.3f} GHz")
    c2.metric("Isaac Sim Agents", f"{world_state.active_agents}")
    c3.metric("Avg Thermal", f"{avg_temp:.1f} K")
    c4.metric("Health Index", f"{avg_health*100:.1f}%")
    
    col_viz, col_log = st.columns([2,1])
    with col_viz:
        viz = bridge.get_visual_context()
        st.image("https://media.giphy.com/media/3o7qE1YN7aQZ3qhTLy/giphy.gif", caption=f"Optical: {viz.camera_id}")
        fig = go.Figure(go.Scatter(y=s.freq_history[-50:], mode='lines', line=dict(color='#00FF41')))
        fig.update_layout(title="Stability", paper_bgcolor='black', plot_bgcolor='black', font_color='#00FF41', height=250)
        st.plotly_chart(fig, use_container_width=True)

    with col_log:
        if freq_ghz < 2.5 and auto_repair:
            decision = get_gemini_decision(freq_ghz, stage_currents[0]*1e6, avg_temp)
            s.logs.append(f">> GEMINI: {decision}")
            log_to_db("INSERT INTO ai_decisions VALUES (?,?,?,?,?,?,?)", (s.experiment_id, s.timestep, freq_ghz, avg_temp, stage_currents[0], decision, "Floor Violation"))

            if "REPAIR" in decision.upper():
                old_val = s.oscillator[0]['defects']
                bridge.send_command(RobotAction.DEPLOY_AGENT, {"target": "Stage_0"})
                s.oscillator[0]['defects'] = max(0, s.oscillator[0]['defects'] - 0.1)
                log_to_db("INSERT INTO interventions VALUES (?,?,?,?,?,?)", (s.experiment_id, s.timestep, "REPAIR", "defects", old_val, s.oscillator[0]['defects']))
                s.logs.append(">> ISAAC SIM: Repair Complete.")
        
        st.subheader("🏭 EVENT_STREAM")
        st.markdown(f"<div class='terminal'>{'<br>'.join(s.logs[-12:])}</div>", unsafe_allow_html=True)

solver_loop()

with st.sidebar:
    st.divider()
    try:
        with open("factory_data.db", "rb") as fp:
            st.download_button(label="Download DB", data=fp, file_name="surge_data.db")
    except: pass