import streamlit as st
import pickle
import pandas as pd
from scipy.sparse import hstack

from engine.parser import normalize_input
from engine.matcher import get_roles, classify_components
from engine.generator import (
    generate_projects,
    get_missing_component_suggestions,
    generate_system_flow,
    get_feasibility_issues,
)
from engine.warnings_engine import generate_warnings


# =========================
# LOAD MODEL (ONLY ONCE)
# =========================
@st.cache_resource
def load_model():
    model = pickle.load(open("model.pkl", "rb"))
    vectorizer = pickle.load(open("vectorizer.pkl", "rb"))
    scaler = pickle.load(open("scaler.pkl", "rb"))
    return model, vectorizer, scaler

model, vectorizer, scaler = load_model()
# =========================
# ML PREDICTION FUNCTION
# =========================
def predict_score(user_input):
    text = user_input.lower()

    X_text = vectorizer.transform([text])

    components = [c.strip() for c in text.split(",")]

    component_count = len(components)

    has_controller = int(any(x in text for x in ["arduino", "esp", "raspberry"]))
    has_sensor = int(any(x in text for x in ["mq2", "dht", "pir", "ldr", "ultrasonic", "soil", "flame", "temperature"]))
    has_output = int(any(x in text for x in ["lcd", "led", "buzzer", "oled", "relay"]))
    has_comm = int(any(x in text for x in ["wifi", "gsm", "bluetooth"]))

    X_numeric = pd.DataFrame([{
        "has_controller": has_controller,
        "has_sensor": has_sensor,
        "has_output": has_output,
        "has_comm": has_comm,
        "component_count": component_count
    }])

    X_numeric_scaled = scaler.transform(X_numeric)

    X_final = hstack([X_text, X_numeric_scaled])

    prediction = model.predict(X_final)

    return int(prediction[0])


# =========================
# UI
# =========================
st.title("🔧 Sensor Helper AI")

user_input = st.text_input("Enter components (comma separated):")

if st.button("Generate Project"):

    if not user_input.strip():
        st.warning("Enter some components")
    else:
        # ML score
        ml_score = predict_score(user_input)

        # Rule engine
        components = normalize_input(user_input)
        known_components, unknown_components = classify_components(components)
        roles = get_roles(known_components)

        projects = generate_projects(known_components, roles, ml_score=ml_score)
        warnings = generate_warnings(known_components)
        suggestions = get_missing_component_suggestions(roles)
        system_flow = generate_system_flow(known_components)
        feasibility_issues = get_feasibility_issues(roles, known_components)

        # =========================
        # OUTPUT UI
        # =========================
        st.subheader(f"ML Score: {ml_score}")

        st.write("### Detected Components")
        st.write(known_components)

        st.write("### Unknown Components")
        st.write(unknown_components)

        st.write("### Projects")
        for p in projects:
            st.markdown(f"**{p['name']}**")
            st.write(f"Score: {p['score']} | Type: {p['type']}")
            st.write(p["description"])
            st.write("---")

        st.write("### Warnings")
        st.write(warnings)

        st.write("### Suggestions")
        st.write(suggestions)

        st.write("### System Flow")
        st.write(system_flow)

        st.write("### Feasibility Issues")
        st.write(feasibility_issues)