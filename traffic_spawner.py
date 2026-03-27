import traci
import random

# ───────────────── CONFIG ─────────────────

SUMO_CONFIG = "simulation.sumocfg"

SIMULATION_END = 3600
SPAWN_INTERVAL = 2
CARS_PER_BURST = 3

VTYPE_ID = "car"

# Incoming edges around your TLS
INCOMING_EDGES = {

    "UP": "709276138#1",
    "DOWN": "537797266#4",
    "LEFT": "359757123",
    "RIGHT": "-537797267#1"
}

# Allowed traffic movements (valid routes)
VALID_CONNECTIONS = {

    "709276138#1": [
        "359757123",
        "-537797267#1",
        "537797266#4"
    ],

    "537797266#4": [
        "359757123",
        "-537797267#1",
        "709276138#1"
    ],

    "359757123": [
        "709276138#1",
        "537797266#4"
    ],

    "-537797267#1": [
        "709276138#1",
        "537797266#4"
    ]
}

# Traffic density control
# increase weight = more traffic from that road
TRAFFIC_WEIGHTS = {

    "709276138#1": 0.25,   # UP
    "537797266#4": 0.25,   # DOWN
    "359757123": 0.25,     # LEFT
    "-537797267#1": 0.25   # RIGHT
}

# ───────────────── HELPERS ─────────────────

def choose_depart_edge():

    edges = list(TRAFFIC_WEIGHTS.keys())
    weights = list(TRAFFIC_WEIGHTS.values())

    return random.choices(edges, weights=weights, k=1)[0]


def choose_destination(depart_edge):

    possible_destinations = VALID_CONNECTIONS[depart_edge]

    return random.choice(possible_destinations)


def spawn_vehicle(counter):

    depart_edge = choose_depart_edge()
    dest_edge = choose_destination(depart_edge)

    route_id = f"route_{counter}"
    veh_id = f"car_{counter}"

    try:

        traci.route.add(route_id, [depart_edge, dest_edge])

        traci.vehicle.add(

            vehID=veh_id,
            routeID=route_id,
            typeID=VTYPE_ID,

            depart="now",
            departLane="best",
            departSpeed="max"
        )

        print(f"🚗 {veh_id}: {depart_edge} → {dest_edge}")

    except Exception as e:

        print(f"⚠ spawn error: {e}")


# ───────────────── MAIN ─────────────────

def run():

    traci.start(["sumo-gui", "-c", SUMO_CONFIG])

    counter = 0
    last_spawn_time = 0

    print("\nSMART TRAFFIC DEMO STARTED")
    print("Spawning vehicles around TLS\n")

    while traci.simulation.getTime() < SIMULATION_END:

        traci.simulationStep()

        current_time = traci.simulation.getTime()

        # spawn vehicles periodically
        if current_time - last_spawn_time >= SPAWN_INTERVAL:

            last_spawn_time = current_time

            for _ in range(CARS_PER_BURST):

                spawn_vehicle(counter)
                counter += 1

    traci.close()

    print("\nSimulation ended")


if __name__ == "__main__":

    run()