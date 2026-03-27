import traci
import traci.constants as tc

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SUMO_CONFIG      = "simulation.sumocfg"
EMERGENCY_TYPES  = {"ambulance", "firebrigade"}
GREEN_DISTANCE   = 150
RESTORE_DELAY    = 10

# ─── MANUAL TLS CONFIG ────────────────────────────────────────────────────────
MANUAL_TLS_ID    = "cluster_267196276_6666318646_6666318659_6666328407_#2more"   # ← your TLS ID

# Fixed yellow phases — never change these durations
YELLOW_DURATION  = 6

# Green time bounds (seconds)
MIN_GREEN        = 5
MAX_GREEN        = 15
BASE_GREEN       = 10   # fallback when no vehicles detected

# Detection range: how far back (meters) to count vehicles on approach lanes
DETECTION_RANGE  = 100

# Phase definitions — pair each green phase with its yellow phase
# Format: (green_state, yellow_state, approach_edges)
# approach_edges: list of edge IDs feeding into this phase's green links
# Leave approach_edges=[] to auto-detect from controlled lanes
PHASE_GROUPS = [
    {
        "green_state":  "rGGrrrrrrrrGGrrrrrr",
        "yellow_state": "ryyrrrrrrrryyrrrrrr",
        "label":        "Phase 0 — Main green",
        "approach_edges": []   # ← fill in or leave empty for auto-detect
    },
    {
        "green_state":  "GrrgGrrrrrGrrgGrrrr",
        "yellow_state": "yrryyrrrrryrryyrrrr",
        "label":        "Phase 2 — Left turns",
        "approach_edges": []
    },
    {
        "green_state":  "rrrrrGGGrrrrrrrGGrr",
        "yellow_state": "rrrrryyyrrrrrrryyrr",
        "label":        "Phase 4 — Secondary green",
        "approach_edges": []
    },
    {
        "green_state":  "rrrrrrrrGGrrrrrrrGG",
        "yellow_state": "rrrrrrrryyrrrrrrryy",
        "label":        "Phase 6 — Tertiary green",
        "approach_edges": []
    },
]

# ─── STATE TRACKING ───────────────────────────────────────────────────────────
tls_overrides        = {}
tls_restore_timers   = {}
manual_tls_active    = True

# Adaptive cycle state
current_phase_group  = 0       # index into PHASE_GROUPS
current_sub_phase    = "green" # "green" or "yellow"
phase_elapsed        = 0.0
current_green_time   = BASE_GREEN

# Cache: phase group index -> list of approach lane IDs (auto-detected)
approach_lanes_cache = {}

# ─── LANE AUTO-DETECTION ──────────────────────────────────────────────────────
def get_approach_lanes(phase_index):
    """
    Auto-detect incoming lanes for a phase group by reading
    controlled links where the green state has 'G' or 'g'.
    """
    if phase_index in approach_lanes_cache:
        return approach_lanes_cache[phase_index]

    group      = PHASE_GROUPS[phase_index]
    green_state = group["green_state"]

    # If user manually specified edges, convert to lanes
    if group["approach_edges"]:
        lanes = []
        for edge in group["approach_edges"]:
            try:
                lane_count = traci.edge.getLaneNumber(edge)
                for i in range(lane_count):
                    lanes.append(f"{edge}_{i}")
            except traci.TraCIException:
                pass
        approach_lanes_cache[phase_index] = lanes
        return lanes

    # Auto-detect: find controlled links where state is G or g
    try:
        controlled = traci.trafficlight.getControlledLinks(MANUAL_TLS_ID)
        lanes = set()
        for i, link_list in enumerate(controlled):
            if i < len(green_state) and green_state[i] in ("G", "g"):
                for link in link_list:
                    if link:
                        incoming_lane = link[0]  # (incoming, outgoing, via)
                        lanes.add(incoming_lane)
        result = list(lanes)
        approach_lanes_cache[phase_index] = result
        return result
    except traci.TraCIException:
        return []

