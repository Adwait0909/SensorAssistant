import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# LOAD DATASET
# =========================
df = pd.read_csv("iot_dataset_clean.csv")

print("\n========================")
print("DATASET SHAPE")
print("========================")
print(df.shape)

# =========================
# 1. PROJECT TYPE DISTRIBUTION
# =========================
print("\n========================")
print("PROJECT TYPE DISTRIBUTION")
print("========================")
print(df["project_type"].value_counts())

df["project_type"].value_counts().plot(kind="bar")
plt.title("Project Type Distribution")
plt.show()

# =========================
# 2. DIFFICULTY DISTRIBUTION
# =========================
print("\n========================")
print("DIFFICULTY DISTRIBUTION")
print("========================")
print(df["difficulty"].value_counts())

df["difficulty"].value_counts().plot(kind="bar")
plt.title("Difficulty Distribution")
plt.show()

# =========================
# 3. SCORE DISTRIBUTION
# =========================
print("\n========================")
print("SCORE STATISTICS")
print("========================")
print(df["score_label"].describe())

df["score_label"].hist(bins=20)
plt.title("Score Distribution")
plt.show()

# =========================
# 4. SENSOR BIAS CHECK
# =========================
sensor_cols = [
    "lm35","dht11","mq2","mq3","pir","ultrasonic",
    "ldr","flame","rain","soil_moisture","sound","ir_sensor"
]

print("\n========================")
print("SENSOR USAGE COUNT")
print("========================")
print(df[sensor_cols].sum().sort_values(ascending=False))

df[sensor_cols].sum().plot(kind="bar")
plt.title("Sensor Usage Distribution")
plt.show()

# =========================
# 5. OUTPUT BIAS CHECK
# =========================
output_cols = ["led","buzzer","relay","lcd_16x2","i2c_lcd","servo","dc_motor"]

print("\n========================")
print("OUTPUT USAGE COUNT")
print("========================")
print(df[output_cols].sum().sort_values(ascending=False))

df[output_cols].sum().plot(kind="bar")
plt.title("Output Usage Distribution")
plt.show()

# =========================
# 6. COMMUNICATION BIAS CHECK
# =========================
comm_cols = ["gsm","bluetooth","wifi"]

print("\n========================")
print("COMMUNICATION USAGE COUNT")
print("========================")
print(df[comm_cols].sum().sort_values(ascending=False))

df[comm_cols].sum().plot(kind="bar")
plt.title("Communication Usage Distribution")
plt.show()

# =========================
# 7. SUPPORT COMPONENT BIAS CHECK
# =========================
support_cols = [
    "resistor","breadboard","power_supply_5v",
    "power_supply_4v","regulator","battery","i2c_backpack"
]

print("\n========================")
print("SUPPORT COMPONENT USAGE")
print("========================")
print(df[support_cols].sum().sort_values(ascending=False))

df[support_cols].sum().plot(kind="bar")
plt.title("Support Component Usage Distribution")
plt.show()

# =========================
# 8. FEATURE CORRELATION HEATMAP
# =========================
print("\n========================")
print("CORRELATION HEATMAP")
print("========================")

numeric_df = df.drop(columns=["project_type","difficulty"])

plt.figure(figsize=(14,10))
sns.heatmap(numeric_df.corr(), cmap="coolwarm")
plt.title("Feature Correlation Heatmap")
plt.show()

# =========================
# 9. CLASS IMBALANCE REPORT
# =========================
def imbalance_report(series):
    total = len(series)
    for k, v in series.value_counts().items():
        print(f"{k}: {v} ({(v/total)*100:.2f}%)")

print("\n========================")
print("PROJECT TYPE BALANCE %")
print("========================")
imbalance_report(df["project_type"])

print("\n========================")
print("DIFFICULTY BALANCE %")
print("========================")
imbalance_report(df["difficulty"])

# =========================
# FINAL SUMMARY
# =========================
print("\n========================")
print("CHECK COMPLETE")
print("========================")
print("If any class >40% or <10%, dataset is biased.")
print("If correlation is too high across features, dataset is too synthetic.")