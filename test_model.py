import pickle
import numpy as np
import pandas as pd
from scipy.sparse import hstack


# =========================
# Load
# =========================
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))

# =========================
# Input
# =========================
user_input = "arduino uno"

# =========================
# SAME preprocessing
# =========================
def clean_text(text):
    text = text.lower()
    text = text.replace("mq-2", "mq2")
    text = text.replace("temp sensor", "temperature")
    text = text.replace("gas sensor", "mq2")
    return text

user_input = clean_text(user_input)

# =========================
# TEXT → vector
# =========================
X_text = vectorizer.transform([user_input])

# =========================
# NUMERIC FEATURES (MUST MATCH TRAINING)
# =========================
components = [c.strip() for c in user_input.split(",")]

component_count = len(components)

has_controller = int(any(x in user_input for x in ["arduino", "esp", "raspberry"]))
has_sensor = int(any(x in user_input for x in ["mq2", "dht", "pir", "ldr", "ultrasonic", "soil", "flame", "temperature"]))
has_output = int(any(x in user_input for x in ["lcd", "led", "buzzer", "oled", "relay"]))
has_comm = int(any(x in user_input for x in ["wifi", "gsm", "bluetooth"]))

X_numeric = pd.DataFrame([{
    "has_controller": has_controller,
    "has_sensor": has_sensor,
    "has_output": has_output,
    "has_comm": has_comm,
    "component_count": component_count
}])
# SCALE (VERY IMPORTANT)
X_numeric_scaled = scaler.transform(X_numeric)

# =========================
# Combine
# =========================
X_final = hstack([X_text, X_numeric_scaled])

# =========================
# Predict
# =========================
prediction = model.predict(X_final)

print("Predicted Score:", int(prediction[0]))