# ─── VEHICLE COUNTING ─────────────────────────────────────────────────────────
def count_vehicles_on_lanes(lanes):
    """Count vehicles within DETECTION_RANGE meters of junction on given lanes."""
    total = 0
    for lane_id in lanes:
        try:
            vehicles = traci.lane.getLastStepVehicleIDs(lane_id)
            lane_len = traci.lane.getLength(lane_id)
            for vid in vehicles:
                try:
                    pos = traci.vehicle.getLanePosition(vid)
                    # Only count vehicles in last DETECTION_RANGE meters
                    if pos >= lane_len - DETECTION_RANGE:
                        total += 1
                except traci.TraCIException:
                    pass
        except traci.TraCIException:
            pass
    return total

def get_all_phase_demands():
    """Return vehicle counts for all phase groups."""
    demands = []
    for i in range(len(PHASE_GROUPS)):
        lanes  = get_approach_lanes(i)
        count  = count_vehicles_on_lanes(lanes)
        demands.append(count)
    return demands

# ─── ADAPTIVE GREEN TIME CALCULATION ─────────────────────────────────────────
def calculate_green_time(phase_index, demands):
    """
    Allocate green time proportional to this phase's demand
    relative to total demand. Clamp to [MIN_GREEN, MAX_GREEN].
    """
    total_demand = sum(demands)

    if total_demand == 0:
        return BASE_GREEN   # no vehicles anywhere — use base timing

    phase_demand = demands[phase_index]
    # Proportional share of total cycle green time
    total_green_budget = len(PHASE_GROUPS) * BASE_GREEN
    allocated = (phase_demand / total_demand) * total_green_budget

    # Clamp
    result = max(MIN_GREEN, min(MAX_GREEN, round(allocated)))
    return result

# ─── ADAPTIVE TLS STEP ────────────────────────────────────────────────────────
def step_manual_tls(step_length):
    """Advance adaptive TLS cycle by one simulation step."""
    global current_phase_group, current_sub_phase
    global phase_elapsed, current_green_time
    global manual_tls_active

    if not manual_tls_active:
        return  # green corridor in control

    group = PHASE_GROUPS[current_phase_group]

    # Apply current state
    try:
        if current_sub_phase == "green":
            traci.trafficlight.setRedYellowGreenState(
                MANUAL_TLS_ID, group["green_state"])
        else:
            traci.trafficlight.setRedYellowGreenState(
                MANUAL_TLS_ID, group["yellow_state"])
    except traci.TraCIException:
        return

    phase_elapsed += step_length

    # ── Transition logic ──────────────────────────────────────────────────────
    if current_sub_phase == "green" and phase_elapsed >= current_green_time:
        # Green done → switch to yellow
        current_sub_phase = "yellow"
        phase_elapsed     = 0.0
        print(f"  🟡 [{traci.simulation.getTime():.1f}s] "
              f"{group['label']} → YELLOW ({YELLOW_DURATION}s)")

    elif current_sub_phase == "yellow" and phase_elapsed >= YELLOW_DURATION:
        # Yellow done → advance to next phase group
        current_sub_phase   = "yellow"
        phase_elapsed       = 0.0
        current_phase_group = (current_phase_group + 1) % len(PHASE_GROUPS)

        # ── Calculate green time for upcoming phase based on demand ───────────
        demands            = get_all_phase_demands()
        current_green_time = calculate_green_time(current_phase_group, demands)
        current_sub_phase  = "green"

        next_group = PHASE_GROUPS[current_phase_group]
        print(f"  🚦 [{traci.simulation.getTime():.1f}s] "
              f"→ {next_group['label']} | "
              f"demand={demands[current_phase_group]} vehicles | "
              f"green={current_green_time}s | "
              f"all demands={demands}")

# ─── GREEN CORRIDOR ───────────────────────────────────────────────────────────
def get_upcoming_tls(vehicle_id, lookahead=GREEN_DISTANCE):
    upcoming = []
    try:
        next_tls = traci.vehicle.getNextTLS(vehicle_id)
        for tls in next_tls:
            tls_id, _, distance, _ = tls
            if distance <= lookahead:
                upcoming.append((tls_id, distance))
    except traci.TraCIException:
        pass
    return upcoming

