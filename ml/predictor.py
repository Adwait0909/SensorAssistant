import pickle
import pandas as pd
from scipy.sparse import hstack

# =========================
# LOAD MODEL ARTIFACTS (ONCE)
# =========================
model = pickle.load(open("ml/model.pkl", "rb"))
vectorizer = pickle.load(open("ml/vectorizer.pkl", "rb"))
scaler = pickle.load(open("ml/scaler.pkl", "rb"))

# =========================
# CLEANING (MATCH TRAINING)
# =========================
def clean_text(text: str) -> str:
    text = text.lower()
    text = text.replace("mq-2", "mq2")
    text = text.replace("temp sensor", "temperature")
    text = text.replace("gas sensor", "mq2")
    return text

# =========================
# FEATURE EXTRACTION
# =========================
def extract_features(text: str):
    components = [c.strip() for c in text.split(",")]

    component_count = len(components)

    has_controller = int(any(x in text for x in ["arduino", "esp", "raspberry"]))
    has_sensor = int(any(x in text for x in [
        "mq2", "dht", "pir", "ldr", "ultrasonic",
        "soil", "flame", "temperature"
    ]))
    has_output = int(any(x in text for x in [
        "lcd", "led", "buzzer", "oled", "relay"
    ]))
    has_comm = int(any(x in text for x in [
        "wifi", "gsm", "bluetooth"
    ]))

    return pd.DataFrame([{
        "has_controller": has_controller,
        "has_sensor": has_sensor,
        "has_output": has_output,
        "has_comm": has_comm,
        "component_count": component_count
    }])

# =========================
# MAIN PREDICT FUNCTION
# =========================
def predict_score(user_input: str) -> int:
    text = clean_text(user_input)

    # TEXT → TF-IDF
    X_text = vectorizer.transform([text])

    # NUMERIC
    X_numeric = extract_features(text)
    X_numeric_scaled = scaler.transform(X_numeric)

    # COMBINE
    X_final = hstack([X_text, X_numeric_scaled])

    # PREDICT
    prediction = model.predict(X_final)

    return int(prediction[0])

# =========================
# OPTIONAL: SCORE → CATEGORY
# =========================
def score_to_category(score: int) -> str:
    if score >= 8:
        return "IoT"
    elif score >= 6:
        return "Monitoring"
    elif score >= 4:
        return "Control"
    else:
        return "Basic Output"