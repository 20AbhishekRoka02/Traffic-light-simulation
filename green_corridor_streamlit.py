import traci
import traci.constants as tc

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SUMO_CONFIG     = "simulation.sumocfg"
EMERGENCY_TYPES = {"ambulance", "firebrigade"}
GREEN_DISTANCE  = 150   # meters ahead to activate green corridor
RESTORE_DELAY   = 10    # seconds after vehicle passes to restore phase

# ─── MANUAL TLS CONTROL CONFIG ────────────────────────────────────────────────
MANUAL_TLS_ID   = "cluster_1870091900_6689054518_6689054519_6689054520_#2more"   # ← Replace with your junction TLS ID

# Define your custom cycle for the junction
# Each entry: (state_string, duration_in_seconds)
# Get state strings from Step 2 above
MANUAL_TLS_CYCLE = [
    ("rGGrrrrrrrrGGrrrrrr", 27),  # Phase 0 — Main green
    ("ryyrrrrrrrryyrrrrrr",  6),  # Phase 1 — Yellow
    ("GrrgGrrrrrGrrgGrrrr",  6),  # Phase 2 — Left turns green
    ("yrryyrrrrryrryyrrrr",  6),  # Phase 3 — Yellow
    ("rrrrrGGGrrrrrrrGGrr", 27),  # Phase 4 — Secondary green
    ("rrrrryyyrrrrrrryyrr",  6),  # Phase 5 — Yellow
    ("rrrrrrrrGGrrrrrrrGG",  6),  # Phase 6 — Tertiary green
    ("rrrrrrrryyrrrrrrryy",  6),  # Phase 7 — Yellow
]

# ─── STATE TRACKING ───────────────────────────────────────────────────────────
tls_overrides       = {}   # tls_id -> {phase, program, time}
tls_restore_timers  = {}   # tls_id -> time when vehicle left range

# Manual TLS cycle tracking
manual_phase_index    = 0
manual_phase_elapsed  = 0.0
manual_tls_active     = True   # False when green corridor overrides it

# ─── GREEN CORRIDOR FUNCTIONS ─────────────────────────────────────────────────
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
    """Force all links of a TLS to green."""
    global manual_tls_active

    if tls_id in tls_overrides:
        return  # already overridden

    try:
        current_phase   = traci.trafficlight.getPhase(tls_id)
        current_program = traci.trafficlight.getProgram(tls_id)
        tls_overrides[tls_id] = {
            "phase":   current_phase,
            "program": current_program,
            "time":    traci.simulation.getTime()
        }

        num_links   = len(traci.trafficlight.getControlledLinks(tls_id))
        green_state = "G" * num_links
        traci.trafficlight.setRedYellowGreenState(tls_id, green_state)

        # Pause manual control if this is our manually controlled junction
        if tls_id == MANUAL_TLS_ID:
            manual_tls_active = False
            print(f"  ⏸  Manual control PAUSED for '{tls_id}' — green corridor active")

        print(f"  🟢 GREEN CORRIDOR: TLS '{tls_id}' forced GREEN ({num_links} links)")

    except traci.TraCIException as e:
        print(f"  ⚠ Could not override TLS '{tls_id}': {e}")

def restore_tls(tls_id):
    """Restore TLS to its state before green corridor override."""
    global manual_tls_active

    if tls_id not in tls_overrides:
        return
    try:
        info = tls_overrides.pop(tls_id)
        traci.trafficlight.setProgram(tls_id, info["program"])
        traci.trafficlight.setPhase(tls_id,   info["phase"])

        # Resume manual control if this is our junction
        if tls_id == MANUAL_TLS_ID:
            manual_tls_active = True
            print(f"  ▶  Manual control RESUMED for '{tls_id}'")

        print(f"  🔴 RESTORED: TLS '{tls_id}' back to normal")

    except traci.TraCIException as e:
        print(f"  ⚠ Could not restore TLS '{tls_id}': {e}")

# ─── MANUAL TLS CONTROL ───────────────────────────────────────────────────────
def step_manual_tls(step_length):
    """
    Advance the manual TLS cycle by one simulation step.
    Only runs when green corridor is NOT overriding this junction.
    """
    global manual_phase_index, manual_phase_elapsed

    if not manual_tls_active:
        return  # green corridor is in control — do nothing

    manual_phase_elapsed += step_length
    state, duration = MANUAL_TLS_CYCLE[manual_phase_index]

    # Apply current phase state
    try:
        traci.trafficlight.setRedYellowGreenState(MANUAL_TLS_ID, state)
    except traci.TraCIException:
        return

    # Advance to next phase when duration expires
    if manual_phase_elapsed >= duration:
        manual_phase_elapsed = 0.0
        manual_phase_index = (manual_phase_index + 1) % len(MANUAL_TLS_CYCLE)
        next_state, _ = MANUAL_TLS_CYCLE[manual_phase_index]
        print(f"  🚦 Manual TLS '{MANUAL_TLS_ID}' → Phase {manual_phase_index}: {next_state}")

# ─── EMERGENCY VEHICLE DETECTION ──────────────────────────────────────────────
def get_emergency_vehicles():
    emergency = []
    for vid in traci.vehicle.getIDList():
        try:
            if traci.vehicle.getTypeID(vid) in EMERGENCY_TYPES:
                emergency.append(vid)
        except traci.TraCIException:
            pass
    return emergency

# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
def run():
    global manual_phase_index, manual_phase_elapsed

    traci.init(port=37071)
    traci.setOrder(1)  # main controller

    step_length = traci.simulation.getDeltaT()  # respects your step-length config

    print("=" * 60)
    print("  GREEN CORRIDOR + MANUAL TLS CONTROL started")
    print(f"  Manually controlling TLS : '{MANUAL_TLS_ID}'")
    print(f"  Emergency types          : {EMERGENCY_TYPES}")
    print(f"  Green corridor distance  : {GREEN_DISTANCE}m")
    print(f"  Restore delay            : {RESTORE_DELAY}s")
    print("=" * 60)

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        current_time    = traci.simulation.getTime()
        emergency_vehs  = get_emergency_vehicles()
        currently_needed = set()

        # ── Green corridor logic ──────────────────────────────────────────────
        for vid in emergency_vehs:
            upcoming = get_upcoming_tls(vid, GREEN_DISTANCE)
            for tls_id, distance in upcoming:
                print(f"  🚨 [{current_time:.1f}s] {vid} approaching "
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

        # Clean up restore timers for TLS still under emergency control
        for tls_id in currently_needed:
            tls_restore_timers.pop(tls_id, None)

        # ── Manual TLS control ────────────────────────────────────────────────
        step_manual_tls(step_length)

    traci.close()
    print("=" * 60)
    print("  Simulation ended.")
    print("=" * 60)

if __name__ == "__main__":
    run()
