import streamlit as st
from ultralytics import YOLO
import PIL.Image as Image
import json
import time
import os

# ---------------- CONFIG ----------------
IMAGE_PATHS = ["north.jpg", "south.jpg", "east.jpg", "west.jpg"]
LANE_NAMES  = ["North Lane", "South Lane", "East Lane", "West Lane"]

JSON_FILE   = "traffic_density.json"

# YOLO vehicle class IDs (COCO dataset)
VEHICLE_CLASSES = [2, 3, 5, 7]
# car=2, motorcycle=3, bus=5, truck=7

# ---------------- MODEL ----------------
@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")

model = load_model()

# ---------------- LOGIC ----------------
def classify_density(count):
    if count <= 2:
        return "Low Traffic", 10
    elif count <= 7:
        return "Medium Traffic", 30
    else:
        return "High Traffic", 60

def save_density_json(counts):
    data = {
        "North": counts[0],
        "South": counts[1],
        "East": counts[2],
        "West": counts[3],
        "timestamp": time.time()
    }

    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- UI ----------------
st.set_page_config(layout="wide", page_title="AI Smart Traffic")

st.title("🚦 AI Smart Traffic Control System")
st.write("Vehicle detection using YOLOv8 → signal timing sent to SUMO simulation")

# show initial images
cols = st.columns(4)

for i in range(4):
    with cols[i]:
        st.subheader(LANE_NAMES[i])

        if os.path.exists(IMAGE_PATHS[i]):
            st.image(IMAGE_PATHS[i], use_container_width=True)
        else:
            st.warning("image missing")

st.divider()

# ---------------- ANALYSIS ----------------
if st.button("🔍 Analyze Traffic Density", type="primary"):

    counts = []

    result_cols = st.columns(4)

    with st.spinner("Running YOLO detection..."):

        for i, img_path in enumerate(IMAGE_PATHS):

            img = Image.open(img_path)

            results = model.predict(img, conf=0.25, verbose=False)

            # filter only vehicle classes
            vehicle_count = 0

            for cls in results[0].boxes.cls:
                if int(cls) in VEHICLE_CLASSES:
                    vehicle_count += 1

            counts.append(vehicle_count)

            label, timer = classify_density(vehicle_count)

            annotated_img = results[0].plot()

            with result_cols[i]:

                st.image(
                    annotated_img,
                    caption=f"{LANE_NAMES[i]}",
                    use_container_width=True
                )

                color = (
                    "green"
                    if label == "Low Traffic"
                    else "orange"
                    if label == "Medium Traffic"
                    else "red"
                )

                st.markdown(f"### Status: :{color}[{label}]")

                st.metric("Green Time", f"{timer} sec")

                st.write(f"Vehicles detected: {vehicle_count}")

                st.progress(min(vehicle_count / 15, 1.0))

    save_density_json(counts)

    st.success("Density saved → SUMO will adapt signals 🚦")

# ---------------- SHOW LAST DATA ----------------
if os.path.exists(JSON_FILE):

    with open(JSON_FILE) as f:
        data = json.load(f)

    st.subheader("Latest Density Data")

    st.json(data)