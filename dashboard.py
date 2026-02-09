import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time
import random
import sqlite3
from datetime import datetime

# --- 1. HUD STYLING ---
st.set_page_config(page_title="FICKS LABS | QNMS 2nm", layout="wide")

st.markdown("""
    <style>
    .main { background: #000; color: #00FF41; font-family: 'Courier New', monospace; }
    .ficks-header { font-size: 2rem; font-weight: 800; color: #7000FF; border-bottom: 2px solid #7000FF; margin-bottom: 20px; letter-spacing: 2px; }
    .stMetric { background: rgba(112, 0, 255, 0.05); border: 1px solid #333; padding: 10px; }
    .terminal { background: #000; border: 1px solid #7000FF; padding: 15px; height: 380px; overflow-y: auto; font-size: 0.75rem; color: #00FF41; }
    .safety-gate { color: #00FF41; font-weight: bold; border: 1px solid #00FF41; padding: 5px; text-align: center; margin-bottom: 10px; }
    .warning-gate { color: #FFA500; font-weight: bold; border: 1px solid #FFA500; padding: 5px; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE 2nm PHYSICS KERNEL ---
def get_sim_data(aging_factor):
    ideal_v = 0.85 
    # RTS Noise (Quantum Jitter)
    noise = random.uniform(-0.01, 0.01) if random.random() > 0.15 else random.uniform(-0.05, 0.05)
    actual_v = ideal_v - (aging_factor * 0.012) + noise
    leakage = 10 + (aging_factor * 65) + random.uniform(-8, 8) 
    ber = 1e-9 * (1.9 ** aging_factor) 
    return {"v": actual_v, "ideal_v": ideal_v, "leak": leakage, "ber": ber, "res": abs(actual_v - ideal_v)}

# Persistent Session State
if 'aging' not in st.session_state: st.session_state.aging = 0
if 'logs' not in st.session_state: st.session_state.logs = [">> FICKS_LABS: QNMS KERNEL RELOADED"]
if 'res_history' not in st.session_state: st.session_state.res_history = [0.01, 0.012, 0.009]
# NEW: Tracking Healing Percentage
if 'total_damage' not in st.session_state: st.session_state.total_damage = 0.0
if 'total_healed' not in st.session_state: st.session_state.total_healed = 0.0

# --- 3. SIDEBAR: OPERATOR SIGNAL ---
with st.sidebar:
    st.markdown("<div class='ficks-header'>FICKS LABS</div>", unsafe_allow_html=True)
    st.subheader("📡 Mission Profile")
    mode = st.radio("Environment", ["Consumer Smartphone", "Deep Space Satellite"])
    
    st.subheader("⚙️ Verification Gate")
    default_limit = 0.88 if mode == "Consumer Smartphone" else 0.96
    v_max = st.slider("Vdd Safety Limit", 0.8, 1.1, default_limit)
    
    st.write("---")
    if st.button("Inject Atomic Stress Event"):
        st.session_state.aging += 10
        st.session_state.total_damage += 10 # Track the damage
    st.caption(f"Backend: Vultr-VM-Surge")

# --- 4. THE AUTONOMOUS MISSION LOOP ---
@st.fragment(run_every="3s")
def qnms_orchestration():
    # Simulate natural aging
    degradation = 0.08
    st.session_state.aging += degradation
    st.session_state.total_damage += degradation
    
    data = get_sim_data(st.session_state.aging)
    st.session_state.res_history.append(data['res'])
    
    # CALCULATE HEALING EFFICIENCY %
    if st.session_state.total_damage > 0:
        efficiency = (st.session_state.total_healed / st.session_state.total_damage) * 100
    else:
        efficiency = 0.0

    # 🛰️ HUD: TELEMETRY
    st.markdown(f"### 🛰️ QNMS : 2nm MONITOR | <span style='color:#7000FF'>{mode.upper()}</span>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RESIDUAL (R)", f"{data['res']:.4f}", f"{'CRITICAL' if data['res'] > 0.06 else 'STABLE'}")
    c2.metric("Vdd (PHYS vs GHOST)", f"{data['v']:.3f}V", f"Δ {data['v']-data['ideal_v']:.3f}")
    
    # NEW METRIC: HEALING EFFICIENCY
    # This proves your point: Even a small percentage is valuable.
    c3.metric("HEALING EFFICIENCY", f"{efficiency:.2f}%", f"{'+0.5%' if st.session_state.total_healed > 0 else '0%'}")
    
    c4.metric("PREDICTED LIFESPAN", f"{max(0.2, 6.0 - (st.session_state.aging/4)):.1f} Yrs", "AI Optimized")

    st.divider()
    col_viz, col_log = st.columns([2, 1])

    # 🛠️ AI REASONING & SAFETY GATE
    is_critical = data['res'] > 0.06
    thermal_warning = data['v'] > 0.92
    
    if is_critical:
        st.session_state.logs.append(f"!! ALERT: Physics Deviation R={data['res']:.4f}")
        st.session_state.logs.append(f">> CONSULTING GEMAI-1.5-FLASH ON VULTR...")
        time.sleep(0.5) 
        
        strategy = "NANOSHEET REDUNDANCY" if mode == "Deep Space Satellite" else "ADAPTIVE BIAS SCALING"
        st.session_state.logs.append(f">> REASONING: NBTI Aging detected. Strategy: {strategy}.")

        suggested_v = data['v'] + 0.08
        if suggested_v > v_max:
            st.session_state.logs.append(f"!! SAFETY_GATE: REJECTED {suggested_v}V (Thermal Limit Exceeded)")
        else:
            st.session_state.logs.append(f"✅ SAFETY_GATE: VERIFIED {suggested_v}V. Applying RTL Patch.")
            
            # --- DATABASE SYNC ---
            try:
                # Use 'with' to auto-close the connection (Professional Standard)
                with sqlite3.connect('factory_data.db') as conn:
                    conn.execute("INSERT INTO production_logs (timestamp, event_type, sector, residual) VALUES (?, ?, ?, ?)", 
                                 (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'HEAL_SUCCESS', mode, float(data['res'])))
            except Exception as e:
                st.session_state.logs.append(f"!! DB_ERROR: {str(e)}")
            # ---------------------

            # --- SMART DYNAMIC HEALING (No Magic Numbers) ---
            severity = data['res'] # How bad is the gap?
            # Satellites get stronger medicine (80x), Phones get lighter medicine (50x)
            multiplier = 80 if mode == "Deep Space Satellite" else 50
            
            heal_amount = severity * multiplier
            
            st.session_state.aging -= heal_amount
            st.session_state.total_healed += heal_amount 
            st.session_state.logs.append(f">> SYSTEM: Recovered {heal_amount:.2f} units (Efficiency: {multiplier}x).")

    # 🎮 THE KINETIC DIGITAL TWIN (FIXED RENDERING)
    with col_viz:
        fig = go.Figure()
        
        # Create 3 Layers (Nanosheets)
        for i, z_h in enumerate([0, 2, 4]):
            # Color Logic
            color = '#00F0FF' # Cyan (Healthy)
            if is_critical and i == 1: 
                color = '#FF4B4B' # Red (Broken)
            elif thermal_warning:
                color = '#FFA500' # Orange (Hot)
            elif not is_critical and st.session_state.aging < 10 and i == 1:
                color = '#7000FF' # Purple (Healed)

            # FIX: Using Scatter3d with surfaceaxis=2 fills the shape (Z-axis fill)
            # This guarantees it will be visible unlike Mesh3d
            fig.add_trace(go.Scatter3d(
                x=[0, 10, 10, 0, 0],
                y=[0, 0, 10, 10, 0],
                z=[z_h, z_h, z_h, z_h, z_h],
                mode='lines',
                surfaceaxis=2, # This fills the loop
                surfacecolor=color,
                opacity=0.8,
                line=dict(color='white', width=2),
                showlegend=False
            ))

        fig.update_layout(
            scene=dict(
                # Camera position to ensure we see the sheets
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)), 
                bgcolor='black', 
                xaxis=dict(visible=False), 
                yaxis=dict(visible=False), 
                zaxis=dict(visible=False, range=[-1, 6])
            ),
            margin=dict(l=0,r=0,b=0,t=0), 
            height=350, 
            paper_bgcolor='black'
        )
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        
        # RESIDUAL CHART
        res_fig = go.Figure(go.Scatter(y=st.session_state.res_history[-30:], mode='lines', line=dict(color='#7000FF', width=3), fill='tozeroy', fillcolor='rgba(112, 0, 255, 0.2)'))
        res_fig.update_layout(title="Sub-Atomic Prediction Error (Residual R)", height=180, margin=dict(l=0,r=0,b=0,t=30), 
                              paper_bgcolor='black', plot_bgcolor='black', font_color='#00FF41', xaxis_visible=False, yaxis=dict(range=[0, 0.15]))
        st.plotly_chart(res_fig, width='stretch')

    # TERMINAL LOGS
    with col_log:
        status_box = "warning-gate" if thermal_warning else "safety-gate"
        status_text = "WARNING: THERMAL LIMIT" if thermal_warning else "SAFETY_GATE: ACTIVE"
        st.markdown(f"<div class='{status_box}'>{status_text}</div>", unsafe_allow_html=True)
        
        st.subheader("🏭 PRODUCTION_LOGS")
        log_html = f"<div class='terminal'>{'<br>'.join(st.session_state.logs[-14:])}</div>"
        st.markdown(log_html, unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, 1.0 - (st.session_state.aging / 50))), text="LATTICE_INTEGRITY")

qnms_orchestration()