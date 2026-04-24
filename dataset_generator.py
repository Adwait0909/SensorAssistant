import random
import pandas as pd

# =========================
# COMPONENT POOLS
# =========================

CONTROLLERS = ["arduino_uno", "arduino_nano", "esp8266"]

SENSORS = [
    "lm35", "dht11", "mq2", "mq3", "pir", "ultrasonic",
    "ldr", "flame", "rain", "soil_moisture", "sound", "ir_sensor"
]

OUTPUTS = ["led", "buzzer", "relay", "lcd_16x2", "i2c_lcd", "servo", "dc_motor"]

COMM = ["gsm", "bluetooth", "wifi"]

SUPPORT = [
    "resistor", "breadboard", "power_supply_5v",
    "power_supply_4v", "regulator", "battery", "i2c_backpack"
]

PROJECT_TYPES = [
    "ALERT", "MONITORING", "CONTROL",
    "IOT", "AUTOMATION", "SAFETY", "DATA_LOGGING"
]

# =========================
# RULE-BASED SCORE FUNCTION
# =========================

def compute_score(features):
    score = 0

    score += 2 * features["sensor_count"]
    score += 2 * features["controller_count"]
    score += 1 * features["output_count"]
    score += 3 * features["communication_count"]

    if features["has_iot_pattern"]:
        score += 3
    if features["has_alert_pattern"]:
        score += 2
    if features["has_closed_loop"]:
        score += 3
    if features["multi_sensor_system"]:
        score += 2

    return min(score, 20)

# =========================
# SYSTEM TYPE INFERENCE
# =========================

def infer_type(f):
    if f["has_alert_pattern"]:
        return "ALERT"
    if f["has_iot_pattern"]:
        return "IOT"
    if f["has_closed_loop"]:
        return "CONTROL"
    if f["sensor_count"] > 2:
        return "MONITORING"
    if f["communication_count"] > 0:
        return "DATA_LOGGING"
    return "AUTOMATION"

# =========================
# ROW GENERATOR
# =========================

def generate_row(i):

    row = {}

    # -------------------------
    # RESET ALL BINARY FEATURES
    # -------------------------
    for c in CONTROLLERS + SENSORS + OUTPUTS + COMM + SUPPORT:
        row[c] = 0

    # -------------------------
    # CONTROLLER (always at least 1)
    # -------------------------
    controller = random.choice(CONTROLLERS)
    row[controller] = 1

    # -------------------------
    # SENSORS (1–4)
    # -------------------------
    sensors = random.sample(SENSORS, random.randint(1, 4))
    for s in sensors:
        row[s] = 1

    # -------------------------
    # OUTPUTS (0–3)
    # -------------------------
    outputs = random.sample(OUTPUTS, random.randint(0, 3))
    for o in outputs:
        row[o] = 1

    # -------------------------
    # COMM (0–2)
    # -------------------------
    comm = random.sample(COMM, random.randint(0, 2))
    for c in comm:
        row[c] = 1

    # -------------------------
    # SUPPORT (random 2–5)
    # -------------------------
    support = random.sample(SUPPORT, random.randint(2, 5))
    for s in support:
        row[s] = 1

    # =========================
    # DERIVED FEATURES
    # =========================
    row["sensor_count"] = sum(row[s] for s in SENSORS)
    row["output_count"] = sum(row[o] for o in OUTPUTS)
    row["controller_count"] = sum(row[c] for c in CONTROLLERS)
    row["communication_count"] = sum(row[c] for c in COMM)
    row["support_count"] = sum(row[s] for s in SUPPORT)
    row["total_components"] = sum(row[c] for c in CONTROLLERS + SENSORS + OUTPUTS + COMM + SUPPORT)

    # =========================
    # INTERACTION FEATURES
    # =========================
    row["has_alert_pattern"] = int(
        row["buzzer"] == 1 or (row["gsm"] == 1 and row["sensor_count"] > 0)
    )

    row["has_iot_pattern"] = int(
        row["wifi"] == 1 or row["gsm"] == 1
    )

    row["has_closed_loop"] = int(
        row["servo"] == 1 or row["relay"] == 1 or row["dc_motor"] == 1
    )

    row["has_sensor_comm_pair"] = int(
        row["sensor_count"] > 0 and row["communication_count"] > 0
    )

    row["multi_sensor_system"] = int(row["sensor_count"] > 1)

    # =========================
    # SYSTEM TYPE
    # =========================
    row["project_type"] = infer_type(row)

    # =========================
    # SCORE
    # =========================
    row["score_label"] = compute_score(row)

    # =========================
    # DIFFICULTY
    # =========================
    if row["score_label"] >= 14:
        row["difficulty"] = "HARD"
    elif row["score_label"] >= 8:
        row["difficulty"] = "MEDIUM"
    else:
        row["difficulty"] = "BASIC"

    return row

# =========================
# GENERATE DATASET
# =========================

def generate_dataset(n=10000):
    data = [generate_row(i) for i in range(n)]
    df = pd.DataFrame(data)

    df.to_csv("iot_dataset.csv", index=False)
    print("Dataset generated:", df.shape)

# =========================
# RUN
# =========================

if __name__ == "__main__":
    generate_dataset(10000)