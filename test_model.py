import pickle
import pandas as pd
import json
from engine.parser import normalize_input

# =========================
# LOAD MODEL
# =========================
model = pickle.load(open("ml/xgb_model.pkl", "rb"))

# =========================
# LOAD FEATURE ORDER
# =========================
with open("ml/feature_columns.json") as f:
    FEATURE_COLUMNS = json.load(f)

# =========================
# FEATURE GROUPS (IMPORTANT)
# =========================
SENSORS = [
    "lm35","dht11","mq2","mq3","pir","ultrasonic",
    "ldr","flame","rain","soil_moisture","sound","ir_sensor"
]

OUTPUTS = [
    "led","buzzer","relay","lcd_16x2","i2c_lcd","servo","dc_motor"
]

COMM = ["gsm","bluetooth","wifi"]

# =========================
# SAME MAPPING AS TRAINING
# =========================
CANONICAL_TO_FEATURE = {
    "Arduino Uno": "arduino_uno",
    "Arduino Nano": "arduino_nano",
    "ESP8266 (NodeMCU)": "esp8266",

    "Temperature Sensor (LM35 / DHT11)": "lm35",
    "Humidity Sensor": "dht11",
    "Gas Sensor (MQ-2)": "mq2",
    "Alcohol Sensor (MQ-3)": "mq3",
    "Motion Sensor (PIR)": "pir",
    "Ultrasonic Sensor (HC-SR04)": "ultrasonic",
    "Light Sensor (LDR)": "ldr",
    "Sound Sensor": "sound",
    "Flame Sensor": "flame",
    "Rain Sensor": "rain",
    "Soil Moisture Sensor": "soil_moisture",
    "IR Sensor (Obstacle Detection)": "ir_sensor",

    "LED": "led",
    "Buzzer": "buzzer",
    "Relay Module": "relay",
    "LCD 16x2": "lcd_16x2",
    "I2C LCD Module": "i2c_lcd",
    "Servo Motor": "servo",
    "DC Motor": "dc_motor",

    "GSM SIM800L": "gsm",
    "Bluetooth Module (HC-05)": "bluetooth",
    "WiFi Module": "wifi",

    "Resistor": "resistor",
    "Breadboard": "breadboard",
    "Power Supply (5V regulated)": "power_supply_5v",
    "Power Supply (4V regulated)": "power_supply_4v",
    "Voltage Regulator (AMS1117 / LM2596)": "regulator",
    "Battery": "battery",
    "I2C Backpack": "i2c_backpack"
}

def load_aliases():
    with open("data/aliases.json") as f:
        return json.load(f)

# =========================
# NORMALIZATION
# =========================
def normalize(text):
    aliases = load_aliases()
    parts = [p.strip().lower() for p in text.split(",")]

    normalized = []
    for p in parts:
        if p in aliases:
            normalized.append(aliases[p])
        else:
            normalized.append(p)

    return normalized

# =========================
# BUILD FEATURE VECTOR
# =========================
def build_vector(components):
    row = {col: 0 for col in FEATURE_COLUMNS}

    # --- Binary features ---
    for comp in components:
        feature = CANONICAL_TO_FEATURE.get(comp)
        if feature:
            row[feature] = 1
        if row["sensor_count"] > 0 and row["output_count"] == 0:
            score -= 2

    # --- Derived features (CRITICAL FIX) ---
    row["sensor_count"] = sum(row.get(s, 0) for s in SENSORS)
    row["output_count"] = sum(row.get(o, 0) for o in OUTPUTS)
    row["communication_count"] = sum(row.get(c, 0) for c in COMM)
    row["total_components"] = sum(row.values())
    row["has_iot_pattern"] = int(row["wifi"] == 1 or row["gsm"] == 1)

    return pd.DataFrame([row])[FEATURE_COLUMNS]

# =========================
# TEST CASES
# =========================
tests = [
    "Arduino Uno",
    "Arduino Uno, DHT11, LCD 16x2",
    "Arduino Uno, MQ2, Buzzer",
    "ESP8266 (NodeMCU), DHT11, WiFi Module, LCD 16x2",
    "Arduino Uno, DHT11, MQ2, GSM SIM800L, Relay Module, LCD 16x2",
    "quantum sensor, laser cannon"
]

# =========================
# RUN TESTS
# =========================
for t in tests:
    components = normalize_input(t)
    X = build_vector(components)

    # Handle garbage input
    if X.sum(axis=1).values[0] == 0:
        pred = 0
    else:
        pred = model.predict(X)[0]
        pred = max(0, min(20, pred))

    print("\nInput:", t)
    print("Predicted Score:", round(pred, 2))