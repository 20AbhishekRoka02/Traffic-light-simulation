import traci
import json
import os

# ─── CONFIG ─────────────────────────────────────────────

SUMO_CONFIG = "simulation.sumocfg"

JSON_FILE = "traffic_density.json"

EMERGENCY_TYPES = {"ambulance", "firebrigade"}

GREEN_DISTANCE = 150
RESTORE_DELAY = 10

YELLOW_DURATION = 4
MIN_GREEN = 5
MAX_GREEN = 15
BASE_GREEN = 10

# all TLS ids
TLS_IDS = [

"1869716862",
"249783302",
"249783316",
"267075196",
"432874005",
"5792664575",
"6122832366",
"6223295222",
"6223295223",
"6234228016",
"6234228017",
"939091071",

"GS_249783308",
"GS_cluster_11301690339_11301690340_3661513065_3661513066",
"GS_cluster_12865950987_13087429776_9860744486",
"GS_cluster_1668978741_458640643",
"GS_cluster_1869716959_450631313",

"cluster_11726690852_12896534974_13018550234_562591570",
"cluster_12105998311_12105998312_12105998314_249791204_#2more",
"cluster_12319493498_12319493500",

"cluster_13506319762_13506319763_13506319764_13506319765_#7more",

"cluster_1870091900_6689054518_6689054519_6689054520_#2more",

"cluster_249783293_5681450581",

"cluster_267196276_6666318646_6666318659_6666328407_#2more",

"joinedS_11187714088_12044574565_5792664573_6234226367_#4more",

"joinedS_3947530960_9798119678",

"joinedS_6720393130_6720393131"
]

# store overrides
tls_overrides = {}
tls_restore_timers = {}

# per tls timing state
tls_phase_index = {}
tls_sub_phase = {}
tls_elapsed = {}

# ─── AI DENSITY ─────────────────────────────────────────

def read_density():

    if not os.path.exists(JSON_FILE):

        return [0,0,0,0]

    try:

        with open(JSON_FILE) as f:

            d = json.load(f)

        return list(d.values())[:4]

    except:

        return [0,0,0,0]

def compute_green_time(density):

    if density == 0:

        return BASE_GREEN

    return max(MIN_GREEN, min(MAX_GREEN, density*3))

# ─── GREEN CORRIDOR ─────────────────────────────────────

def get_upcoming_tls(vehicle_id):

    upcoming = []

    try:

        tls_list = traci.vehicle.getNextTLS(vehicle_id)

        for tls in tls_list:

            tls_id, _, distance, _ = tls

            if distance <= GREEN_DISTANCE:

                upcoming.append(tls_id)

    except:

        pass

    return upcoming

def force_green(tls_id):

    if tls_id in tls_overrides:

        return

    try:

        tls_overrides[tls_id] = {

            "program":

            traci.trafficlight.getProgram(tls_id),

            "phase":

            traci.trafficlight.getPhase(tls_id),

            "time":

            traci.simulation.getTime()

        }

        links = traci.trafficlight.getControlledLinks(tls_id)

        green_state = "G"*len(links)

        traci.trafficlight.setRedYellowGreenState(

            tls_id,

            green_state
        )

        print("🚑 GREEN CORRIDOR →", tls_id)

    except:

        pass

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

        print("🔄 restored", tls_id)

    except:

        pass

def get_emergency_vehicles():

    result = []

    for vid in traci.vehicle.getIDList():

        try:

            if traci.vehicle.getTypeID(vid) in EMERGENCY_TYPES:

                result.append(vid)

        except:

            pass

    return result

# ─── AI SIGNAL CONTROL ──────────────────────────────────

def adaptive_step(tls_id, density, step):

    if tls_id in tls_overrides:

        return

    if tls_id not in tls_phase_index:

        tls_phase_index[tls_id] = 0

        tls_sub_phase[tls_id] = "green"

        tls_elapsed[tls_id] = 0

    tls_elapsed[tls_id] += step

    green_time = compute_green_time(density)

    try:

        logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]

        phases = logic.phases

        phase_index = tls_phase_index[tls_id]

        sub_phase = tls_sub_phase[tls_id]

        if sub_phase == "green":

            traci.trafficlight.setRedYellowGreenState(

                tls_id,

                phases[phase_index].state
            )

            if tls_elapsed[tls_id] >= green_time:

                tls_sub_phase[tls_id] = "yellow"

                tls_elapsed[tls_id] = 0

        else:

            next_phase = (phase_index+1)%len(phases)

            traci.trafficlight.setRedYellowGreenState(

                tls_id,

                phases[next_phase].state
            )

            tls_phase_index[tls_id] = next_phase

            tls_sub_phase[tls_id] = "green"

            tls_elapsed[tls_id] = 0

    except:

        pass

# ─── MAIN ───────────────────────────────────────────────

def run():
    traci.init(port=37071)
    traci.setOrder(1)
    # traci.start([

    #     "sumo-gui",

    #     "-c",

    #     SUMO_CONFIG,

    #     "--start"

    # ])

    step = traci.simulation.getDeltaT()

    print("\nSMART CITY CONTROL ACTIVE\n")

    while traci.simulation.getMinExpectedNumber() > 0:

        traci.simulationStep()

        now = traci.simulation.getTime()

        densities = read_density()

        emergency_tls = set()

        # PRIORITY 1
        for vid in get_emergency_vehicles():

            for tls_id in get_upcoming_tls(vid):

                force_green(tls_id)

                emergency_tls.add(tls_id)

        # restore
        for tls_id in set(tls_overrides.keys()) - emergency_tls:

            if tls_id not in tls_restore_timers:

                tls_restore_timers[tls_id] = now

            elif now - tls_restore_timers[tls_id] > RESTORE_DELAY:

                restore_tls(tls_id)

                tls_restore_timers.pop(tls_id, None)

        # PRIORITY 2
        for i, tls_id in enumerate(TLS_IDS):

            density = densities[i%4]

            adaptive_step(

                tls_id,

                density,

                step
            )

    traci.close()

# ─── START ──────────────────────────────────────────────

if __name__ == "__main__":

    run()