import traci
import traci.constants as tc

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SUMO_CONFIG     = "simulation.sumocfg"
EMERGENCY_TYPES = {"ambulance", "firebrigade"}
GREEN_DISTANCE  = 150
RESTORE_DELAY   = 10

MANUAL_TLS_ID   = "cluster_1870091900_6689054518_6689054519_6689054520_#2more"

# base cycle (keep structure same)
MANUAL_TLS_CYCLE = [
    ("rGGrrrrrrrrGGrrrrrr", 27),
    ("ryyrrrrrrrryyrrrrrr",  6),
    ("GrrgGrrrrrGrrgGrrrr",  6),
    ("yrryyrrrrryrryyrrrr",  6),
    ("rrrrrGGGrrrrrrrGGrr", 27),
    ("rrrrryyyrrrrrrryyrr",  6),
    ("rrrrrrrrGGrrrrrrrGG",  6),
    ("rrrrrrrryyrrrrrrryy",  6),
]

# traffic thresholds
LOW_TRAFFIC_MAX    = 5
MEDIUM_TRAFFIC_MAX = 15

GREEN_LOW    = 5
GREEN_MEDIUM = 10
GREEN_HIGH   = 15


# ─── STATE TRACKING ───────────────────────────────────────────────────────────
tls_overrides       = {}
tls_restore_timers  = {}

manual_phase_index    = 0
manual_phase_elapsed  = 0.0
manual_tls_active     = True


# ─── TRAFFIC DENSITY FUNCTION ─────────────────────────────────────────────────
def get_traffic_level(tls_id):
    """
    Count vehicles waiting near TLS.
    Returns duration for green phase.
    """
    lanes = traci.trafficlight.getControlledLanes(tls_id)

    vehicle_count = 0
    for lane in lanes:
        vehicle_count += traci.lane.getLastStepVehicleNumber(lane)

    if vehicle_count <= LOW_TRAFFIC_MAX:
        return GREEN_LOW
    elif vehicle_count <= MEDIUM_TRAFFIC_MAX:
        return GREEN_MEDIUM
    else:
        return GREEN_HIGH


def dynamic_duration(state, default_duration):
    """
    Adjust duration ONLY for green phases.
    Yellow/red phases remain unchanged.
    """
    if "G" in state:
        return get_traffic_level(MANUAL_TLS_ID)
    return default_duration


# ─── GREEN CORRIDOR FUNCTIONS (UNCHANGED) ─────────────────────────────────────
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

        if tls_id == MANUAL_TLS_ID:
            manual_tls_active = False
            print(f"  ⏸ Manual paused for '{tls_id}'")

        print(f"  🟢 GREEN CORRIDOR ACTIVE on '{tls_id}'")

    except traci.TraCIException as e:
        print(e)


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
            print(f"  ▶ Manual resumed for '{tls_id}'")

        print(f"  🔴 RESTORED '{tls_id}'")

    except traci.TraCIException as e:
        print(e)


# ─── MODIFIED MANUAL TLS CONTROL ──────────────────────────────────────────────
def step_manual_tls(step_length):
    global manual_phase_index, manual_phase_elapsed

    if not manual_tls_active:
        return

    state, default_duration = MANUAL_TLS_CYCLE[manual_phase_index]

    # NEW: adjust timing dynamically
    duration = dynamic_duration(state, default_duration)

    manual_phase_elapsed += step_length

    try:
        traci.trafficlight.setRedYellowGreenState(MANUAL_TLS_ID, state)
    except traci.TraCIException:
        return

    if manual_phase_elapsed >= duration:
        manual_phase_elapsed = 0.0
        manual_phase_index = (manual_phase_index + 1) % len(MANUAL_TLS_CYCLE)

        next_state, _ = MANUAL_TLS_CYCLE[manual_phase_index]

        print(
            f"🚦 Phase {manual_phase_index} | "
            f"Traffic-based duration = {duration}s"
        )


# ─── EMERGENCY VEHICLE DETECTION ──────────────────────────────────────────────
def get_emergency_vehicles():
    emergency = []

    for vid in traci.vehicle.getIDList():
        try:
            if traci.vehicle.getTypeID(vid) in EMERGENCY_TYPES:
                emergency.append(vid)
        except:
            pass

    return emergency


# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
def run():

    sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG, "--start", "--quit-on-end"]

    traci.start(sumo_cmd)

    step_length = traci.simulation.getDeltaT()

    print("SMART TRAFFIC CONTROL STARTED")

    while traci.simulation.getMinExpectedNumber() > 0:

        traci.simulationStep()

        current_time    = traci.simulation.getTime()
        emergency_vehs  = get_emergency_vehicles()

        currently_needed = set()

        # green corridor logic unchanged
        for vid in emergency_vehs:

            upcoming = get_upcoming_tls(vid, GREEN_DISTANCE)

            for tls_id, distance in upcoming:

                force_green(tls_id)

                currently_needed.add(tls_id)

        for tls_id in set(tls_overrides.keys()) - currently_needed:

            if tls_id not in tls_restore_timers:

                tls_restore_timers[tls_id] = current_time

            elif current_time - tls_restore_timers[tls_id] >= RESTORE_DELAY:

                restore_tls(tls_id)

                tls_restore_timers.pop(tls_id, None)

        for tls_id in currently_needed:

            tls_restore_timers.pop(tls_id, None)

        # manual smart timing
        step_manual_tls(step_length)

    traci.close()

    print("SIMULATION COMPLETE")


if __name__ == "__main__":
    run()