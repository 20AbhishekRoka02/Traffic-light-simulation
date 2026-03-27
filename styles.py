"""
Premium CSS Theme — AI Traffic Vision Command v5.0
Ultra-dark glassmorphism with animated neon accents, particle effects, and micro-interactions.
"""

PREMIUM_CSS = """
<style>
/* ── Import Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&family=Orbitron:wght@400;500;600;700;800;900&display=swap');

/* ── Root Variables ── */
:root {
    --bg-primary: #030712;
    --bg-secondary: #0a0f1a;
    --bg-card: rgba(10, 15, 26, 0.88);
    --bg-card-hover: rgba(15, 23, 42, 0.92);
    --border-glass: rgba(56, 189, 248, 0.08);
    --border-hover: rgba(56, 189, 248, 0.25);
    --text-primary: #e6edf3;
    --text-secondary: #6b7a8d;
    --text-dim: #3d4f63;
    --accent-cyan: #38bdf8;
    --accent-emerald: #34d399;
    --accent-rose: #f43f5e;
    --accent-amber: #fbbf24;
    --accent-violet: #a78bfa;
    --accent-blue: #60a5fa;
    --accent-pink: #f472b6;
    --glow-cyan: 0 0 30px rgba(56, 189, 248, 0.25);
    --glow-emerald: 0 0 30px rgba(52, 211, 153, 0.25);
    --glow-rose: 0 0 30px rgba(244, 63, 94, 0.35);
    --glow-violet: 0 0 30px rgba(167, 139, 250, 0.25);
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --radius-xl: 28px;
}

/* ── Animated Background ── */
.stApp {
    background: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif !important;
    background-image:
        radial-gradient(ellipse at 10% 20%, rgba(56,189,248,0.03) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 80%, rgba(167,139,250,0.03) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(52,211,153,0.02) 0%, transparent 60%) !important;
}

.block-container { padding-top: 0.5rem !important; padding-bottom: 0 !important; max-width: 100% !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(56,189,248,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(56,189,248,0.4); }

/* ── Animated Keyframes ── */
@keyframes pulse-glow { 0%,100%{opacity:1;box-shadow:0 0 8px rgba(52,211,153,0.3)} 50%{opacity:0.5;box-shadow:none} }
@keyframes scan-line { 0%{transform:translateY(-100%)} 100%{transform:translateY(100%)} }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }
@keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
@keyframes emergency-pulse { 0%,100%{opacity:1;border-color:rgba(244,63,94,0.5)} 50%{opacity:0.85;border-color:rgba(244,63,94,0.9)} }
@keyframes shake { 0%,100%{transform:rotate(0)} 25%{transform:rotate(-5deg)} 75%{transform:rotate(5deg)} }
@keyframes badge-pulse { 0%,100%{box-shadow:0 0 8px rgba(244,63,94,0.3)} 50%{box-shadow:0 0 20px rgba(244,63,94,0.6)} }
@keyframes gradient-shift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
@keyframes count-up { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
@keyframes border-flow {
    0% { border-image: linear-gradient(0deg, #38bdf8, #a78bfa, #34d399) 1; }
    33% { border-image: linear-gradient(120deg, #a78bfa, #34d399, #38bdf8) 1; }
    66% { border-image: linear-gradient(240deg, #34d399, #38bdf8, #a78bfa) 1; }
    100% { border-image: linear-gradient(360deg, #38bdf8, #a78bfa, #34d399) 1; }
}

/* ── Command Center Header ── */
.command-header {
    background: linear-gradient(135deg, rgba(10,15,26,0.97), rgba(15,23,42,0.95));
    border: 1px solid var(--border-glass);
    border-radius: var(--radius-lg);
    padding: 16px 28px;
    margin-bottom: 16px;
    backdrop-filter: blur(24px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 8px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
    position: relative;
    overflow: hidden;
}
.command-header::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 200%; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), var(--accent-violet), transparent);
    animation: shimmer 4s linear infinite;
}
.command-header .brand {
    font-family: 'Orbitron', sans-serif;
    font-size: 22px;
    font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #a78bfa, #34d399, #f472b6);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient-shift 6s ease infinite;
    letter-spacing: 1px;
}
.command-header .sub { color: var(--text-secondary); font-size: 11px; margin-top: 2px; font-weight: 400; letter-spacing: 0.3px; }
.status-pill {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.25);
    padding: 5px 14px; border-radius: 20px;
    font-size: 10px; font-weight: 700; color: var(--accent-emerald);
    text-transform: uppercase; letter-spacing: 1.2px;
}
.status-dot { width: 7px; height: 7px; background: var(--accent-emerald); border-radius: 50%; animation: pulse-glow 2s ease-in-out infinite; }
.inference-chip {
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    padding: 4px 12px; border-radius: 8px;
    background: rgba(167,139,250,0.1); border: 1px solid rgba(167,139,250,0.2);
    color: var(--accent-violet); font-weight: 600;
}

/* ── Glass Card v2 ── */
.glass-v2 {
    background: var(--bg-card);
    border: 1px solid var(--border-glass);
    border-radius: var(--radius-md);
    padding: 16px 18px;
    backdrop-filter: blur(20px);
    box-shadow: 0 4px 30px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.03);
    transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
}
.glass-v2::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(56,189,248,0.15), transparent);
}
.glass-v2:hover {
    border-color: var(--border-hover);
    box-shadow: 0 8px 40px rgba(0,0,0,0.5), var(--glow-cyan);
    transform: translateY(-2px);
}
.card-label {
    font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.8px;
    color: var(--text-dim); margin-bottom: 10px;
    display: flex; align-items: center; gap: 6px;
}

/* ── Metric Display ── */
.metric-hero { text-align: center; padding: 6px 0; }
.metric-hero .val {
    font-family: 'Orbitron', sans-serif; font-size: 32px; font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #34d399);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1; animation: count-up 0.6s ease-out;
}
.metric-hero .val.rose { background: linear-gradient(135deg, #f43f5e, #f472b6); -webkit-background-clip: text; }
.metric-hero .val.violet { background: linear-gradient(135deg, #a78bfa, #60a5fa); -webkit-background-clip: text; }
.metric-hero .val.amber { background: linear-gradient(135deg, #fbbf24, #f97316); -webkit-background-clip: text; }
.metric-hero .unit { font-size: 9px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 2px; margin-top: 6px; font-weight: 600; }

/* ── Camera Feed ── */
.cam-feed {
    background: var(--bg-card); border: 1px solid var(--border-glass); border-radius: var(--radius-md);
    overflow: hidden; backdrop-filter: blur(16px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.35); transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
    position: relative;
}
.cam-feed:hover { transform: translateY(-4px) scale(1.01); box-shadow: 0 16px 48px rgba(0,0,0,0.6), var(--glow-cyan); border-color: var(--border-hover); }
.cam-feed::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(180deg, transparent 60%, rgba(3,7,18,0.8) 100%);
    z-index: 1; pointer-events: none;
}
.cam-top { display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:rgba(0,0,0,0.5); border-bottom: 1px solid rgba(255,255,255,0.03); position:relative; z-index:2; }
.cam-id { font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; color:var(--accent-cyan); letter-spacing:0.5px; }
.cam-bottom { padding:10px 14px; position:relative; z-index:2; display:flex; justify-content:space-between; align-items:flex-end; }
.cam-count { font-family:'Orbitron',sans-serif; font-size:22px; font-weight:800; line-height:1; }
.cam-label { font-size:9px; text-transform:uppercase; letter-spacing:1.2px; color:var(--text-dim); margin-top:2px; font-weight:600; }
.cam-road { font-size:12px; font-weight:700; color:var(--text-primary); text-align:right; }
.cam-speed { font-family:'JetBrains Mono',monospace; font-size:10px; color:var(--text-secondary); }

/* ── Density Badges ── */
.density-badge { display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:16px; font-size:9px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase; }
.density-critical { background:rgba(244,63,94,0.12); border:1px solid rgba(244,63,94,0.35); color:var(--accent-rose); animation:badge-pulse 1.5s ease-in-out infinite; }
.density-moderate { background:rgba(251,191,36,0.1); border:1px solid rgba(251,191,36,0.3); color:var(--accent-amber); }
.density-stable { background:rgba(52,211,153,0.1); border:1px solid rgba(52,211,153,0.25); color:var(--accent-emerald); }

/* ── Live Tag ── */
.live-tag { display:inline-flex; align-items:center; gap:5px; font-family:'JetBrains Mono',monospace; font-size:9px; color:var(--accent-rose); font-weight:700; text-transform:uppercase; letter-spacing:1.5px; }
.live-dot-r { width:5px; height:5px; background:var(--accent-rose); border-radius:50%; animation:pulse-glow 1s infinite; }

/* ── Emergency Alert ── */
.emg-alert {
    background: linear-gradient(135deg, rgba(127,29,29,0.5), rgba(153,27,27,0.3));
    border: 2px solid rgba(244,63,94,0.5); border-radius: var(--radius-md);
    padding: 16px 20px; animation: emergency-pulse 1.5s ease-in-out infinite;
    box-shadow: 0 0 40px rgba(244,63,94,0.2); display:flex; align-items:center; gap:14px;
}
.emg-alert .emg-icon { font-size:28px; animation:shake 0.5s ease-in-out infinite; }
.emg-alert .emg-title { font-weight:800; font-size:14px; color:#fca5a5; letter-spacing:0.5px; }
.emg-alert .emg-sub { font-size:11px; color:rgba(252,165,165,0.65); margin-top:3px; }

/* ── Phase Timeline ── */
.phase-bar { display:flex; gap:3px; margin-top:8px; height:32px; border-radius:6px; overflow:hidden; }
.phase-segment {
    display:flex; align-items:center; justify-content:center;
    font-family:'JetBrains Mono',monospace; font-size:9px; font-weight:700;
    border-radius:4px; transition: all 0.3s ease; position:relative;
    overflow: hidden;
}
.phase-segment.active::before {
    content:''; position:absolute; top:0; left:0; bottom:0; width:100%;
    background: linear-gradient(90deg, rgba(255,255,255,0.1), transparent);
    animation: scan-line 2s linear infinite;
}

/* ── Progress Ring ── */
.ring-container { position:relative; width:80px; height:80px; margin:0 auto; }

/* ── Log Console v2 ── */
.log-v2 {
    background: rgba(3,7,18,0.7); border: 1px solid rgba(56,189,248,0.06); border-radius: 10px;
    padding: 12px 16px; font-family:'JetBrains Mono',monospace; font-size:10px;
    color: var(--text-dim); max-height: 200px; overflow-y: auto; line-height:1.9;
}
.log-v2 .ts { color:rgba(56,189,248,0.35); }
.log-v2 .info { color:var(--accent-cyan); }
.log-v2 .warn { color:var(--accent-amber); }
.log-v2 .ok { color:var(--accent-emerald); }
.log-v2 .err { color:var(--accent-rose); }
.log-v2 .vio { color:var(--accent-violet); }

/* ── Section Title ── */
.sec-title {
    font-size: 13px; font-weight: 800; color: var(--text-primary);
    margin-bottom: 12px; display:flex; align-items:center; gap:8px; letter-spacing:-0.2px;
}

/* ── Mini Stat Row ── */
.stat-row { display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }
.stat-row:last-child { border-bottom:none; }
.stat-key { font-size:11px; color:var(--text-secondary); }
.stat-val { font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:600; color:var(--text-primary); }

/* ── Tabs Override ── */
.stTabs [data-baseweb="tab-list"] { gap:2px; background:rgba(3,7,18,0.6); padding:3px; border-radius:12px; border:1px solid var(--border-glass); }
.stTabs [data-baseweb="tab"] { border-radius:10px; padding:8px 18px; color:var(--text-secondary)!important; font-weight:600; font-size:12px; transition:all 0.3s ease; }
.stTabs [aria-selected="true"] { background:rgba(56,189,248,0.12)!important; color:var(--accent-cyan)!important; box-shadow:var(--glow-cyan); }

/* ── Button Override ── */
.stButton > button {
    background: linear-gradient(135deg, rgba(56,189,248,0.12), rgba(167,139,250,0.12)) !important;
    border: 1px solid rgba(56,189,248,0.2) !important;
    color: var(--accent-cyan) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.8px;
    padding: 8px 20px !important;
    transition: all 0.4s cubic-bezier(0.4,0,0.2,1) !important;
    text-transform: uppercase;
    font-size: 11px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(56,189,248,0.22), rgba(167,139,250,0.22)) !important;
    border-color: rgba(56,189,248,0.45) !important;
    box-shadow: var(--glow-cyan), 0 4px 20px rgba(0,0,0,0.3) !important;
    transform: translateY(-2px);
}

/* ── Metric Override ── */
div[data-testid="stMetric"] {
    background: var(--bg-card); border: 1px solid var(--border-glass); border-radius: 12px; padding: 14px;
}
div[data-testid="stMetric"] label { color: var(--text-dim) !important; font-size: 10px !important; text-transform: uppercase; letter-spacing: 1.5px; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-family: 'Orbitron', sans-serif !important; color: var(--text-primary) !important; }

/* ── Expander ── */
div[data-testid="stExpander"] { background: var(--bg-card)!important; border: 1px solid var(--border-glass)!important; border-radius: 12px!important; }

/* ── Select / Dropdown ── */
div[data-baseweb="select"] > div { background: var(--bg-card) !important; border-color: var(--border-glass) !important; border-radius: 10px !important; }

/* ── Toggle ──*/
div[data-testid="stToggle"] label span { color: var(--text-secondary) !important; }

/* ── Dividers ── */
hr { border-color: rgba(56,189,248,0.05) !important; margin: 12px 0 !important; }

/* hide branding */
#MainMenu, footer, header { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }

/* ── Vehicle Type Pills ── */
.vtype-pill {
    display:inline-flex; align-items:center; gap:4px;
    padding:2px 8px; border-radius:10px; font-size:9px; font-weight:700;
    background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06);
    color:var(--text-secondary);
}

/* ── AQI Indicator ── */
.aqi-bar { height:4px; border-radius:2px; background:rgba(255,255,255,0.05); overflow:hidden; margin-top:6px; }
.aqi-fill { height:100%; border-radius:2px; transition:width 0.8s ease; }

/* ── Network Health Dots ── */
.health-dot { width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:6px; }
.health-ok { background:var(--accent-emerald); box-shadow:0 0 6px rgba(52,211,153,0.5); }
.health-warn { background:var(--accent-amber); box-shadow:0 0 6px rgba(251,191,36,0.5); }
.health-crit { background:var(--accent-rose); box-shadow:0 0 6px rgba(244,63,94,0.5); }
</style>
"""
