import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time
import os
import math
import sqlite3
import uuid
from datetime import datetime
from ai_module import get_gemini_decision 
from isaac_bridge import bridge, RobotAction 

# --- 1. SYSTEM STATE OBJECT ---
class SystemState:
    def __init__(self, experiment_id, seed=42):
        self.experiment_id = experiment_id
        self.timestep = 0
        self.seed = seed
        self.oscillator = []
        self.freq_history = []
        # Upgraded timeline storage: dicts instead of raw strings
        self.action_timeline = [{"time": 0, "ai_intent": "BOOT", "robot_action": "INITIALIZE", "status": "NOMINAL"}]
        
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

# --- 2. SYSTEM CONFIGURATION & AESTHETICS ---
st.set_page_config(page_title="FICKS LABS | SURGE OS", layout="wide")

# Subtle, professional engineering theme (Dark slate with subtle purple accents)
st.markdown("""
    <style>
    .main { background: #0E0E12; color: #E2DEDB; font-family: 'Inter', sans-serif; }
    .ficks-header { font-size: 1.8rem; font-weight: 600; color: #A882DD; border-bottom: 1px solid #333; margin-bottom: 20px; padding-bottom: 10px; letter-spacing: 1px; }
    .metric-box { background: rgba(168, 130, 221, 0.05); border: 1px solid rgba(168, 130, 221, 0.2); padding: 15px; border-radius: 6px; margin-bottom: 10px; }
    .metric-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 1.4rem; font-weight: 600; color: #A882DD; font-family: monospace; }
    .timeline-table { width: 100%; font-size: 0.85rem; color: #ccc; border-collapse: collapse; }
    .timeline-table th { text-align: left; padding: 8px; border-bottom: 1px solid #444; color: #A882DD; }
    .timeline-table td { padding: 8px; border-bottom: 1px solid #222; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE INITIALIZATION ---
if 'db_ready' not in st.session_state:
    with sqlite3.connect('factory_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS experiments (experiment_id TEXT PRIMARY KEY, timestamp_start TEXT, mission_profile TEXT, chip_seed INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS device_states (experiment_id TEXT, timestep INTEGER, stage_id INTEGER, vth_personality REAL, temperature REAL, defect_density REAL, current REAL, region TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ai_decisions (experiment_id TEXT, timestep INTEGER, frequency REAL, temperature REAL, current REAL, ai_action TEXT, ai_reasoning TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS performance_metrics (experiment_id TEXT, timestep INTEGER, frequency REAL, power REAL, avg_temperature REAL, health_index REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS interventions (experiment_id TEXT, timestep INTEGER, action_type TEXT, parameter_changed TEXT, old_value REAL, new_value REAL)''')
    st.session_state.db_ready = True

def log_to_db(query, params):
    try:
        with sqlite3.connect('factory_data.db', timeout=10) as conn:
            conn.execute(query, params)
    except Exception as e:
        print(f"DB Error: {e}")

def calculate_mosfet_current(v_gs, v_ds, defect_density, temp_kelvin, variation):
    V_th_actual = 0.22 + (0.15 * defect_density) + variation - (0.0005 * (temp_kelvin - 300))
    mobility = 1.0 / (1 + (defect_density * 2.0) + ((temp_kelvin-300)*0.002))
    Kn = 0.0015 * mobility
    if v_gs < V_th_actual:
        return 1e-10 * (10 ** ((v_gs - V_th_actual) / 0.065)), "CUTOFF", V_th_actual
    elif v_ds < (v_gs - V_th_actual):
        return Kn * ((v_gs - V_th_actual) * v_ds - (v_ds**2)/2), "TRIODE", V_th_actual
    else:
        return 0.5 * Kn * (v_gs - V_th_actual)**2 * (1 + 0.04 * v_ds), "SATURATION", V_th_actual

if 'state' not in st.session_state:
    st.session_state.state = SystemState(str(uuid.uuid4()))

# --- 3. ORCHESTRATION ---
with st.sidebar:
    st.markdown("<div class='ficks-header'>FICKS LABS</div>", unsafe_allow_html=True)
    run_mode = st.radio("Run Mode", ["Live", "Replay"])
    mission = st.radio("Cosmos Environment", ["Terrestrial_Lab", "Orbital_Satellite"])
    v_gs = st.slider("Gate Voltage (V_gs)", 0.0, 1.0, 0.75)
    auto_repair = st.toggle("Autonomous AI Agent", value=True)
    
    st.divider()
    
    # Download button logic (safely checks if file exists first)
    if os.path.exists("factory_data.db"):
        with open("factory_data.db", "rb") as fp:
            st.download_button(label="Download DB", data=fp, file_name="surge_data.db")
    else:
        st.caption("Waiting for DB generation...")

@st.fragment(run_every="2s")
def solver_loop():
    if run_mode == "Replay":
        return

    s = st.session_state.state
    s.timestep += 1
    
    # PERCEPTION
    world_state = bridge.get_world_state()
    ambient_temp = 310 if mission == "Terrestrial_Lab" else 240
    
    total_delay, total_power, avg_temp = 0, 0, 0
    stage_currents = []
    
    # PHYSICS
    for i in range(5):
        if np.random.rand() < 0.005: 
            s.oscillator[i]['defects'] += 0.25
            s.action_timeline.insert(0, {"time": s.timestep, "ai_intent": "DETECT", "robot_action": "LOG", "status": "ANOMALY_SEU"})

        power = s.oscillator[i]['last_current'] * 0.8
        s.oscillator[i]['temp'] = ambient_temp + (power * 50000)
        ids, reg, vth = calculate_mosfet_current(v_gs, 0.8, s.oscillator[i]['defects'], s.oscillator[i]['temp'], s.oscillator[i]['vth_personality'])
        s.oscillator[i]['last_current'] = ids
        stage_currents.append(ids)
        total_power += power
        avg_temp += s.oscillator[i]['temp']
        total_delay += (1e-15 * 0.8) / max(ids, 1e-12)

    freq_ghz = (1.0 / (2 * total_delay)) / 1e9
    s.freq_history.append(freq_ghz)
    avg_temp /= 5
    healths = [1.0 - stage['defects'] for stage in s.oscillator]
    avg_health = sum(healths) / len(healths)

    # --- UI RENDER: PROFESSIONAL SCADA LAYOUT ---
    
    # LAYER 4: WORLD MODEL PANEL
    env_status = "ONLINE" if world_state.environment != "Simulated_Environment" else "FALLBACK"
    rad_level = "HIGH (1.2 Sv/h)" if mission == "Orbital_Satellite" else "NOMINAL (Background)"
    grav_level = "MICRO-G" if mission == "Orbital_Satellite" else "1.0 G"
    
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;">
            <div><span style="color:#888; font-size:0.8rem;">WORLD CONTEXT //</span> <b style="color:#A882DD;">{mission.upper()}</b></div>
            <div><span style="color:#888; font-size:0.8rem;">RADIATION:</span> {rad_level} &nbsp;&nbsp;|&nbsp;&nbsp; <span style="color:#888; font-size:0.8rem;">GRAVITY:</span> {grav_level}</div>
            <div><span style="color:#888; font-size:0.8rem;">LINK STATE:</span> <b style="color:{'#00FF41' if env_status == 'ONLINE' else '#FF4136'};">{env_status}</b></div>
        </div>
    """, unsafe_allow_html=True)

    # MAIN PANELS
    col_telemetry, col_kinematics = st.columns([1.2, 1])

    with col_telemetry:
        # Core Telemetry
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-box'><div class='metric-label'>Freq Stability</div><div class='metric-value'>{freq_ghz:.2f} GHz</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-box'><div class='metric-label'>Thermal Core</div><div class='metric-value'>{avg_temp:.1f} K</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-box'><div class='metric-label'>Health Index</div><div class='metric-value'>{avg_health*100:.1f}%</div></div>", unsafe_allow_html=True)
        
        # Stability Graph
        fig = go.Figure(go.Scatter(y=s.freq_history[-60:], mode='lines', line=dict(color='#A882DD', width=2)))
        fig.update_layout(title="Sub-Threshold Stability Tracking", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ccc', height=250, margin=dict(l=0, r=0, t=30, b=0), yaxis=dict(gridcolor='#222'), xaxis=dict(gridcolor='#222'))
        st.plotly_chart(fig, use_container_width=True)

    with col_kinematics:
        # LAYER 1 & 2: ROBOT STATE & JOINT VISUALIZER
        st.markdown("<div style='font-size:0.9rem; color:#888; margin-bottom:5px;'>KINEMATIC STATE VECTORS</div>", unsafe_allow_html=True)
        
        # Parse simulated or live joints (Default Franka pose if empty)
        raw_joints = world_state.thermal_map.get('Joint_Data', "0.0, -0.78, 0.0, -2.35, 0.0, 1.57, 0.78")
        try:
            joints = [float(x.strip()) for x in str(raw_joints).split(',')]
        except:
            joints = [0.0, -0.78, 0.0, -2.35, 0.0, 1.57, 0.78]
        
        categories = [f'J{i+1}' for i in range(len(joints[:7]))] # 7 DOF Arm
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=joints[:7], theta=categories, fill='toself', name='Joints (rad)',
            fillcolor='rgba(168, 130, 221, 0.2)', line_color='#A882DD'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[-3.14, 3.14], gridcolor='#333'), angularaxis=dict(gridcolor='#333')),
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ccc', height=250, margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; font-family:monospace; font-size:0.8rem; color:#A882DD;">
            <span>MODE: {'REPAIRING' if freq_ghz < 20.0 else 'STANDBY'}</span>
            <span>END-EFFECTOR: {'ACTIVE' if freq_ghz < 20.0 else 'IDLE'}</span>
        </div>
        """, unsafe_allow_html=True)

   # ACTION LOOP & TIMELINE
    if freq_ghz < 20.0 and auto_repair: # Using 20.0 threshold to force failure for the video
        decision = get_gemini_decision(freq_ghz, stage_currents[0]*1e6, avg_temp)
        
        # RESTORED: Log AI Decision to DB
        log_to_db("INSERT INTO ai_decisions VALUES (?,?,?,?,?,?,?)", 
                  (s.experiment_id, s.timestep, freq_ghz, avg_temp, stage_currents[0], decision, "Floor Violation"))

        if "REPAIR" in decision.upper() and s.action_timeline[0]["ai_intent"] != "REPAIR":
            old_val = s.oscillator[0]['defects']
            
            # Send command to Brev
            bridge.send_command(RobotAction.DEPLOY_AGENT, {"target": "Stage_0"})
            
            # Apply the Physics Heal
            s.oscillator[0]['defects'] = max(0, s.oscillator[0]['defects'] - 0.1)
            
            # RESTORED: Log Intervention to DB
            log_to_db("INSERT INTO interventions VALUES (?,?,?,?,?,?)", 
                      (s.experiment_id, s.timestep, "REPAIR", "defects", old_val, s.oscillator[0]['defects']))
            
            # ADDED: Explicit SUCCESS status in the timeline
            s.action_timeline.insert(0, {"time": s.timestep, "ai_intent": "REPAIR", "robot_action": "DEPLOY_AGENT", "status": "SUCCESS ✅"})

    # LAYER 3: ACTION TIMELINE
    st.markdown("<br><div style='font-size:0.9rem; color:#888; margin-bottom:10px;'>DECISION & ACTION TIMELINE</div>", unsafe_allow_html=True)
    
    table_html = "<table class='timeline-table'><tr><th>T-STEP</th><th>AI INTENT</th><th>ISAAC SIM ACTION</th><th>STATUS</th></tr>"
    for row in s.action_timeline[:5]:
        # Color coding the success!
        status_color = "#00FF41" if "SUCCESS" in row['status'] or row['status'] == "NOMINAL" else "#FF4136"
        table_html += f"<tr><td>{row['time']}</td><td>{row['ai_intent']}</td><td>{row['robot_action']}</td><td style='color:{status_color};'>{row['status']}</td></tr>"
    table_html += "</table>"
    
    st.markdown(table_html, unsafe_allow_html=True)

solver_loop()