import pandas as pd

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("iot_dataset.csv")

print("Original shape:", df.shape)

# =========================
# COMPONENT LISTS
# =========================
SENSORS = ["lm35","dht11","mq2","mq3","pir","ultrasonic","ldr","flame","rain","soil_moisture","sound","ir_sensor"]
OUTPUTS = ["led","buzzer","relay","lcd_16x2","i2c_lcd","servo","dc_motor"]
COMM = ["gsm","bluetooth","wifi"]
CONTROLLERS = ["arduino_uno","arduino_nano","esp8266"]
SUPPORT = ["resistor","breadboard","power_supply_5v","power_supply_4v","regulator","battery","i2c_backpack"]

# =========================
# STEP 1: REMOVE DUPLICATES
# =========================
df = df.drop_duplicates()

# =========================
# STEP 2: RECOMPUTE COUNTS
# =========================
df["sensor_count_check"] = df[SENSORS].sum(axis=1)
df["output_count_check"] = df[OUTPUTS].sum(axis=1)
df["comm_count_check"] = df[COMM].sum(axis=1)
df["controller_count_check"] = df[CONTROLLERS].sum(axis=1)
df["support_count_check"] = df[SUPPORT].sum(axis=1)

# Remove mismatched rows
df = df[
    (df["sensor_count"] == df["sensor_count_check"]) &
    (df["output_count"] == df["output_count_check"]) &
    (df["communication_count"] == df["comm_count_check"]) &
    (df["controller_count"] == df["controller_count_check"])
]

# =========================
# STEP 3: VALIDATE IoT LOGIC
# =========================
df["has_actuator"] = df[["servo","dc_motor","relay"]].sum(axis=1) > 0

df = df[~(
    (df["has_closed_loop"] == 1) &
    (df["has_actuator"] == False)
)]

df = df[~(
    (df["has_iot_pattern"] == 1) &
    (df[["wifi","gsm"]].sum(axis=1) == 0)
)]

# =========================
# STEP 4: FIX LABEL CONSISTENCY
# =========================
def difficulty(score):
    if score >= 14:
        return "HARD"
    elif score >= 8:
        return "MEDIUM"
    return "BASIC"

df = df[df["difficulty"] == df["score_label"].apply(difficulty)]

# =========================
# STEP 5: DROP CHECK COLUMNS
# =========================
df = df.drop(columns=[
    "sensor_count_check",
    "output_count_check",
    "comm_count_check",
    "controller_count_check",
    "support_count_check",
    "has_actuator"
])

# =========================
# FINAL OUTPUT
# =========================
print("Cleaned shape:", df.shape)

df.to_csv("iot_dataset_clean.csv", index=False)

print("Saved: iot_dataset_clean.csv")