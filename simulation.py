import traci
import json
import os

# ─── CONFIG ───────────────────────────────────────────────

SUMO_CONFIG = "simulation.sumocfg"

JSON_FILE = "traffic_density.json"

EMERGENCY_TYPES = {"ambulance", "firebrigade"}

GREEN_DISTANCE = 150     # meters ahead of TLS
RESTORE_DELAY  = 10      # seconds after emergency passes

MANUAL_TLS_ID = "cluster_267196276_6666318646_6666318659_6666328407_#2more"

# timing settings
YELLOW_DURATION = 4
MIN_GREEN = 5
MAX_GREEN = 15
BASE_GREEN = 10

# phase definitions (4 directions)
PHASES = [
    {
        "green":  "rGGrrrrrrrrGGrrrrrr",
        "yellow": "ryyrrrrrrrryyrrrrrr",
        "label": "North-South"
    },
    {
        "green":  "GrrgGrrrrrGrrgGrrrr",
        "yellow": "yrryyrrrrryrryyrrrr",
        "label": "East-West"
    },
    {
        "green":  "rrrrrGGGrrrrrrrGGrr",
        "yellow": "rrrrryyyrrrrrrryyrr",
        "label": "Turns A"
    },
    {
        "green":  "rrrrrrrrGGrrrrrrrGG",
        "yellow": "rrrrrrrryyrrrrrrryy",
        "label": "Turns B"
    }
]

# ─── STATE ─────────────────────────────────────────────────

tls_overrides = {}
tls_restore_timers = {}

phase_index = 0
sub_phase = "green"
elapsed = 0

# ─── AI DENSITY ───────────────────────────────────────────

def read_density():

    if not os.path.exists(JSON_FILE):
        return [0,0,0,0]

    try:

        with open(JSON_FILE) as f:

            d = json.load(f)

        return [
            d["North"],
            d["South"],
            d["East"],
            d["West"]
        ]

    except:

        return [0,0,0,0]

def compute_green_times():

    counts = read_density()

    total = sum(counts)

    if total == 0:
        return [BASE_GREEN]*4

    budget = BASE_GREEN * 4

    times = []

    for c in counts:

        t = (c/total)*budget

        t = max(MIN_GREEN, min(MAX_GREEN, round(t)))

        times.append(t)

    return times

# ─── GREEN CORRIDOR ───────────────────────────────────────

def get_upcoming_tls(vehicle_id):

    upcoming = []

    try:

        next_tls = traci.vehicle.getNextTLS(vehicle_id)

        for tls in next_tls:

            tls_id, _, distance, _ = tls

            if distance <= GREEN_DISTANCE:

                upcoming.append((tls_id, distance))

    except:

        pass

    return upcoming

def force_green(tls_id):

    if tls_id in tls_overrides:
        return

    try:

        tls_overrides[tls_id] = {

            "phase": traci.trafficlight.getPhase(tls_id),

            "program": traci.trafficlight.getProgram(tls_id),

            "time": traci.simulation.getTime()

        }

        controlled_links = traci.trafficlight.getControlledLinks(tls_id)

        green_state = "G"*len(controlled_links)

        traci.trafficlight.setRedYellowGreenState(

            tls_id,

            green_state
        )

        print(f"🟢 GREEN CORRIDOR ACTIVE → {tls_id}")

    except Exception as e:

        print("override error", e)

def restore_tls(tls_id):

    if tls_id not in tls_overrides:
        return

    try:

        info = tls_overrides.pop(tls_id)

        traci.trafficlight.setProgram(

            tls_id,

            info["program"]
        )

        traci.trafficlight.setPhase(

            tls_id,

            info["phase"]
        )

        print(f"🔴 RESTORED NORMAL → {tls_id}")

    except Exception as e:

        print("restore error", e)

def get_emergency_vehicles():

    vehicles = []

    for vid in traci.vehicle.getIDList():

        try:

            if traci.vehicle.getTypeID(vid) in EMERGENCY_TYPES:

                vehicles.append(vid)

        except:

            pass

    return vehicles

# ─── ADAPTIVE TLS ─────────────────────────────────────────

def adaptive_signal_step(step):

    global phase_index, sub_phase, elapsed

    green_times = compute_green_times()

    phase = PHASES[phase_index]

    elapsed += step

    if sub_phase == "green":

        traci.trafficlight.setRedYellowGreenState(

            MANUAL_TLS_ID,

            phase["green"]
        )

        if elapsed >= green_times[phase_index]:

            sub_phase = "yellow"

            elapsed = 0

            print("🟡", phase["label"])

    else:

        traci.trafficlight.setRedYellowGreenState(

            MANUAL_TLS_ID,

            phase["yellow"]
        )

        if elapsed >= YELLOW_DURATION:

            sub_phase = "green"

            elapsed = 0

            phase_index = (phase_index+1)%4

            print(
                "🚦",
                PHASES[phase_index]["label"],
                "green:",
                green_times[phase_index]
            )

# ─── MAIN LOOP ────────────────────────────────────────────

def run():

    sumo_cmd = [

        "sumo-gui",

        "-c",

        SUMO_CONFIG,

        "--start",

        "--quit-on-end"
    ]

    traci.start(sumo_cmd)
    
    # create emergency vehicle type
    # traci.vehicletype.copy("car", "ambulance")

    # # add route (replace edges)
    # traci.route.add(
    #     "ambulance_route",
    #     ["edge_1", "edge_2", "edge_3"]
    # )

    # # spawn vehicle
    # traci.vehicle.add(
    #     "ambulance_test",
    #     "ambulance_route",
    #     typeID="ambulance",
    #     depart="5"
    # )

    # print("🚑 Test ambulance added")

    step_length = traci.simulation.getDeltaT()

    print("\nSMART TRAFFIC STARTED")

    while traci.simulation.getMinExpectedNumber() > 0:

        traci.simulationStep()

        time_now = traci.simulation.getTime()

        emergency_vehicles = get_emergency_vehicles()

        currently_needed = set()

        # ─── PRIORITY 1: GREEN CORRIDOR ───────────────

        for vid in emergency_vehicles:

            for tls_id, dist in get_upcoming_tls(vid):

                print(

                    f"🚑 {vid} approaching {tls_id}"

                    f" distance {dist:.1f}"

                )

                force_green(tls_id)

                currently_needed.add(tls_id)

        # restore signals after emergency passes

        for tls_id in set(tls_overrides.keys()) - currently_needed:

            if tls_id not in tls_restore_timers:

                tls_restore_timers[tls_id] = time_now

            elif time_now - tls_restore_timers[tls_id] > RESTORE_DELAY:

                restore_tls(tls_id)

                tls_restore_timers.pop(tls_id, None)

        for tls_id in currently_needed:

            tls_restore_timers.pop(tls_id, None)

        # ─── PRIORITY 2: AI TRAFFIC CONTROL ───────────

        if MANUAL_TLS_ID not in tls_overrides:

            adaptive_signal_step(step_length)

    traci.close()

    print("SIMULATION COMPLETE")

# ─── START ────────────────────────────────────────────────

if __name__ == "__main__":

    run()