"""
Configuration & Data Models for AI Traffic Vision Command v5.0
"""
import random
from datetime import datetime, timedelta

# ════════════════════════════════════════════════════════════════════
# JUNCTION DATABASE — Multi-Junction Support
# ════════════════════════════════════════════════════════════════════
JUNCTIONS = {
    "india_gate": {
        "name": "India Gate Circle",
        "coordinates": [28.6129, 77.2295],
        "city": "New Delhi",
        "status": "AI_ADAPTIVE_MODE",
        "zone": "Central Delhi",
        "priority": "HIGH",
        "cameras": [
            {"cam_id": 1, "road": "Rajpath", "image": "assets/rajpath_high.png",
             "count": 18, "density": "CRITICAL", "speed_avg": 12, "queue_length": 340,
             "vehicles": {"cars": 10, "trucks": 2, "bikes": 4, "buses": 2, "autos": 0}},
            {"cam_id": 2, "road": "KG Marg", "image": "assets/kg_low.png",
             "count": 3, "density": "STABLE", "speed_avg": 45, "queue_length": 60,
             "vehicles": {"cars": 2, "trucks": 0, "bikes": 1, "buses": 0, "autos": 0}},
            {"cam_id": 3, "road": "Akbar Rd", "image": "assets/akbar_med.png",
             "count": 7, "density": "MODERATE", "speed_avg": 28, "queue_length": 150,
             "vehicles": {"cars": 3, "trucks": 1, "bikes": 2, "buses": 0, "autos": 1}},
            {"cam_id": 4, "road": "Ashoka Rd", "image": "assets/ashoka_low.png",
             "count": 2, "density": "STABLE", "speed_avg": 52, "queue_length": 30,
             "vehicles": {"cars": 1, "trucks": 0, "bikes": 1, "buses": 0, "autos": 0}},
        ],
        "decision_engine": {
            "last_inference_ms": 42,
            "active_phase": "Phase 1 (North-South)",
            "allocated_time": 60,
            "model": "YOLOv8-n",
            "confidence": 0.94,
            "logic_reasoning": "High density on Rajpath detected via YOLOv8. Emergency priority: Off. Adaptive green wave enabled for N-S corridor.",
            "phase_queue": [
                {"name": "P1 — Rajpath (N-S)", "duration": 60, "status": "ACTIVE"},
                {"name": "P2 — KG Marg (E)", "duration": 30, "status": "QUEUED"},
                {"name": "P3 — Akbar Rd (W)", "duration": 35, "status": "QUEUED"},
                {"name": "P4 — Ashoka Rd (S)", "duration": 25, "status": "QUEUED"},
            ]
        },
        "emergency": {"ambulance_detected": False, "corridor_active": False, "target_lane": None},
        "environment": {"current_co2": 1450.8, "reduction": "22.4%", "aqi": 142, "noise_db": 72.5, "temp_c": 34.2},
        "network_health": {"uptime": "14h 23m", "fps": 24, "sumo_ver": "v1.18.0", "gpu_util": 67, "cpu_util": 43, "ram_gb": 6.2, "bandwidth_mbps": 84}
    },
    "connaught_place": {
        "name": "Connaught Place Circle",
        "coordinates": [28.6315, 77.2167],
        "city": "New Delhi",
        "status": "AI_ADAPTIVE_MODE",
        "zone": "Central Delhi",
        "priority": "HIGH",
        "cameras": [
            {"cam_id": 5, "road": "Barakhamba Rd", "image": "assets/rajpath_high.png",
             "count": 14, "density": "MODERATE", "speed_avg": 22, "queue_length": 220,
             "vehicles": {"cars": 8, "trucks": 1, "bikes": 3, "buses": 1, "autos": 1}},
            {"cam_id": 6, "road": "Janpath", "image": "assets/kg_low.png",
             "count": 22, "density": "CRITICAL", "speed_avg": 8, "queue_length": 410,
             "vehicles": {"cars": 12, "trucks": 3, "bikes": 4, "buses": 2, "autos": 1}},
            {"cam_id": 7, "road": "Parliament St", "image": "assets/akbar_med.png",
             "count": 5, "density": "STABLE", "speed_avg": 40, "queue_length": 80,
             "vehicles": {"cars": 3, "trucks": 0, "bikes": 1, "buses": 1, "autos": 0}},
            {"cam_id": 8, "road": "Tolstoy Marg", "image": "assets/ashoka_low.png",
             "count": 9, "density": "MODERATE", "speed_avg": 30, "queue_length": 170,
             "vehicles": {"cars": 5, "trucks": 1, "bikes": 2, "buses": 0, "autos": 1}},
        ],
        "decision_engine": {
            "last_inference_ms": 38,
            "active_phase": "Phase 2 (Janpath Priority)",
            "allocated_time": 55,
            "model": "YOLOv8-n",
            "confidence": 0.91,
            "logic_reasoning": "Critical density on Janpath. Extending green phase for E-W corridor. Pedestrian crossing demand high.",
            "phase_queue": [
                {"name": "P1 — Barakhamba (N)", "duration": 40, "status": "COMPLETED"},
                {"name": "P2 — Janpath (E-W)", "duration": 55, "status": "ACTIVE"},
                {"name": "P3 — Parliament (S)", "duration": 30, "status": "QUEUED"},
                {"name": "P4 — Tolstoy (W)", "duration": 35, "status": "QUEUED"},
            ]
        },
        "emergency": {"ambulance_detected": False, "corridor_active": False, "target_lane": None},
        "environment": {"current_co2": 1620.3, "reduction": "18.7%", "aqi": 168, "noise_db": 78.1, "temp_c": 35.0},
        "network_health": {"uptime": "22h 07m", "fps": 22, "sumo_ver": "v1.18.0", "gpu_util": 72, "cpu_util": 51, "ram_gb": 7.1, "bandwidth_mbps": 76}
    }
}


