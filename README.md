# 🚦 SUMO City Traffic Simulation — Rajiv Chowk

A real-world city traffic simulation built with [Eclipse SUMO](https://sumo.dlr.de/), featuring multi-modal traffic (cars, bikes, buses, emergency vehicles), adaptive traffic signal control, and a green corridor system for emergency vehicles — all controlled via TraCI.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Simulation](#running-the-simulation)
- [Understanding the Python Scripts](#understanding-the-python-scripts)
- [Modifying the Simulation](#modifying-the-simulation)
- [SUMO-GUI Tips](#sumo-gui-tips)
- [Branching & Contribution Guidelines](#branching--contribution-guidelines)

---

## Prerequisites

Before cloning, make sure you have the following installed:

- **SUMO** (≥ 1.20.0) — [Download here](https://sumo.dlr.de/docs/Downloads.php)
- **Python** (≥ 3.9)
- `SUMO_HOME` environment variable must be set

To verify:

```bash
echo $SUMO_HOME          # Linux/macOS
echo %SUMO_HOME%         # Windows CMD
echo $env:SUMO_HOME      # Windows PowerShell
```

If not set, add it:

```bash
# Linux/macOS — add to ~/.bashrc or ~/.zshrc
export SUMO_HOME=/path/to/sumo

# Windows — set in System Environment Variables
# e.g. C:\Program Files (x86)\Eclipse\Sumo
```

---

## Project Structure

```
.
├── 📄 README.md
├── 📄 requirements.txt
│
├── ── Simulation Config ──────────────────────────────────────
├── simulation.sumocfg            # Main SUMO config — entry point
├── osm.net.xml                   # Road network (generated from OSM)
├── verified.net.xml              # Verified copy of the network
├── rajiv_chowk.osm               # Raw OpenStreetMap source file
├── viewsettings.xml              # GUI display settings (real-world mode)
│
├── ── Vehicle Definitions ────────────────────────────────────
├── vtypes.add.xml                # Vehicle type definitions (shapes, colors, classes)
│
├── ── Trip & Route Files ─────────────────────────────────────
├── trips_cars.xml                # Random trip origins/destinations for cars
├── trips_bikes.xml               # Random trip origins/destinations for bikes
├── trips_buses.xml               # Random trip origins/destinations for buses
├── trips_ambulance.xml           # Random trip origins/destinations for ambulances
├── trips_firebrigade.xml         # Random trip origins/destinations for fire brigade
├── routes_cars.rou.xml           # Routed paths for cars
├── routes_bikes.rou.xml          # Routed paths for bikes
├── routes_buses.rou.xml          # Routed paths for buses
├── routes_ambulance.rou.xml      # Routed paths for ambulances
├── routes_firebrigade.rou.xml    # Routed paths for fire brigade
│
├── ── Output Files ───────────────────────────────────────────
├── summary.xml                   # Simulation summary statistics
├── all_tls_ids.txt               # All traffic light IDs in the network
│
└── ── Python Scripts ─────────────────────────────────────────
    ├── green_corridor.py                  # Core: green corridor for emergency vehicles
    ├── green_corridor_test_tls.py         # Green corridor + manual/adaptive TLS control
    ├── test_tls.py                        # Utility: list all TLS IDs in the network
    └── number_of_links_in_given_tls.py   # Utility: inspect links & phases for a TLS ID
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

> The main dependency is `traci`, which ships with SUMO. Make sure `$SUMO_HOME/tools` is on your `PYTHONPATH`:

```bash
# Linux/macOS
export PYTHONPATH=$SUMO_HOME/tools:$PYTHONPATH

# Windows CMD
set PYTHONPATH=%SUMO_HOME%\tools;%PYTHONPATH%

# Windows PowerShell
$env:PYTHONPATH = "$env:SUMO_HOME\tools;" + $env:PYTHONPATH
```

---

## Running the Simulation

### Option A — Basic simulation (no TraCI)

Opens SUMO-GUI with all vehicle types and viewsettings:

```bash
sumo-gui -c simulation.sumocfg
```

### Option B — Green corridor only (emergency vehicle priority)

Launches SUMO-GUI and activates automatic green corridor for ambulances and fire brigade:

```bash
python green_corridor.py
```

### Option C — Green corridor + Adaptive TLS control

Launches SUMO-GUI with full adaptive signal control on the target junction AND green corridor override:

```bash
python green_corridor_test_tls.py
```

### Option D — Green corridor + Adaptive TLS control + StreamLit Display (recommended)

Launches SUMO-GUI with full adaptive signal control on the target junction AND green corridor override ans shares snapshots to streamlit:

```bash
sumo-gui -c simulation.sumocfg --remote-port 37071 --num-clients 2 --start
```
Now in a separate terminal run :

```bash
python green_corridor_streamlit.py
```

Now in another separate terminal run :

```bash
streamlit run app.py
```

This should open a streamlit window in your browser (If not, visit http://localhost:8501)
and click on "Start Simulation" button in the sidebar


---

## Understanding the Python Scripts

### `green_corridor.py`

Controls traffic lights network-wide when an emergency vehicle is nearby.

**How it works:**
- Every simulation step, it checks all active vehicles
- If a vehicle of type `ambulance` or `firebrigade` is within **150 metres** of a traffic light on its route, that TLS is forced fully green
- After the vehicle passes and **10 seconds** elapse, the TLS is restored to its original phase and program

**Key config values at the top of the file:**

| Variable | Default | Description |
|---|---|---|
| `EMERGENCY_TYPES` | `{"ambulance", "firebrigade"}` | vType IDs that trigger the corridor |
| `GREEN_DISTANCE` | `150` | Metres ahead to activate green |
| `RESTORE_DELAY` | `10` | Seconds to wait before restoring TLS |

---

### `green_corridor_test_tls.py`

Built on top of `green_corridor.py`. Adds **manual and adaptive control** of a specific junction TLS.

**How it works:**
- Manually cycles through the junction's phases using a custom `PHASE_GROUPS` definition
- Every time a yellow phase ends, it counts vehicles on all approach lanes within **100 metres**
- Green time for the next phase is allocated **proportionally to vehicle demand**, clamped between `MIN_GREEN` and `MAX_GREEN`
- If a green corridor event fires for this junction, manual/adaptive control **pauses automatically** and resumes after the emergency vehicle clears

**Key config values:**

| Variable | Default | Description |
|---|---|---|
| `MANUAL_TLS_ID` | `"YOUR_TLS_ID"` | The TLS ID to control — **must be updated** |
| `MIN_GREEN` | `10s` | Minimum green time per phase |
| `MAX_GREEN` | `60s` | Maximum green time per phase |
| `BASE_GREEN` | `27s` | Fallback green when no vehicles detected |
| `DETECTION_RANGE` | `100m` | How far back to count approaching vehicles |
| `YELLOW_DURATION` | `6s` | Fixed yellow duration — do not change |
| `PHASE_GROUPS` | see file | Green/yellow state strings per phase group |

> ⚠️ **Important:** `PHASE_GROUPS` state strings must exactly match the number of controlled links at your TLS. Use `number_of_links_in_given_tls.py` to inspect them before editing.

---

### `test_tls.py`

Utility script. Prints all TLS IDs present in the loaded network to the console. Use this to find the ID of any junction you want to control.

```bash
python test_tls.py
```

Output is also saved to `all_tls_ids.txt`.

---

### `number_of_links_in_given_tls.py`

Utility script. Given a TLS ID, prints the number of controlled links and all phase states with their durations.

Edit the `TARGET_TLS` variable at the top of the file before running:

```python
TARGET_TLS = "your_tls_id_here"
```

```bash
python number_of_links_in_given_tls.py
```

Use the output to correctly populate `PHASE_GROUPS` in `green_corridor_test_tls.py`.

---

## Modifying the Simulation

### Changing vehicle density

Re-generate trip files using `randomTrips.py`. Lower `-p` = more vehicles per hour:

```bash
# Windows CMD
python %SUMO_HOME%\tools\randomTrips.py ^
  -n osm.net.xml ^
  -o trips_cars.xml ^
  --prefix car_ ^
  -p 0.5 -b 0 -e 3600 ^
  --trip-attributes "type=""car""" ^
  --no-validate
```

Then re-run `duarouter` to regenerate route files:

```bash
duarouter ^
  -n osm.net.xml ^
  --route-files trips_cars.xml ^
  --additional-files vtypes.add.xml ^
  -o routes_cars.rou.xml ^
  --ignore-errors
```

> After regenerating routes, **remove any embedded `<vType>` lines** from the `.rou.xml` files — they conflict with `vtypes.add.xml`. Check with:
> ```bash
> findstr "vType" routes_cars.rou.xml
> ```

### Adding a new vehicle type

1. Add a `<vType>` entry to `vtypes.add.xml`
2. Generate `trips_TYPENAME.xml` and `routes_TYPENAME.rou.xml`
3. Add the new route file to `simulation.sumocfg` under `<route-files>`
4. If it's an emergency type, add its `id` to `EMERGENCY_TYPES` in `green_corridor.py`

### Controlling a different junction

1. Run `test_tls.py` to find the TLS ID
2. Run `number_of_links_in_given_tls.py` with that ID to get link count and phase states
3. Update `MANUAL_TLS_ID` and `PHASE_GROUPS` in `green_corridor_test_tls.py`

---

## SUMO-GUI Tips

### Enable real-world vehicle shapes

In the GUI: **Edit → Visualization Settings → Vehicles → Show As → `real world`**

Or use the dropdown at the top of the view — change from `custom` to **`real world`**.

### Locate a specific vehicle or TLS by ID

**Locate → Vehicles** (or **Locate → TLS**) → type the ID → press Enter.

From there you can centre the view on it, track it, and highlight it.

### Vehicle colours

Vehicles are coloured by their `vType` definition in `vtypes.add.xml`. If all vehicles look the same colour, go to **Edit → Visualization Settings → Vehicles → Color → `given vehicle color`**.

| Vehicle | Colour | Shape |
|---|---|---|
| Car | Yellow | `passenger/sedan` |
| Bike | Green | `bicycle` |
| Bus | Blue | `bus/coach` |
| Ambulance | Red | `emergency` |
| Fire Brigade | Orange | `truck` |

---

## Branching & Contribution Guidelines

> ⚠️ **Do NOT push directly to `master`.** All changes must go through a feature branch and pull request.

### Workflow

```bash
# 1. Pull latest master
git checkout master
git pull origin master

# 2. Create a feature branch
git checkout -b feature/your-feature-name

# 3. Make your changes, then commit
git add .
git commit -m "feat: describe your change clearly"

# 4. Push your branch
git push origin feature/your-feature-name

# 5. Open a Pull Request on GitHub targeting master
```

### Branch naming conventions

| Prefix | Use for |
|---|---|
| `feature/` | New functionality |
| `fix/` | Bug fixes |
| `refactor/` | Code restructuring without behaviour change |
| `docs/` | README or comment updates |
| `experiment/` | Trying out new SUMO configs or parameters |

### What to keep in mind

- Never commit `.rou.xml` or `trips_*.xml` files regenerated from scratch without documenting why in your PR description — these are large and affect reproducibility
- Always run the simulation locally before opening a PR
- If you change `PHASE_GROUPS` state strings, include the output of `number_of_links_in_given_tls.py` in your PR description to prove the link count matches
- `summary.xml` and `tripinfo.xml` are simulation outputs — do not commit them

---

## Quick Reference

```bash
# List all TLS IDs
python test_tls.py

# Inspect a specific TLS
python number_of_links_in_given_tls.py

# Run basic simulation
sumo-gui -c simulation.sumocfg

# Run with green corridor
python green_corridor.py

# Run with green corridor + adaptive TLS
python green_corridor_test_tls.py
```
