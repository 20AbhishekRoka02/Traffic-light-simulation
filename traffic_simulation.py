import traci
import traci.constants as tc
import random

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SUMO_CONFIG      = "simulation.sumocfg"

EMERGENCY_TYPES  = {"ambulance", "firebrigade"}
GREEN_DISTANCE   = 150
RESTORE_DELAY    = 10

MANUAL_TLS_ID    = "cluster_267196276_6666318646_6666318659_6666328407_#2more"

# Fixed yellow duration
YELLOW_DURATION  = 6

# Adaptive green timing bounds
MIN_GREEN        = 5
MAX_GREEN        = 15
BASE_GREEN       = 10

# vehicle detection distance before junction
DETECTION_RANGE  = 100


# ─── TRAFFIC GENERATION CONFIG ────────────────────────────────────────────────
SPAWN_INTERVAL   = 0.8       # faster traffic buildup
SIM_END          = 3600

EDGE_WEIGHTS = {
    "709276138#1": 5,     # HIGH density (UP)
    "537797266#4": 3,     # MEDIUM density (DOWN)
    "359757123":   1,     # LOW density (LEFT)
    "-537797267#1":1      # LOW density (RIGHT)
}

VTYPE_ID     = "car"
DEPART_SPEED = "max"


# ─── PHASE DEFINITIONS ────────────────────────────────────────────────────────
PHASE_GROUPS = [

    {
        "green_state":  "rGGrrrrrrrrGGrrrrrr",
        "yellow_state": "ryyrrrrrrrryyrrrrrr",
        "label":        "Main road"
    },

    {
        "green_state":  "GrrgGrrrrrGrrgGrrrr",
        "yellow_state": "yrryyrrrrryrryyrrrr",
        "label":        "Left turns"
    },

    {
        "green_state":  "rrrrrGGGrrrrrrrGGrr",
        "yellow_state": "rrrrryyyrrrrrrryyrr",
        "label":        "Secondary"
    },

    {
        "green_state":  "rrrrrrrrGGrrrrrrrGG",
        "yellow_state": "rrrrrrrryyrrrrrrryy",
        "label":        "Tertiary"
    },

]


# ─── STATE ────────────────────────────────────────────────────────────────────
tls_overrides        = {}
tls_restore_timers   = {}
manual_tls_active    = True

current_phase_group  = 0
current_sub_phase    = "green"
phase_elapsed        = 0
current_green_time   = BASE_GREEN

spawn_counter        = 0
last_spawn_time      = 0

approach_lanes_cache = {}


# ─── LANE DETECTION ───────────────────────────────────────────────────────────
def get_approach_lanes(phase_index):

    if phase_index in approach_lanes_cache:
        return approach_lanes_cache[phase_index]

    group       = PHASE_GROUPS[phase_index]
    green_state = group["green_state"]

    try:

        controlled = traci.trafficlight.getControlledLinks(MANUAL_TLS_ID)

        lanes = set()

        for i, links in enumerate(controlled):

            if i < len(green_state) and green_state[i] in ("G","g"):

                for link in links:

                    if link:

                        lanes.add(link[0])

        lanes = list(lanes)

        approach_lanes_cache[phase_index] = lanes

        return lanes

    except:

        return []


# ─── TRAFFIC DEMAND MEASUREMENT ───────────────────────────────────────────────
def count_vehicles_on_lanes(lanes):

    total = 0

    for lane_id in lanes:

        try:

            vehicles = traci.lane.getLastStepVehicleIDs(lane_id)

            lane_len = traci.lane.getLength(lane_id)

            for vid in vehicles:

                pos = traci.vehicle.getLanePosition(vid)

                if pos >= lane_len - DETECTION_RANGE:

                    total += 1

        except:

            pass

    return total


def get_all_phase_demands():

    demands = []

    for i in range(len(PHASE_GROUPS)):

        lanes  = get_approach_lanes(i)

        demand = count_vehicles_on_lanes(lanes)

        demands.append(demand)

    return demands


# ─── ADAPTIVE GREEN TIME ──────────────────────────────────────────────────────
def calculate_green_time(phase_index, demands):

    total_demand = sum(demands)

    if total_demand == 0:

        return BASE_GREEN

    phase_demand = demands[phase_index]

    total_budget = len(PHASE_GROUPS) * BASE_GREEN

    proportional = (phase_demand / total_demand) * total_budget

    return max(

        MIN_GREEN,

        min(MAX_GREEN, round(proportional))

    )


# ─── VEHICLE SPAWNING ─────────────────────────────────────────────────────────
def weighted_edge_choice():

    edges   = list(EDGE_WEIGHTS.keys())

    weights = list(EDGE_WEIGHTS.values())

    return random.choices(

        edges,

        weights = weights,

        k = 1

    )[0]


def get_random_destination(from_edge):

    all_edges = [

        e for e in traci.edge.getIDList()

        if not e.startswith(":") and e != from_edge

    ]

    return random.choice(all_edges)


