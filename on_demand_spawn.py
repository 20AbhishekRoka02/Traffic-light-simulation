import traci
import random
import threading

# ───────────── CONFIG ─────────────

SUMO_CONFIG = "simulation.sumocfg"

SIMULATION_END = 100000

SPAWN_INTERVAL = 3
CARS_PER_BURST = 2

VTYPE_ID = "car"

# edges around TLS
EDGES = {

    "U": "709276138#1",
    "D": "537797266#4",
    "L": "359757123",
    "R": "-537797267#1"
}

# valid routes through intersection
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

TRAFFIC_WEIGHTS = {

    "709276138#1": 0.25,
    "537797266#4": 0.25,
    "359757123": 0.25,
    "-537797267#1": 0.25
}

# ───────────── STATE ─────────────

spawn_queue = []

vehicle_counter = 0

# ───────────── HELPERS ─────────────

def choose_random_edge():

    edges = list(TRAFFIC_WEIGHTS.keys())
    weights = list(TRAFFIC_WEIGHTS.values())

    return random.choices(edges, weights=weights, k=1)[0]


def choose_destination(from_edge):

    return random.choice(VALID_CONNECTIONS[from_edge])


def spawn_vehicle(from_edge):

    global vehicle_counter

    dest_edge = choose_destination(from_edge)

    route_id = f"route_{vehicle_counter}"
    veh_id = f"car_{vehicle_counter}"

    vehicle_counter += 1   # increment immediately

    try:

        # ensure route exists between edges
        route = traci.simulation.findRoute(from_edge, dest_edge)

        if len(route.edges) == 0:
            print(f"⚠ no connection {from_edge} → {dest_edge}")
            return

        traci.route.add(route_id, route.edges)

        traci.vehicle.add(

            vehID=veh_id,
            routeID=route_id,
            typeID=VTYPE_ID,

            depart="now",
            departLane="best",
            departSpeed="max"
        )

        print(f"🚗 {veh_id}: {from_edge} → {dest_edge}")

    except Exception as e:

        print("spawn error:", e)


# ───────────── USER INPUT THREAD ─────────────

def user_input_loop():

    print("\nInteractive control ready:")
    print("L 3 → spawn 3 cars from LEFT")
    print("R 2 → spawn 2 cars from RIGHT")
    print("U 1 → spawn 1 car from UP")
    print("D 5 → spawn 5 cars from DOWN")
    print("type 'exit' to stop\n")

    while True:

        cmd = input()

        if cmd.lower() == "exit":

            spawn_queue.append(("EXIT", 0))
            break

        try:

            direction, count = cmd.split()

            direction = direction.upper()

            if direction in EDGES:

                spawn_queue.append((direction, int(count)))

            else:

                print("invalid direction")

        except:

            print("format example: L 3")


# ───────────── MAIN ─────────────

def run():

    traci.start(["sumo-gui", "-c", SUMO_CONFIG])

    input_thread = threading.Thread(target=user_input_loop)

    input_thread.daemon = True
    input_thread.start()

    last_spawn_time = 0

    print("\nSimulation running...\n")

    while traci.simulation.getTime() < SIMULATION_END:

        traci.simulationStep()

        current_time = traci.simulation.getTime()

        # normal background traffic
        if current_time - last_spawn_time >= SPAWN_INTERVAL:

            last_spawn_time = current_time

            for _ in range(CARS_PER_BURST):

                edge = choose_random_edge()
                spawn_vehicle(edge)

        # handle user commands
        while spawn_queue:

            direction, count = spawn_queue.pop(0)

            if direction == "EXIT":

                traci.close()
                print("simulation ended")
                return

            edge = EDGES[direction]

            print(f"\nManual spawn: {count} cars from {direction}")

            for _ in range(count):

                spawn_vehicle(edge)


    traci.close()


if __name__ == "__main__":

    run()