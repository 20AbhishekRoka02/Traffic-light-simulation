import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import time
import random
from datetime import datetime
import folium
from streamlit_folium import st_folium

from config import JUNCTIONS, DENSITY_MAP, generate_historical_data, generate_predictions
from styles import PREMIUM_CSS

# ════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="AI Traffic Vision Command v5.0", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════════════
if "selected_junction" not in st.session_state:
    st.session_state.selected_junction = "india_gate"
if "historical" not in st.session_state:
    st.session_state.historical = generate_historical_data()
if "predictions" not in st.session_state:
    st.session_state.predictions = generate_predictions()
if "alerts" not in st.session_state:
    st.session_state.alerts = []

J = JUNCTIONS[st.session_state.selected_junction]
engine = J["decision_engine"]
env = J["environment"]
net = J["network_health"]
ts = datetime.now().strftime("%H:%M:%S")

# ════════════════════════════════════════════════════════════════════
# HEADER — Command Center Bar
# ════════════════════════════════════════════════════════════════════
hcol1, hcol2 = st.columns([4, 1])
with hcol1:
    st.markdown(f"""
    <div class="command-header">
        <div>
            <div class="brand">🛡️ AI TRAFFIC VISION COMMAND</div>
            <div class="sub">v5.0 Enterprise • {J['name']} • {J['city']} • Real-time Neural Inference Engine</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            <span class="inference-chip">⚡ {engine['last_inference_ms']}ms</span>
            <span class="inference-chip" style="background:rgba(52,211,153,0.08);border-color:rgba(52,211,153,0.2);color:var(--accent-emerald);">🎯 {engine['confidence']*100:.0f}%</span>
            <span class="status-pill"><span class="status-dot"></span>{J['status'].replace('_',' ')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
with hcol2:
    junc_options = {k: v["name"] for k, v in JUNCTIONS.items()}
    sel = st.selectbox("🔀 Junction", list(junc_options.keys()), format_func=lambda x: junc_options[x], label_visibility="collapsed")
    if sel != st.session_state.selected_junction:
        st.session_state.selected_junction = sel
        st.rerun()

# ════════════════════════════════════════════════════════════════════
# TOP METRICS STRIP — KPI Dashboard
# ════════════════════════════════════════════════════════════════════
total_v = sum(c["count"] for c in J["cameras"])
avg_speed = sum(c["speed_avg"] for c in J["cameras"]) / len(J["cameras"])
critical_count = sum(1 for c in J["cameras"] if c["density"] == "CRITICAL")
avg_queue = sum(c["queue_length"] for c in J["cameras"]) / len(J["cameras"])

m1, m2, m3, m4, m5, m6, m7, m8 = st.columns(8)
metrics = [
    (m1, "🚗", "VEHICLES", str(total_v), "Across All Feeds", ""),
    (m2, "⚡", "LATENCY", f'{engine["last_inference_ms"]}ms', "YOLOv8 Inference", "violet"),
    (m3, "🏎️", "AVG SPEED", f'{avg_speed:.0f}', "km/h Junction Avg", "amber"),
    (m4, "🔴", "CRITICAL", str(critical_count), "Lanes Over Threshold", "rose"),
    (m5, "🌿", "CO₂ CUT", env["reduction"], "vs Fixed Timer", ""),
    (m6, "🌡️", "AQI", str(env["aqi"]), "Air Quality Index", "amber" if env["aqi"] > 150 else ""),
    (m7, "📡", "GPU", f'{net["gpu_util"]}%', "Utilization", "violet"),
    (m8, "📐", "QUEUE", f'{avg_queue:.0f}m', "Average Length", "rose" if avg_queue > 200 else ""),
]
for col, icon, label, value, sub, cls in metrics:
    with col:
        st.markdown(f"""
        <div class="glass-v2" style="text-align:center;padding:12px 8px;">
            <div style="font-size:18px;margin-bottom:4px;">{icon}</div>
            <div class="metric-hero">
                <div class="val {cls}" style="font-size:22px;">{value}</div>
                <div class="unit">{label}</div>
            </div>
            <div style="font-size:8px;color:var(--text-dim);margin-top:2px;">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# MAIN TABS — Multi-Panel Command Interface
# ════════════════════════════════════════════════════════════════════
tab_live, tab_analytics, tab_network, tab_control = st.tabs([
    "🎥 LIVE VISION & CONTROL",
    "📊 ANALYTICS & PREDICTIONS",
    "🔧 NETWORK & TELEMETRY",
    "🚨 EMERGENCY & SCENARIOS"
])

# ═══════════════════════════════════════
# TAB 1: LIVE VISION & CONTROL
# ═══════════════════════════════════════
with tab_live:
    st.markdown('<div class="sec-title">📸 Multi-Lane YOLOv8 Vision Feeds <span class="live-tag"><span class="live-dot-r"></span>LIVE</span></div>', unsafe_allow_html=True)

    cam_cols = st.columns(4, gap="medium")
    for i, feed in enumerate(J["cameras"]):
        with cam_cols[i]:
            dm = DENSITY_MAP[feed["density"]]
            st.markdown(f"""
            <div class="cam-feed">
                <div class="cam-top">
                    <span class="cam-id">CAM_{feed['cam_id']:02d}</span>
                    <span class="density-badge {dm['class']}">{dm['icon']} {feed['density']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.image(feed["image"], use_container_width=True)
            vehs = feed["vehicles"]
            pills = " ".join([f'<span class="vtype-pill">🚗{vehs["cars"]}</span>',
                              f'<span class="vtype-pill">🚛{vehs["trucks"]}</span>',
                              f'<span class="vtype-pill">🏍️{vehs["bikes"]}</span>',
                              f'<span class="vtype-pill">🚌{vehs["buses"]}</span>'])
            st.markdown(f"""
            <div class="cam-feed" style="border-top:none;border-top-left-radius:0;border-top-right-radius:0;margin-top:-6px;">
                <div class="cam-bottom">
                    <div>
                        <div class="cam-count" style="color:{dm['color']}">{feed['count']}</div>
                        <div class="cam-label">Vehicles</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="cam-road">{feed['road']}</div>
                        <div class="cam-speed">{feed['speed_avg']} km/h • Queue: {feed['queue_length']}m</div>
                    </div>
                </div>
                <div style="padding:6px 12px 10px;display:flex;gap:4px;flex-wrap:wrap;">{pills}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Row 2: AI Brain + Map + Phase Timeline ──
    col_ai, col_map = st.columns([1.3, 2], gap="medium")

    with col_ai:
        st.markdown('<div class="sec-title">🧠 Neural Decision Engine</div>', unsafe_allow_html=True)

        if st.button("🚀 TRIGGER AI ANALYSIS CYCLE", use_container_width=True, key="ai_btn"):
            with st.status("Neural Analysis Running...", expanded=True) as status:
                steps = [
                    ("⏳ Fetching real-time vehicle counts from SUMO twin...", 0.4),
                    ("🔬 YOLOv8 inference on 4 HD streams (batch mode)...", 0.5),
                    ("🧮 Computing optimal phase allocation via RL agent...", 0.4),
                    ("📊 Updating predictive models with new telemetry...", 0.3),
                    ("✅ Syncing decisions to traffic controller...", 0.2),
                ]
                for msg, dur in steps:
                    st.write(msg)
                    time.sleep(dur)
                status.update(label="✅ Analysis Complete — Phase Updated", state="complete", expanded=False)

        # Active phase
        st.markdown(f"""
        <div class="glass-v2" style="margin-bottom:10px;">
            <div class="card-label">⚡ Active Phase</div>
            <div style="font-size:16px;font-weight:800;color:var(--accent-cyan);font-family:'Orbitron',sans-serif;">{engine['active_phase']}</div>
            <div style="height:5px;background:rgba(255,255,255,0.04);border-radius:3px;margin-top:8px;overflow:hidden;">
                <div style="width:75%;height:100%;border-radius:3px;background:linear-gradient(90deg,var(--accent-cyan),var(--accent-emerald));"></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:4px;">
                <span style="font-size:10px;color:var(--text-dim);">Elapsed: 45s</span>
                <span style="font-size:10px;color:var(--text-dim);">Allocated: {engine['allocated_time']}s</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Phase timeline
        phase_colors_map = {"ACTIVE": "rgba(56,189,248,0.3)", "COMPLETED": "rgba(52,211,153,0.15)", "QUEUED": "rgba(255,255,255,0.04)"}
        phase_text_map = {"ACTIVE": "var(--accent-cyan)", "COMPLETED": "var(--accent-emerald)", "QUEUED": "var(--text-dim)"}
        total_dur = sum(p["duration"] for p in engine["phase_queue"])
        segments = ""
        for p in engine["phase_queue"]:
            pct = p["duration"] / total_dur * 100
            active_cls = " active" if p["status"] == "ACTIVE" else ""
            segments += f'<div class="phase-segment{active_cls}" style="width:{pct}%;background:{phase_colors_map[p["status"]]};color:{phase_text_map[p["status"]]}">{p["duration"]}s</div>'

        st.markdown(f"""
        <div class="glass-v2" style="margin-bottom:10px;">
            <div class="card-label">🔄 Phase Rotation Timeline</div>
            <div class="phase-bar">{segments}</div>
            <div style="display:flex;justify-content:space-between;margin-top:6px;">
                {"".join(f'<span style="font-size:8px;color:var(--text-dim);">{p["name"].split("—")[0].strip()}</span>' for p in engine["phase_queue"])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # AI reasoning
        st.markdown(f"""
        <div class="glass-v2" style="margin-bottom:10px;">
            <div class="card-label">💡 AI Reasoning Log</div>
            <div style="font-size:11px;color:var(--text-secondary);line-height:1.7;">{engine['logic_reasoning']}</div>
            <div style="margin-top:8px;display:flex;gap:6px;">
                <span class="inference-chip">Model: {engine['model']}</span>
                <span class="inference-chip" style="background:rgba(52,211,153,0.08);border-color:rgba(52,211,153,0.2);color:var(--accent-emerald);">Conf: {engine['confidence']*100:.0f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Phase allocation chart
        phases = [p["name"] for p in engine["phase_queue"]]
        p_times = [p["duration"] for p in engine["phase_queue"]]
        p_colors = ["#f43f5e" if p["status"]=="ACTIVE" else "#34d399" if p["status"]=="COMPLETED" else "#3d4f63" for p in engine["phase_queue"]]
        fig_phase = go.Figure(go.Bar(x=p_times, y=phases, orientation='h', marker=dict(color=p_colors, line=dict(width=0), opacity=0.85),
                                      text=[f"{t}s" for t in p_times], textposition='outside', textfont=dict(family="JetBrains Mono", size=10, color="#6b7a8d")))
        fig_phase.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=40,t=5,b=5),
                                height=140, xaxis=dict(visible=False, range=[0, max(p_times)+15]),
                                yaxis=dict(tickfont=dict(family="Inter", size=9, color="#6b7a8d"), gridcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig_phase, use_container_width=True, config={'displayModeBar': False})

    with col_map:
        st.markdown('<div class="sec-title">📍 Digital Twin — Live SUMO Feed</div>', unsafe_allow_html=True)

        import traci
        import os
        import sys
        import time
        from PIL import Image

        if "SUMO_HOME" in os.environ:
            sys.path += [os.path.join(os.environ["SUMO_HOME"], "tools")]
        else:
            st.error("SUMO_HOME not set")
            st.stop()

        SCREENSHOT_PATH = "temp_frame.png"
        TRACI_PORT = 37071

        frame_placeholder = st.empty()

        # connect once
        if "traci_connected" not in st.session_state:
            try:
                traci.init(port=TRACI_PORT)
                traci.setOrder(2)
                st.session_state.traci_connected = True
            except Exception as e:
                st.error(f"Connection failed: {e}")
                st.stop()

        # 🚀 LOOP WITHOUT RERUN (KEY FIX)
        while True:
            try:
                # 🔥 REQUIRED: sync with simulation
                traci.simulationStep()

                # take screenshot
                traci.gui.screenshot("View #0", SCREENSHOT_PATH)

                if os.path.exists(SCREENSHOT_PATH):
                    with open(SCREENSHOT_PATH, "rb") as f:
                        img_bytes = f.read()
                    frame_placeholder.image(img_bytes, use_container_width=True)

            except Exception as e:
                st.error(f"Stream error: {e}")
                break

            time.sleep(0.05)

# ═══════════════════════════════════════
# TAB 2: ANALYTICS & PREDICTIONS
# ═══════════════════════════════════════
with tab_analytics:
    hist = st.session_state.historical

    ac1, ac2 = st.columns([2, 1], gap="medium")
    with ac1:
        st.markdown('<div class="sec-title">📈 24-Hour Traffic Flow Trends</div>', unsafe_allow_html=True)
        times = [d["time"] for d in hist]
        vehs = [d["vehicles"] for d in hist]
        speeds = [d["speed"] for d in hist]

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=times, y=vehs, mode='lines', name='Vehicles', fill='tozeroy',
                                        fillcolor='rgba(56,189,248,0.08)', line=dict(color='#38bdf8', width=2, shape='spline'),
                                        hovertemplate='<b>%{x}</b><br>Vehicles: %{y}<extra></extra>'))
        fig_trend.add_trace(go.Scatter(x=times, y=speeds, mode='lines', name='Avg Speed (km/h)', yaxis='y2',
                                        line=dict(color='#34d399', width=2, dash='dot', shape='spline'),
                                        hovertemplate='<b>%{x}</b><br>Speed: %{y} km/h<extra></extra>'))
        fig_trend.add_hline(y=15, line_dash="dash", line_color="rgba(244,63,94,0.3)", line_width=1,
                            annotation_text="Critical", annotation_font=dict(size=9, color="rgba(244,63,94,0.5)"))
        fig_trend.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=10,b=30), height=300,
            xaxis=dict(tickfont=dict(size=9, color='#6b7a8d'), gridcolor='rgba(255,255,255,0.03)', showgrid=True, dtick=8),
            yaxis=dict(tickfont=dict(size=9, color='#6b7a8d'), gridcolor='rgba(255,255,255,0.03)', title=dict(text="Vehicles", font=dict(size=9, color='#6b7a8d'))),
            yaxis2=dict(tickfont=dict(size=9, color='#34d399'), overlaying='y', side='right', title=dict(text="Speed km/h", font=dict(size=9, color='#34d399'))),
            legend=dict(font=dict(size=10, color='#6b7a8d'), bgcolor='rgba(0,0,0,0)', x=0, y=1.15, orientation='h'),
            font=dict(family='Inter'))
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

    with ac2:
        st.markdown('<div class="sec-title">🔮 6-Hour Prediction</div>', unsafe_allow_html=True)
        pred = st.session_state.predictions
        pt = [d["time"] for d in pred]
        pp = [d["predicted"] for d in pred]
        pu = [d["upper"] for d in pred]
        pl = [d["lower"] for d in pred]

        fig_pred = go.Figure()
        fig_pred.add_trace(go.Scatter(x=pt, y=pu, mode='lines', line=dict(width=0), showlegend=False))
        fig_pred.add_trace(go.Scatter(x=pt, y=pl, mode='lines', line=dict(width=0), fill='tonexty',
                                       fillcolor='rgba(167,139,250,0.1)', showlegend=False))
        fig_pred.add_trace(go.Scatter(x=pt, y=pp, mode='lines', name='Predicted', line=dict(color='#a78bfa', width=2, shape='spline')))
        fig_pred.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=10,b=30), height=300,
                               xaxis=dict(tickfont=dict(size=9, color='#6b7a8d'), gridcolor='rgba(255,255,255,0.03)', dtick=4),
                               yaxis=dict(tickfont=dict(size=9, color='#6b7a8d'), gridcolor='rgba(255,255,255,0.03)'),
                               legend=dict(font=dict(size=10, color='#6b7a8d'), bgcolor='rgba(0,0,0,0)'), font=dict(family='Inter'))
        st.plotly_chart(fig_pred, use_container_width=True, config={'displayModeBar': False})

    # Row 2: Density + Radar + Vehicle Classification
    bc1, bc2, bc3 = st.columns([1.2, 1, 1.2], gap="medium")
    with bc1:
        st.markdown('<div class="sec-title">📊 Lane Density Distribution</div>', unsafe_allow_html=True)
        roads = [c["road"] for c in J["cameras"]]
        counts = [c["count"] for c in J["cameras"]]
        colors = [DENSITY_MAP[c["density"]]["color"] for c in J["cameras"]]

        fig_d = go.Figure(go.Bar(x=roads, y=counts, marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
                                  text=counts, textposition='outside', textfont=dict(family="JetBrains Mono", size=12, color="#e6edf3"),
                                  hovertemplate="<b>%{x}</b><br>Vehicles: %{y}<extra></extra>"))
        fig_d.add_hline(y=10, line_dash="dash", line_color="rgba(244,63,94,0.3)", line_width=1,
                        annotation_text="Critical", annotation_font=dict(size=9, color="rgba(244,63,94,0.5)"), annotation_position="top right")
        fig_d.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=10,b=30), height=250,
                            xaxis=dict(tickfont=dict(size=10, color='#6b7a8d'), gridcolor='rgba(0,0,0,0)'),
                            yaxis=dict(tickfont=dict(size=9, color='#6b7a8d'), gridcolor='rgba(255,255,255,0.03)'), showlegend=False)
        st.plotly_chart(fig_d, use_container_width=True, config={'displayModeBar': False})

    with bc2:
        st.markdown('<div class="sec-title">🎯 Density Radar</div>', unsafe_allow_html=True)
        fig_r = go.Figure(go.Scatterpolar(r=counts+[counts[0]], theta=roads+[roads[0]], fill='toself',
                                           fillcolor='rgba(56,189,248,0.08)', line=dict(color='#38bdf8', width=2),
                                           marker=dict(size=6, color=colors+[colors[0]])))
        fig_r.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)',
                                       radialaxis=dict(visible=True, range=[0,25], gridcolor='rgba(255,255,255,0.04)', tickfont=dict(size=8, color='#6b7a8d')),
                                       angularaxis=dict(gridcolor='rgba(255,255,255,0.04)', tickfont=dict(size=10, color='#6b7a8d'))),
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=30,r=30,t=15,b=15), height=250, showlegend=False)
        st.plotly_chart(fig_r, use_container_width=True, config={'displayModeBar': False})

    with bc3:
        st.markdown('<div class="sec-title">🚗 Vehicle Classification</div>', unsafe_allow_html=True)
        all_v = {"Cars": 0, "Trucks": 0, "Bikes": 0, "Buses": 0, "Autos": 0}
        for c in J["cameras"]:
            for k, v in c["vehicles"].items():
                all_v[k.capitalize()] += v
        fig_vc = go.Figure(go.Pie(labels=list(all_v.keys()), values=list(all_v.values()), hole=0.6,
                                   marker=dict(colors=['#38bdf8', '#f43f5e', '#34d399', '#fbbf24', '#a78bfa'],
                                               line=dict(width=1, color='rgba(3,7,18,0.8)')),
                                   textinfo='percent+label', textfont=dict(size=10, color='#e6edf3'),
                                   hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'))
        fig_vc.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=10,b=10), height=250,
                             showlegend=False, annotations=[dict(text=f'<b>{total_v}</b><br>Total', x=0.5, y=0.5, font_size=14, font_color='#e6edf3', showarrow=False)])
        st.plotly_chart(fig_vc, use_container_width=True, config={'displayModeBar': False})

    # CO2 & Environmental Row
    st.markdown('<div class="sec-title">🌍 Environmental Impact Analysis</div>', unsafe_allow_html=True)
    ec1, ec2, ec3 = st.columns(3, gap="medium")
    with ec1:
        co2_vals = [d["co2"] for d in hist[-48:]]
        co2_times = [d["time"] for d in hist[-48:]]
        fig_co2 = go.Figure(go.Scatter(x=co2_times, y=co2_vals, mode='lines', fill='tozeroy',
                                        fillcolor='rgba(52,211,153,0.06)', line=dict(color='#34d399', width=1.5, shape='spline')))
        fig_co2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=25,b=20), height=180,
                              title=dict(text="CO₂ Trend (12h)", font=dict(size=11, color='#6b7a8d'), x=0),
                              xaxis=dict(tickfont=dict(size=8, color='#6b7a8d'), gridcolor='rgba(255,255,255,0.03)', dtick=6),
                              yaxis=dict(tickfont=dict(size=8, color='#6b7a8d'), gridcolor='rgba(255,255,255,0.03)'), showlegend=False)
        st.plotly_chart(fig_co2, use_container_width=True, config={'displayModeBar': False})
    with ec2:
        wait_vals = [d["wait_time"] for d in hist[-48:]]
        fig_wait = go.Figure(go.Scatter(x=co2_times, y=wait_vals, mode='lines', fill='tozeroy',
                                         fillcolor='rgba(251,191,36,0.06)', line=dict(color='#fbbf24', width=1.5, shape='spline')))
        fig_wait.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=25,b=20), height=180,
                               title=dict(text="Avg Wait Time (12h)", font=dict(size=11, color='#6b7a8d'), x=0),
                               xaxis=dict(tickfont=dict(size=8, color='#6b7a8d'), gridcolor='rgba(255,255,255,0.03)', dtick=6),
                               yaxis=dict(tickfont=dict(size=8, color='#6b7a8d'), gridcolor='rgba(255,255,255,0.03)'), showlegend=False)
        st.plotly_chart(fig_wait, use_container_width=True, config={'displayModeBar': False})
    with ec3:
        aqi = env["aqi"]
        aqi_color = "#34d399" if aqi < 100 else "#fbbf24" if aqi < 200 else "#f43f5e"
        aqi_label = "Good" if aqi < 100 else "Moderate" if aqi < 200 else "Unhealthy"
        st.markdown(f"""
        <div class="glass-v2" style="text-align:center;padding:20px;">
            <div class="card-label" style="justify-content:center;">🌡️ Air Quality Index</div>
            <div class="metric-hero">
                <div class="val" style="font-size:42px;background:linear-gradient(135deg,{aqi_color},{aqi_color}aa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{aqi}</div>
                <div class="unit" style="color:{aqi_color}">{aqi_label}</div>
            </div>
            <div class="aqi-bar"><div class="aqi-fill" style="width:{min(aqi/3, 100)}%;background:{aqi_color};"></div></div>
            <div style="display:flex;justify-content:space-between;margin-top:8px;">
                <span style="font-size:9px;color:var(--text-dim);">Noise: {env['noise_db']} dB</span>
                <span style="font-size:9px;color:var(--text-dim);">Temp: {env['temp_c']}°C</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════
# TAB 3: NETWORK & TELEMETRY
# ═══════════════════════════════════════
with tab_network:
    nc1, nc2, nc3 = st.columns([1.5, 1.5, 1], gap="medium")
    with nc1:
        st.markdown('<div class="sec-title">🔧 System Telemetry</div>', unsafe_allow_html=True)
        telemetry = [
            ("AI Model", engine["model"], "var(--accent-cyan)"),
            ("Inference FPS", f'{net["fps"]} fps', "var(--accent-emerald)"),
            ("SUMO Version", net["sumo_ver"], "var(--accent-violet)"),
            ("Active Cameras", f'{len(J["cameras"])} / {len(J["cameras"])} Online', "var(--accent-emerald)"),
            ("Phase Cycle", "4-Phase Adaptive RL", "var(--accent-cyan)"),
            ("System Uptime", net["uptime"], "var(--accent-emerald)"),
            ("Bandwidth", f'{net["bandwidth_mbps"]} Mbps', "var(--accent-cyan)"),
            ("Confidence", f'{engine["confidence"]*100:.0f}%', "var(--accent-emerald)"),
        ]
        rows = ""
        for param, val, col in telemetry:
            rows += f'<div class="stat-row"><span class="stat-key">{param}</span><span class="stat-val" style="color:{col}">{val}</span></div>'
        st.markdown(f'<div class="glass-v2">{rows}</div>', unsafe_allow_html=True)

    with nc2:
        st.markdown('<div class="sec-title">📊 Resource Utilization</div>', unsafe_allow_html=True)
        res_data = {"GPU": net["gpu_util"], "CPU": net["cpu_util"], "RAM": int(net["ram_gb"]/16*100), "Network": int(net["bandwidth_mbps"]/100*100)}
        fig_res = go.Figure()
        for i, (name, val) in enumerate(res_data.items()):
            color = "#34d399" if val < 60 else "#fbbf24" if val < 80 else "#f43f5e"
            fig_res.add_trace(go.Bar(x=[val], y=[name], orientation='h', marker=dict(color=color, opacity=0.8),
                                      text=f'{val}%', textposition='outside', textfont=dict(size=10, color='#e6edf3'), showlegend=False))
        fig_res.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=40,t=5,b=5), height=200,
                              xaxis=dict(visible=False, range=[0, 110]), yaxis=dict(tickfont=dict(size=11, color='#6b7a8d'), gridcolor='rgba(0,0,0,0)'),
                              barmode='stack')
        st.plotly_chart(fig_res, use_container_width=True, config={'displayModeBar': False})

    with nc3:
        st.markdown('<div class="sec-title">🟢 Health Status</div>', unsafe_allow_html=True)
        services = [("YOLOv8 Engine", "ok"), ("SUMO Twin", "ok"), ("Camera Array", "ok"), ("Phase Controller", "ok"),
                    ("Emergency Sys", "ok"), ("Data Pipeline", "ok"), ("Cloud Sync", "warn"), ("Backup Node", "ok")]
        health_html = ""
        for svc, status in services:
            dot_cls = f"health-{status}"
            health_html += f'<div class="stat-row"><span class="stat-key"><span class="health-dot {dot_cls}"></span>{svc}</span><span class="stat-val" style="color:{"var(--accent-emerald)" if status=="ok" else "var(--accent-amber)"};font-size:10px;">{"ONLINE" if status=="ok" else "DEGRADED"}</span></div>'
        st.markdown(f'<div class="glass-v2">{health_html}</div>', unsafe_allow_html=True)

    # Live log
    st.markdown('<div class="sec-title">📝 Real-time System Log</div>', unsafe_allow_html=True)
    phase_rot_str = "→".join(p["name"].split("—")[0].strip() + "(" + str(p["duration"]) + "s)" for p in engine["phase_queue"])
    logs = [
        f'<span class="ts">[{ts}]</span> <span class="info">SYS</span> Neural Inference Engine v5.0 online — latency {engine["last_inference_ms"]}ms — confidence {engine["confidence"]*100:.0f}%',
        f'<span class="ts">[{ts}]</span> <span class="err">CAM_01</span> {J["cameras"][0]["road"]} density {J["cameras"][0]["density"]} → {J["cameras"][0]["count"]} vehicles | speed {J["cameras"][0]["speed_avg"]} km/h',
        f'<span class="ts">[{ts}]</span> <span class="ok">DECISION</span> {engine["active_phase"]} allocated {engine["allocated_time"]}s green — RL agent reward: +0.87',
        f'<span class="ts">[{ts}]</span> <span class="vio">YOLO</span> Batch inference: {total_v} objects classified across {len(J["cameras"])} feeds — {engine["model"]}',
        f'<span class="ts">[{ts}]</span> <span class="warn">ENV</span> CO₂: {env["current_co2"]} ppm | AQI: {env["aqi"]} | Reduction: {env["reduction"]} vs baseline',
        f'<span class="ts">[{ts}]</span> <span class="ok">SUMO</span> Digital twin sync complete — junction state updated — SUMO {net["sumo_ver"]}',
        f'<span class="ts">[{ts}]</span> <span class="info">SYS</span> Emergency corridor: STANDBY | GPU: {net["gpu_util"]}% | CPU: {net["cpu_util"]}% | RAM: {net["ram_gb"]}GB',
        f'<span class="ts">[{ts}]</span> <span class="ok">PHASE</span> Rotation: {phase_rot_str}',
    ]
    st.markdown(f'<div class="log-v2">{"<br>".join(logs)}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════
# TAB 4: EMERGENCY & SCENARIOS
# ═══════════════════════════════════════
with tab_control:
    ec1, ec2 = st.columns([1.5, 1], gap="medium")
    with ec1:
        st.markdown('<div class="sec-title">🚨 Emergency Corridor System</div>', unsafe_allow_html=True)
        emg_on = st.toggle("🔴 Simulate Emergency Vehicle Detection", key="emg_toggle")

        if emg_on:
            st.markdown(f"""
            <div class="emg-alert">
                <div class="emg-icon">🚑</div>
                <div>
                    <div class="emg-title">⚠️ AMBULANCE DETECTED — CLEARING {J['cameras'][0]['road'].upper()}</div>
                    <div class="emg-sub">Priority override active • All phases suspended • Green corridor ETA: 45 seconds • Signal preemption engaged</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="glass-v2" style="margin-top:10px;border-color:rgba(244,63,94,0.25);">
                <div class="card-label" style="color:var(--accent-rose);">🔴 Emergency Corridor Status</div>
                <div style="font-size:11px;color:var(--text-secondary);line-height:2;">
                    <b style="color:var(--accent-rose);">Target Lane:</b> {J['cameras'][0]['road']} (Priority Corridor)<br>
                    <b style="color:var(--accent-rose);">Override:</b> All Phases Suspended — Emergency Preemption<br>
                    <b style="color:var(--accent-rose);">Signal State:</b> GREEN — {J['cameras'][0]['road']} Only | All others RED<br>
                    <b style="color:var(--accent-rose);">Queue Clear:</b> Active — Vehicles diverted to secondary routes<br>
                    <b style="color:var(--accent-rose);">Duration:</b> Until corridor clear + 15s buffer
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="glass-v2">
                <div class="card-label">✅ Normal Operations</div>
                <div style="font-size:11px;color:var(--text-secondary);line-height:2;">
                    <b style="color:var(--accent-emerald);">Ambulance Detected:</b> No<br>
                    <b style="color:var(--accent-emerald);">Corridor Active:</b> No — Standby Mode<br>
                    <b style="color:var(--accent-emerald);">Mode:</b> Normal AI Adaptive Operation<br>
                    <b style="color:var(--accent-emerald);">Override:</b> Standby — Ready for instant activation
                </div>
            </div>
            """, unsafe_allow_html=True)

    with ec2:
        st.markdown('<div class="sec-title">⚙️ Scenario Controls</div>', unsafe_allow_html=True)

        scenario = st.selectbox("Select Scenario", ["Normal Operation", "Peak Hour Rush", "VIP Convoy", "Road Closure", "Festival Traffic", "Weather Emergency"], key="scenario_sel")
        st.markdown(f"""
        <div class="glass-v2" style="margin-top:8px;">
            <div class="card-label">📋 Active Scenario</div>
            <div style="font-size:13px;font-weight:700;color:var(--accent-cyan);">{scenario}</div>
            <div style="font-size:10px;color:var(--text-dim);margin-top:4px;">Scenario parameters loaded into decision engine</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 REFRESH ALL DATA", use_container_width=True, key="refresh_btn"):
            st.session_state.historical = generate_historical_data()
            st.session_state.predictions = generate_predictions()
            st.rerun()

        st.markdown(f"""
        <div class="glass-v2" style="margin-top:8px;">
            <div class="card-label">📡 Junction Info</div>
            <div style="font-size:10px;color:var(--text-secondary);line-height:1.8;">
                <b>Name:</b> {J['name']}<br>
                <b>Zone:</b> {J['zone']}<br>
                <b>Priority:</b> {J['priority']}<br>
                <b>Coordinates:</b> {J['coordinates'][0]:.4f}, {J['coordinates'][1]:.4f}<br>
                <b>Cameras:</b> {len(J['cameras'])} active feeds
            </div>
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════
st.divider()
st.markdown(f"""
<div style="text-align:center;padding:6px 0;">
    <span style="font-family:'Orbitron',sans-serif;font-size:10px;color:var(--text-dim);letter-spacing:2px;">
        AI TRAFFIC VISION COMMAND v5.0 ENTERPRISE • {J['name']} • {J['city']} •
        <span style="color:var(--accent-emerald);">ALL SYSTEMS OPERATIONAL</span> •
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </span>
</div>
""", unsafe_allow_html=True)