def spawn_vehicle():

    global spawn_counter

    start_edge = weighted_edge_choice()

    dest_edge  = get_random_destination(start_edge)
    
    if not dest_edge:
        return

    route_id = f"r{spawn_counter}"

    veh_id   = f"v{spawn_counter}"

    try:
        route = traci.simulation.findRoute(start_edge, dest_edge)

        if len(route.edges) == 0:
            return

        traci.route.add(route_id, route.edges)

        traci.vehicle.add(

            vehID       = veh_id,

            routeID     = route_id,

            typeID      = VTYPE_ID,

            # depart      = "now",
            
            depart=str(traci.simulation.getTime() + random.uniform(0,1)),
            departLane  = "best",

            departSpeed = "max"

        )

        spawn_counter += 1

    except:

        pass


def step_spawning(current_time):

    global last_spawn_time

    if current_time - last_spawn_time >= SPAWN_INTERVAL:

        last_spawn_time = current_time
        # test
        # for _ in range(3):

        #     spawn_vehicle()
        spawn_vehicle()


# ─── ADAPTIVE TLS STEP ────────────────────────────────────────────────────────
def step_manual_tls(step_length):

    global current_phase_group
    global current_sub_phase
    global phase_elapsed
    global current_green_time

    if not manual_tls_active:

        return

    group = PHASE_GROUPS[current_phase_group]

    if current_sub_phase == "green":

        traci.trafficlight.setRedYellowGreenState(

            MANUAL_TLS_ID,

            group["green_state"]

        )

    else:

        traci.trafficlight.setRedYellowGreenState(

            MANUAL_TLS_ID,

            group["yellow_state"]

        )

    phase_elapsed += step_length


    # transition logic
    if current_sub_phase == "green" and phase_elapsed >= current_green_time:

        current_sub_phase = "yellow"

        phase_elapsed     = 0

        print(

            f"YELLOW → {group['label']}"

        )


    elif current_sub_phase == "yellow" and phase_elapsed >= YELLOW_DURATION:

        current_phase_group = (

            current_phase_group + 1

        ) % len(PHASE_GROUPS)


        demands = get_all_phase_demands()

        current_green_time = calculate_green_time(

            current_phase_group,

            demands

        )

        current_sub_phase = "green"

        phase_elapsed = 0

        print(

            f"GREEN → {PHASE_GROUPS[current_phase_group]['label']}"

            f" | demand={demands[current_phase_group]}"

            f" | time={current_green_time}"

            f" | all={demands}"

        )


# ─── GREEN CORRIDOR (UNCHANGED) ───────────────────────────────────────────────
def get_upcoming_tls(vehicle_id):

    upcoming = []

    try:

        tls_list = traci.vehicle.getNextTLS(vehicle_id)

        for tls in tls_list:

            tls_id, _, distance, _ = tls

            if distance <= GREEN_DISTANCE:

                upcoming.append((tls_id, distance))

    except:

        pass

    return upcoming


def force_green(tls_id):

    global manual_tls_active

    if tls_id in tls_overrides:

        return

    tls_overrides[tls_id] = {

        "phase":

        traci.trafficlight.getPhase(tls_id),

        "program":

        traci.trafficlight.getProgram(tls_id)

    }

    links = len(

        traci.trafficlight.getControlledLinks(tls_id)

    )

    traci.trafficlight.setRedYellowGreenState(

        tls_id,

        "G"*links

    )

    if tls_id == MANUAL_TLS_ID:

        manual_tls_active = False

        print("Green corridor active")


def restore_tls(tls_id):

    global manual_tls_active

    info = tls_overrides.pop(tls_id)

    traci.trafficlight.setProgram(

        tls_id,

        info["program"]

    )

    traci.trafficlight.setPhase(

        tls_id,

        info["phase"]

    )

    if tls_id == MANUAL_TLS_ID:

        manual_tls_active = True

        print("Green corridor cleared")


def get_emergency_vehicles():

    vehicles = []

    for vid in traci.vehicle.getIDList():

        if traci.vehicle.getTypeID(vid) in EMERGENCY_TYPES:

            vehicles.append(vid)

    return vehicles


# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
def run():

    traci.start([

        "sumo-gui",

        "-c",

        SUMO_CONFIG,
        
        "--step-length", "0.2"

        # "--start",

        # "--quit-on-end"

    ])

    step_length = traci.simulation.getDeltaT()

    print("Adaptive traffic control started")


    while traci.simulation.getMinExpectedNumber() > 0:

        traci.simulationStep()

        time_now = traci.simulation.getTime()


        # spawn traffic
        step_spawning(time_now)


        # green corridor check
        needed = set()

        for vid in get_emergency_vehicles():

            for tls_id, _ in get_upcoming_tls(vid):

                force_green(tls_id)

                needed.add(tls_id)


        for tls_id in list(tls_overrides.keys()):

            if tls_id not in needed:

                restore_tls(tls_id)


        # adaptive signal
        step_manual_tls(step_length)


    traci.close()

    print("Simulation ended")


if __name__ == "__main__":

    run()