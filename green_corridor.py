import traci
import traci.constants as tc
import subprocess
import sys
import os

# ─── CONFIG ───────────────────────────────────────────────
SUMO_CONFIG    = "simulation.sumocfg"
EMERGENCY_TYPES = {"ambulance", "firebrigade"}
GREEN_DISTANCE  = 150  # meters ahead to turn green
RESTORE_DELAY   = 10   # seconds after vehicle passes to restore phase

# ─── STATE TRACKING ───────────────────────────────────────
# tls_id -> {original_phase, override_time}
tls_overrides = {}
# tls_id -> countdown timer for restoration
tls_restore_timers = {}

def get_upcoming_tls(vehicle_id, lookahead=GREEN_DISTANCE):
    """Get traffic lights within lookahead distance on vehicle's route."""
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
    """Force all phases of a TLS to green."""
    if tls_id in tls_overrides:
        return  # already overridden

    try:
        current_phase = traci.trafficlight.getPhase(tls_id)
        current_program = traci.trafficlight.getProgram(tls_id)
        tls_overrides[tls_id] = {
            "phase":   current_phase,
            "program": current_program,
            "time":    traci.simulation.getTime()
        }

        # Build an all-green state string
        controlled_links = traci.trafficlight.getControlledLinks(tls_id)
        num_links = len(controlled_links)
        green_state = "G" * num_links

        # Set green for a long duration
        traci.trafficlight.setRedYellowGreenState(tls_id, green_state)
        print(f"  🟢 GREEN CORRIDOR: TLS '{tls_id}' forced GREEN "
              f"({num_links} links)")
    except traci.TraCIException as e:
        print(f"  ⚠ Could not override TLS '{tls_id}': {e}")

def restore_tls(tls_id):
    """Restore a TLS to its original program."""
    if tls_id not in tls_overrides:
        return
    try:
        info = tls_overrides.pop(tls_id)
        traci.trafficlight.setProgram(tls_id, info["program"])
        traci.trafficlight.setPhase(tls_id,   info["phase"])
        print(f"  🔴 RESTORED: TLS '{tls_id}' back to normal")
    except traci.TraCIException as e:
        print(f"  ⚠ Could not restore TLS '{tls_id}': {e}")

def get_emergency_vehicles():
    """Return list of currently active emergency vehicle IDs."""
    emergency = []
    for vid in traci.vehicle.getIDList():
        try:
            vtype = traci.vehicle.getTypeID(vid)
            if vtype in EMERGENCY_TYPES:
                emergency.append(vid)
        except traci.TraCIException:
            pass
    return emergency

def run():
    # Launch SUMO with TraCI
    sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG,
                "--start", "--quit-on-end"]
    traci.start(sumo_cmd)

    print("=" * 60)
    print("  GREEN CORRIDOR simulation started")
    print(f"  Monitoring types: {EMERGENCY_TYPES}")
    print(f"  Lookahead distance: {GREEN_DISTANCE}m")
    print("=" * 60)

    active_tls_per_vehicle = {}  # vid -> set of tls_ids currently green

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        current_time = traci.simulation.getTime()

        emergency_vehicles = get_emergency_vehicles()
        currently_needed = set()  # TLS IDs needed green right now

        for vid in emergency_vehicles:
            upcoming = get_upcoming_tls(vid, GREEN_DISTANCE)

            if upcoming:
                for tls_id, distance in upcoming:
                    print(f"  🚨 [{current_time:.1f}s] {vid} approaching "
                          f"TLS '{tls_id}' ({distance:.1f}m away)")
                    force_green(tls_id)
                    currently_needed.add(tls_id)

        # Restore TLS no longer needed by any emergency vehicle
        overridden_tls = set(tls_overrides.keys())
        for tls_id in overridden_tls - currently_needed:
            # Start restore timer
            if tls_id not in tls_restore_timers:
                tls_restore_timers[tls_id] = current_time
            elif current_time - tls_restore_timers[tls_id] >= RESTORE_DELAY:
                restore_tls(tls_id)
                tls_restore_timers.pop(tls_id, None)

        # Clean up timers for TLS back under emergency control
        for tls_id in currently_needed:
            tls_restore_timers.pop(tls_id, None)

    traci.close()
    print("=" * 60)
    print("  Simulation ended.")
    print("=" * 60)

if __name__ == "__main__":
    run()