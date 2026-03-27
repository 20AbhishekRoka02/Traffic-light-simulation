import traci
import random

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SUMO_CONFIG     = "simulation.sumocfg"

EMERGENCY_TYPES = {"ambulance", "firebrigade"}
GREEN_DISTANCE  = 150
RESTORE_DELAY   = 10

MANUAL_TLS_ID   = "cluster_1870091900_6689054518_6689054519_6689054520_#2more"

# spawn config (increase traffic near TLS)
SPAWN_RADIUS     = 1500
SPAWN_INTERVAL   = 5
CARS_PER_BURST   = 5
VTYPE_ID         = "car"
DEPART_SPEED     = "max"

# traffic thresholds
LOW_TRAFFIC_MAX    = 5
MEDIUM_TRAFFIC_MAX = 15

GREEN_LOW    = 5
GREEN_MEDIUM = 10
GREEN_HIGH   = 15


# ─── MANUAL TLS CYCLE ─────────────────────────────────────────────────────────
MANUAL_TLS_CYCLE = [
    ("rGGrrrrrrrrGGrrrrrr", 27),
    ("ryyrrrrrrrryyrrrrrr", 6),
    ("GrrgGrrrrrGrrgGrrrr", 6),
    ("yrryyrrrrryrryyrrrr", 6),
    ("rrrrrGGGrrrrrrrGGrr", 27),
    ("rrrrryyyrrrrrrryyrr", 6),
    ("rrrrrrrrGGrrrrrrrGG", 6),
    ("rrrrrrrryyrrrrrrryy", 6),
]


# ─── STATE ────────────────────────────────────────────────────────────────────
tls_overrides       = {}
tls_restore_timers  = {}

manual_phase_index   = 0
manual_phase_elapsed = 0.0
manual_tls_active    = True

spawn_counter   = 0
last_spawn_time = 0


# ─── TRAFFIC DENSITY ──────────────────────────────────────────────────────────
def get_traffic_level(tls_id):

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

    if "G" in state:
        return get_traffic_level(MANUAL_TLS_ID)

    return default_duration


# ─── SPAWN VEHICLES ───────────────────────────────────────────────────────────
def get_edges_near_tls(tls_id):

    try:
        controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)

        edges = list({
            lane.split("_")[0]
            for lane in controlled_lanes
            if not lane.startswith(":")
        })

        print(f"Found {len(edges)} connected edges")

        return edges

    except:
        return []


def get_random_destination(exclude_edges):

    all_edges = [
        e for e in traci.edge.getIDList()
        if not e.startswith(":") and e not in exclude_edges
    ]

    return random.choice(all_edges) if all_edges else None


def spawn_car(spawn_edges, car_id):

    depart_edge = random.choice(spawn_edges)

    dest_edge = get_random_destination(spawn_edges)

    if dest_edge is None:
        return False

    route_id = f"route_spawned_{car_id}"

    veh_id = f"spawned_car_{car_id}"

    try:

        traci.route.add(route_id, [depart_edge, dest_edge])

        traci.vehicle.add(
            vehID       = veh_id,
            routeID     = route_id,
            typeID      = VTYPE_ID,
            depart      = "now",
            departLane  = "best",
            departSpeed = DEPART_SPEED
        )

        return True

    except:

        return False


def step_spawning(current_time):

    global spawn_counter, last_spawn_time

    if current_time - last_spawn_time >= SPAWN_INTERVAL:

        last_spawn_time = current_time

        spawn_edges = get_edges_near_tls(MANUAL_TLS_ID)

        for _ in range(CARS_PER_BURST):

            spawn_car(spawn_edges, spawn_counter)

            spawn_counter += 1


# ─── GREEN CORRIDOR ───────────────────────────────────────────────────────────
def get_upcoming_tls(vehicle_id, lookahead=GREEN_DISTANCE):

    upcoming = []

    try:

        next_tls = traci.vehicle.getNextTLS(vehicle_id)

        for tls in next_tls:

            tls_id, _, distance, _ = tls

            if distance <= lookahead:

                upcoming.append((tls_id, distance))

    except:

        pass

    return upcoming


def force_green(tls_id):

    global manual_tls_active

    if tls_id in tls_overrides:
        return

    try:

        phase   = traci.trafficlight.getPhase(tls_id)

        program = traci.trafficlight.getProgram(tls_id)

        tls_overrides[tls_id] = {

            "phase": phase,

            "program": program
        }

        links = len(traci.trafficlight.getControlledLinks(tls_id))

        traci.trafficlight.setRedYellowGreenState(

            tls_id,

            "G" * links
        )

        if tls_id == MANUAL_TLS_ID:

            manual_tls_active = False

    except:

        pass


def restore_tls(tls_id):

    global manual_tls_active

    if tls_id not in tls_overrides:
        return

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


# ─── MANUAL TLS ───────────────────────────────────────────────────────────────
def step_manual_tls(step_length):

    global manual_phase_index, manual_phase_elapsed

    if not manual_tls_active:
        return

    state, default_duration = MANUAL_TLS_CYCLE[manual_phase_index]

    duration = dynamic_duration(state, default_duration)

    manual_phase_elapsed += step_length

    traci.trafficlight.setRedYellowGreenState(

        MANUAL_TLS_ID,

        state
    )

    if manual_phase_elapsed >= duration:

        manual_phase_elapsed = 0

        manual_phase_index = (

            manual_phase_index + 1

        ) % len(MANUAL_TLS_CYCLE)

        print(

            f"Phase {manual_phase_index}"

            f" duration={duration}s"
        )


# ─── EMERGENCY VEHICLES ───────────────────────────────────────────────────────
def get_emergency_vehicles():

    vehicles = []

    for vid in traci.vehicle.getIDList():

        if traci.vehicle.getTypeID(vid) in EMERGENCY_TYPES:

            vehicles.append(vid)

    return vehicles


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def run():

    traci.start([

        "sumo-gui",

        "-c",

        SUMO_CONFIG,

        "--start",

        "--quit-on-end"

    ])

    step_length = traci.simulation.getDeltaT()

    while traci.simulation.getMinExpectedNumber() > 0:

        traci.simulationStep()

        time_now = traci.simulation.getTime()

        step_spawning(time_now)

        needed_tls = set()

        for vid in get_emergency_vehicles():

            for tls_id, _ in get_upcoming_tls(vid):

                force_green(tls_id)

                needed_tls.add(tls_id)

        for tls_id in list(tls_overrides.keys()):

            if tls_id not in needed_tls:

                restore_tls(tls_id)

        step_manual_tls(step_length)

    traci.close()


if __name__ == "__main__":

    run()