def generate_historical_data(hours=24):
    """Generate simulated historical traffic data."""
    now = datetime.now()
    data = []
    for i in range(hours * 4):  # every 15 min
        t = now - timedelta(minutes=15 * (hours * 4 - i))
        hour = t.hour
        # Realistic traffic pattern
        if 7 <= hour <= 10:
            base = random.randint(14, 22)
        elif 17 <= hour <= 20:
            base = random.randint(16, 24)
        elif 0 <= hour <= 5:
            base = random.randint(1, 4)
        else:
            base = random.randint(6, 14)
        data.append({
            "time": t.strftime("%H:%M"),
            "timestamp": t,
            "vehicles": base + random.randint(-2, 2),
            "co2": 1200 + base * 20 + random.uniform(-50, 50),
            "speed": max(5, 55 - base * 2 + random.randint(-5, 5)),
            "wait_time": max(5, base * 3 + random.randint(-10, 10)),
        })
    return data


def generate_predictions(hours=6):
    """Generate predictive analytics data."""
    now = datetime.now()
    data = []
    for i in range(hours * 4):
        t = now + timedelta(minutes=15 * i)
        hour = t.hour
        if 7 <= hour <= 10:
            base = random.randint(15, 20)
        elif 17 <= hour <= 20:
            base = random.randint(17, 22)
        elif 0 <= hour <= 5:
            base = random.randint(1, 3)
        else:
            base = random.randint(7, 13)
        data.append({
            "time": t.strftime("%H:%M"),
            "predicted": base,
            "upper": base + random.randint(2, 5),
            "lower": max(0, base - random.randint(2, 5)),
        })
    return data


DENSITY_MAP = {
    "CRITICAL": {"class": "density-critical", "color": "#f43f5e", "icon": "🔴"},
    "MODERATE": {"class": "density-moderate", "color": "#fbbf24", "icon": "🟡"},
    "STABLE": {"class": "density-stable", "color": "#34d399", "icon": "🟢"},
}
