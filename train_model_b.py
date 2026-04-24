import pandas as pd
import pickle
import numpy as np
import json

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# =========================
# LOAD DATA
# =========================
# =========================
# FEATURES (DROP TARGETS)
# =========================
df = pd.read_csv("iot_dataset_balanced.csv")

# OPTIONAL: small random noise
df["score_label"] += np.random.normal(0, 1.5, len(df))

df["score_label"] = df["score_label"].clip(0, 20)

# Drop leakage
drop_cols = [
    "score_label",
    "project_type",
    "difficulty",
    "has_alert_pattern",
    "has_closed_loop",
    "has_sensor_comm_pair",
    "multi_sensor_system"
]

X = df.drop(columns=drop_cols)
y = df["score_label"]

X = df.drop(columns=drop_cols)
with open("ml/feature_columns.json", "w") as f:
    json.dump(X.columns.tolist(), f)

print("Feature columns saved correctly")
# =========================
# TARGET
# =========================
y = df["score_label"]

# =========================
# ADD NOISE HERE (IMPORTANT)
# =========================
noise = np.random.normal(loc=0, scale=1.5, size=len(df))  # tune scale
df["score_label"] += noise

# Keep values in valid range
df["score_label"] = df["score_label"].clip(0, 20)

# =========================
# SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

# =========================
# MODEL
# =========================
model = XGBRegressor(
    n_estimators=500,
    max_depth=7,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1,
    random_state=42
)

model.fit(X_train, y_train)

# =========================
# EVALUATION
# =========================
y_pred = model.predict(X_test)

print("\n===== PERFORMANCE =====")
print("MAE:", mean_absolute_error(y_test, y_pred))
print("R2:", r2_score(y_test, y_pred))

# =========================
# SAVE MODEL
# =========================
pickle.dump(model, open("ml/xgb_model.pkl", "wb"))

print("\nModel saved successfully.")