def force_green(tls_id):
    global manual_tls_active
    if tls_id in tls_overrides:
        return
    try:
        tls_overrides[tls_id] = {
            "phase":   traci.trafficlight.getPhase(tls_id),
            "program": traci.trafficlight.getProgram(tls_id),
            "time":    traci.simulation.getTime()
        }
        num_links   = len(traci.trafficlight.getControlledLinks(tls_id))
        green_state = "G" * num_links
        traci.trafficlight.setRedYellowGreenState(tls_id, green_state)
        if tls_id == MANUAL_TLS_ID:
            manual_tls_active = False
            print(f"  ⏸  Manual control PAUSED — green corridor active")
        print(f"  🟢 GREEN CORRIDOR: '{tls_id}' → ALL GREEN ({num_links} links)")
    except traci.TraCIException as e:
        print(f"  ⚠ Could not override '{tls_id}': {e}")

def restore_tls(tls_id):
    global manual_tls_active
    if tls_id not in tls_overrides:
        return
    try:
        info = tls_overrides.pop(tls_id)
        traci.trafficlight.setProgram(tls_id, info["program"])
        traci.trafficlight.setPhase(tls_id,   info["phase"])
        if tls_id == MANUAL_TLS_ID:
            manual_tls_active = True
            print(f"  ▶  Manual control RESUMED for '{tls_id}'")
        print(f"  🔴 RESTORED: '{tls_id}' back to normal")
    except traci.TraCIException as e:
        print(f"  ⚠ Could not restore '{tls_id}': {e}")

def get_emergency_vehicles():
    emergency = []
    for vid in traci.vehicle.getIDList():
        try:
            if traci.vehicle.getTypeID(vid) in EMERGENCY_TYPES:
                emergency.append(vid)
        except traci.TraCIException:
            pass
    return emergency

# ─── VALIDATION ───────────────────────────────────────────────────────────────
def validate_manual_tls():
    try:
        num_links = len(traci.trafficlight.getControlledLinks(MANUAL_TLS_ID))
        print(f"  TLS '{MANUAL_TLS_ID}' has {num_links} controlled links")
        ok = True
        for i, group in enumerate(PHASE_GROUPS):
            for key in ("green_state", "yellow_state"):
                state = group[key]
                if len(state) != num_links:
                    print(f"  ❌ Phase group {i} '{key}' = '{state}' "
                          f"has {len(state)} chars, expected {num_links}")
                    ok = False
                else:
                    print(f"  ✅ Phase group {i} '{key}' length OK")
        return ok
    except traci.TraCIException as e:
        print(f"  ❌ TLS validation failed: {e}")
        return False

# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
def run():
    sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG, "--start", "--quit-on-end"]
    traci.start(sumo_cmd)

    step_length = traci.simulation.getDeltaT()

    print("=" * 60)
    print("  ADAPTIVE TLS + GREEN CORRIDOR started")
    print(f"  TLS              : '{MANUAL_TLS_ID}'")
    print(f"  Emergency types  : {EMERGENCY_TYPES}")
    print(f"  Green corridor   : {GREEN_DISTANCE}m lookahead")
    print(f"  Green time range : {MIN_GREEN}s – {MAX_GREEN}s")
    print(f"  Detection range  : {DETECTION_RANGE}m")
    print("=" * 60)

    if not validate_manual_tls():
        print("\n  ❌ Fix phase state strings before running.")
        traci.close()
        return

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        current_time     = traci.simulation.getTime()
        emergency_vehs   = get_emergency_vehicles()
        currently_needed = set()

        # ── Green corridor ────────────────────────────────────────────────────
        for vid in emergency_vehs:
            for tls_id, distance in get_upcoming_tls(vid, GREEN_DISTANCE):
                print(f"  🚨 [{current_time:.1f}s] {vid} → "
                      f"TLS '{tls_id}' ({distance:.1f}m)")
                force_green(tls_id)
                currently_needed.add(tls_id)

        # ── Restore TLS no longer needed ──────────────────────────────────────
        for tls_id in set(tls_overrides.keys()) - currently_needed:
            if tls_id not in tls_restore_timers:
                tls_restore_timers[tls_id] = current_time
            elif current_time - tls_restore_timers[tls_id] >= RESTORE_DELAY:
                restore_tls(tls_id)
                tls_restore_timers.pop(tls_id, None)

        for tls_id in currently_needed:
            tls_restore_timers.pop(tls_id, None)

        # ── Adaptive TLS step ─────────────────────────────────────────────────
        step_manual_tls(step_length)

    traci.close()
    print("=" * 60)
    print("  Simulation ended.")
    print("=" * 60)

if __name__ == "__main__":
    run()
