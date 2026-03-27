import streamlit as st
import traci
import time
import os
import sys
from PIL import Image

# ── Make sure traci is importable ──────────────────────────────────────────────
if "SUMO_HOME" in os.environ:
    sys.path += [os.path.join(os.environ["SUMO_HOME"], "tools")]
else:
    st.error("❌ SUMO_HOME environment variable not set! Please set it before running.")
    st.stop()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rajiv Chowk Traffic Simulation",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 Smart Traffic Dashboard — Rajiv Chowk")
st.caption("Real-time SUMO simulation with Green Corridor for emergency vehicles")

# ── Sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Simulation Controls")
    screenshot_interval = st.slider("Screenshot every N steps", 1, 20, 5)
    sleep_time = st.slider("Frame delay (seconds)", 0.01, 0.5, 0.05)
    run_sim = st.button("▶️ Start Simulation", type="primary")
    stop_sim = st.button("⏹️ Stop")

# ── Layout: video on left, stats on right ──────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Live Simulation View")
    frame_placeholder = st.empty()

with col2:
    st.subheader("📊 Live Stats")
    step_display    = st.empty()
    vehicles_display = st.empty()
    emergency_display = st.empty()
    waiting_display  = st.empty()

# ── Session state to track if simulation is running ───────────────────────────
if "running" not in st.session_state:
    st.session_state.running = False

if stop_sim:
    st.session_state.running = False

# ── Main simulation loop ───────────────────────────────────────────────────────
SCREENSHOT_PATH = "temp_frame.png"
SUMO_CFG = "simulation.sumocfg"   # ← path to your config file

if run_sim:
    st.session_state.running = True

    # Start TraCI with sumo-gui
    try:
    	traci.init(port=37071)   # default SUMO port
    	traci.setOrder(2)       # 👈 viewer client
    except Exception as e:
        st.error(f"Failed to start SUMO: {e}")
        st.stop()

    step = 0

    while st.session_state.running and traci.simulation.getMinExpectedNumber() > 0:

        traci.simulationStep()
        step += 1

        # Only take a screenshot every N steps (reduces load)
        if step % screenshot_interval == 0:

            # ── Take screenshot ──────────────────────────────────────────────
            traci.gui.screenshot("View #0", SCREENSHOT_PATH)

            # ── Update the image frame ───────────────────────────────────────
            if os.path.exists(SCREENSHOT_PATH):
                img = Image.open(SCREENSHOT_PATH)
                frame_placeholder.image(img, use_column_width=True)

            # ── Gather live stats via TraCI ──────────────────────────────────
            vehicle_ids   = traci.vehicle.getIDList()
            total_vehicles = len(vehicle_ids)

            # Count emergency vehicles
            emergency_count = sum(
                1 for vid in vehicle_ids
                if traci.vehicle.getTypeID(vid) in {"ambulance", "firebrigade"}
            )

            # Average waiting time across all vehicles
            if total_vehicles > 0:
                avg_wait = sum(
                    traci.vehicle.getWaitingTime(vid) for vid in vehicle_ids
                ) / total_vehicles
            else:
                avg_wait = 0.0

            # ── Update stat boxes ────────────────────────────────────────────
            step_display.metric("Simulation Step", step)
            vehicles_display.metric("Vehicles on Network", total_vehicles)
            emergency_display.metric("🚨 Emergency Vehicles", emergency_count)
            waiting_display.metric("⏳ Avg Wait (s)", f"{avg_wait:.1f}")

        time.sleep(sleep_time)

    traci.close()
    st.success("✅ Simulation finished!")
    st.session_state.running = False
