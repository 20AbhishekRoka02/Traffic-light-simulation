import traci
import random

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SUMO_CONFIG      = "simulation.sumocfg"
TARGET_TLS_ID    = "cluster_267196276_6666318646_6666318659_6666328407_#2more"       # ← TLS ID to spawn cars around
SPAWN_RADIUS     = 1500                 # metres — edges within this distance
SPAWN_INTERVAL   = 5                   # seconds between each spawn burst
CARS_PER_BURST   = 5                   # how many cars to spawn each burst
VTYPE_ID         = "car"               # must match vtypes.add.xml
DEPART_SPEED     = "max"               # "max", "0", or a number in m/s
SIMULATION_END   = 3600                # seconds

# ─── STATE ────────────────────────────────────────────────────────────────────
spawn_counter    = 0
last_spawn_time  = 0.0

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def get_junction_position(tls_id):
    """Get (x, y) coordinates of the junction controlled by this TLS."""
    # TLS ID often matches junction ID directly
    try:
        pos = traci.junction.getPosition(tls_id)
        return pos
    except traci.TraCIException:
        pass

    # Fallback: try controlled links to find junction
    try:
        links = traci.trafficlight.getControlledLinks(tls_id)
        for link_list in links:
            for link in link_list:
                if link:
                    via_lane = link[2]           # internal via lane
                    edge_id  = via_lane.split("_")[0]
                    # Internal edges start with ':'
                    junction_id = edge_id.lstrip(":")
                    pos = traci.junction.getPosition(junction_id)
                    return pos
    except traci.TraCIException:
        pass

    return None

# def get_edges_near_tls(tls_id, radius=SPAWN_RADIUS):
#     """
#     Return list of regular (non-internal) edges whose midpoint
#     is within `radius` metres of the target TLS junction.
#     """
#     junction_pos = get_junction_position(tls_id)
#     if junction_pos is None:
#         print(f"  ❌ Could not find position for TLS '{tls_id}'")
#         return []

#     jx, jy = junction_pos
#     nearby  = []

#     for edge_id in traci.edge.getIDList():
#         if edge_id.startswith(":"):
#             continue   # skip internal junction edges

#         try:
#             # Use lane 0 midpoint as edge position approximation
#             lane_id  = f"{edge_id}_0"
#             lane_len = traci.lane.getLength(lane_id)
#             # Sample position at midpoint of the lane
#             mid_pos  = traci.simulation.convert2D(lane_id, lane_len / 2)
#             dx = mid_pos[0] - jx
#             dy = mid_pos[1] - jy
#             dist = (dx**2 + dy**2) ** 0.5

#             if dist <= radius:
#                 nearby.append((edge_id, dist))

#         except traci.TraCIException:
#             continue

#     # Sort by distance — closest edges first
#     nearby.sort(key=lambda x: x[1])
#     edges = [e[0] for e in nearby]
#     print(f"  📍 Found {len(edges)} edges within {radius}m of TLS '{tls_id}'")
#     return edges

def get_edges_near_tls(tls_id, radius=SPAWN_RADIUS):

    try:
        controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)

        edges = list({
            lane.split("_")[0]
            for lane in controlled_lanes
            if not lane.startswith(":")
        })

        print(f"  📍 Found {len(edges)} edges connected to TLS '{tls_id}'")
        return edges

    except traci.TraCIException as e:
        print(f"❌ TLS error: {e}")
        return []
    
def get_random_destination(exclude_edges):
    """Pick a random non-internal edge as destination."""
    all_edges = [e for e in traci.edge.getIDList()
                 if not e.startswith(":") and e not in exclude_edges]
    return random.choice(all_edges) if all_edges else None

def spawn_car(spawn_edges, car_id):
    """Spawn a single car on a random nearby edge heading to a random destination."""
    if not spawn_edges:
        return False

    depart_edge = random.choice(spawn_edges)
    dest_edge   = get_random_destination(spawn_edges)

    if dest_edge is None:
        return False

    route_id = f"route_spawned_{car_id}"
    veh_id   = f"spawned_car_{car_id}"

    try:
        # Add a route from depart to destination
        traci.route.add(route_id, [depart_edge, dest_edge])

        # Add the vehicle
        traci.vehicle.add(
            vehID       = veh_id,
            routeID     = route_id,
            typeID      = VTYPE_ID,
            depart      = "now",
            departLane  = "best",
            departSpeed = DEPART_SPEED
        )

        print(f"  🚗 Spawned '{veh_id}' | {depart_edge} → {dest_edge}")
        return True

    except traci.TraCIException as e:
        print(f"  ⚠ Could not spawn car {car_id}: {e}")
        return False

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def run():
    global spawn_counter, last_spawn_time

    sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG, "--start", "--quit-on-end"]
    traci.start(sumo_cmd)

    step_length = traci.simulation.getDeltaT()

    print("=" * 60)
    print(f"  CAR SPAWNER around TLS '{TARGET_TLS_ID}'")
    print(f"  Spawn radius   : {SPAWN_RADIUS}m")
    print(f"  Cars per burst : {CARS_PER_BURST}")
    print(f"  Spawn interval : {SPAWN_INTERVAL}s")
    print("=" * 60)

    # Pre-compute nearby edges once at start
    traci.simulationStep()
    spawn_edges = get_edges_near_tls(TARGET_TLS_ID, SPAWN_RADIUS)

    if not spawn_edges:
        print("  ❌ No nearby edges found. Check TLS ID or increase SPAWN_RADIUS.")
        traci.close()
        return

    print(f"  Nearby edges: {spawn_edges[:5]} ... (showing first 5)")

    while traci.simulation.getTime() < SIMULATION_END:
        traci.simulationStep()
        current_time = traci.simulation.getTime()

        # Spawn burst every SPAWN_INTERVAL seconds
        if current_time - last_spawn_time >= SPAWN_INTERVAL:
            last_spawn_time = current_time
            print(f"\n  ⏱ [{current_time:.1f}s] Spawning {CARS_PER_BURST} cars...")
            for _ in range(CARS_PER_BURST):
                spawn_car(spawn_edges, spawn_counter)
                spawn_counter += 1

    traci.close()
    print("=" * 60)
    print(f"  Done. Total cars spawned: {spawn_counter}")
    print("=" * 60)

if __name__ == "__main__":
    run()