import pickle
import pandas as pd
import json

# =========================
# LOAD FEATURE COLUMNS
# =========================
with open("ml/feature_columns.json") as f:
    FEATURE_COLUMNS = json.load(f)

# =========================
# LOAD MODEL
# =========================
model = pickle.load(open("ml/xgb_model.pkl", "rb"))

# =========================
# CANONICAL → FEATURE MAP
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

# =========================
# BUILD FEATURE VECTOR
# =========================
def build_feature_vector(components: list):
    row = {col: 0 for col in FEATURE_COLUMNS}

    # mark binary features
    for comp in components:
        feature = CANONICAL_TO_FEATURE.get(comp)
        if feature:
            row[feature] = 1

    # 🔥 ADD DERIVED FEATURES (CRUCIAL)
    sensor_features = ["lm35","dht11","mq2","mq3","pir","ultrasonic","ldr","flame","rain","soil_moisture","sound","ir_sensor"]
    output_features = ["led","buzzer","relay","lcd_16x2","i2c_lcd","servo","dc_motor"]
    controller_features = ["arduino_uno","arduino_nano","esp8266"]
    comm_features = ["gsm","bluetooth","wifi"]
    support_features = ["resistor","breadboard","power_supply_5v","power_supply_4v","regulator","battery","i2c_backpack"]

    row["sensor_count"] = sum(row[f] for f in sensor_features)
    row["output_count"] = sum(row[f] for f in output_features)
    row["controller_count"] = sum(row[f] for f in controller_features)
    row["communication_count"] = sum(row[f] for f in comm_features)
    row["support_count"] = sum(row[f] for f in support_features)

    row["total_components"] = sum(row.values())

    return pd.DataFrame([row])[FEATURE_COLUMNS]
# =========================
# MAIN PREDICT FUNCTION
# =========================
def predict_score(user_input: str) -> float:
    from engine.parser import normalize_input

    components = normalize_input(user_input)

    X = build_feature_vector(components)

    prediction = model.predict(X)

    return float(prediction[0])

# =========================
# SCORE → CATEGORY
# =========================
def score_to_category(score: float) -> str:
    if score >= 16:
        return "IoT"
    elif score >= 12:
        return "Monitoring"
    elif score >= 8:
        return "Control"
    else:
        return "Basic Output"