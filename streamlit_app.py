import json
import pandas as pd
import streamlit as st

from ml.predictor import predict_score, score_to_category

from engine.generator import (
    generate_projects,
    generate_system_flow,
    get_feasibility_issues,
    get_missing_component_suggestions,
)
from engine.matcher import classify_components, get_roles
from engine.parser import normalize_input
from engine.warnings_engine import generate_warnings


# =========================
# STREAMLIT CONFIG
# =========================
st.set_page_config(
    page_title="IoT Project Recommender",
    layout="wide",
    page_icon="🔧"
)

st.title("🔧 IoT Project Recommendation System")
st.caption("AI-powered embedded project generator using ML + rule intelligence")


# =========================
# INPUT
# =========================
component_input = st.text_input(
    "Enter components (comma-separated)",
    placeholder="arduino, mq2, gsm, buzzer",
)


# =========================
# MAIN
# =========================
if component_input:

    # ===== ML =====
    ml_score = predict_score(component_input)
    ml_category = score_to_category(ml_score)

    # ===== PARSE =====
    normalized = normalize_input(component_input)
    known_components, unknown_components = classify_components(normalized)
    roles = get_roles(known_components)

    # ===== PROJECTS =====
    projects = generate_projects(known_components, roles, ml_category=ml_category)

    # ===== EXTRA =====
    suggestions = get_missing_component_suggestions(roles)
    warnings = generate_warnings(known_components)
    feasibility = get_feasibility_issues(roles, known_components)
    system_flow = generate_system_flow(known_components)

    # =========================
    # TOP METRICS
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("ML Score", round(ml_score, 2))
    col2.metric("Category", ml_category)
    col3.metric("Projects Found", len(projects))

    st.divider()

    # =========================
    # COMPONENTS
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Detected Components")
        st.write(known_components if known_components else ["None"])

    with col2:
        st.subheader("Unknown Components")
        st.write(unknown_components if unknown_components else ["None"])

    st.divider()

    # =========================
    # PROJECTS DISPLAY
    # =========================
    st.subheader("🚀 All Possible Projects")

    if projects:

        # Highlight best match
        best_projects = [p for p in projects if p["type"] == ml_category]

        if best_projects:
            st.success(f"🎯 Best Match (ML): {best_projects[0]['name']}")

        for project in projects:
            with st.container(border=True):

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"### {project['name']}")
                    st.write(project["description"])

                with col2:
                    st.markdown(f"**Type:** {project['type']}")

                # Components used
                if project.get("components_used"):
                    st.markdown(
                        f"**Components Used:** {', '.join(project['components_used'])}"
                    )

    else:
        st.warning("No projects could be generated")

    st.divider()

    # =========================
    # SYSTEM FLOW
    # =========================
    st.subheader("🔄 System Flow")

    for step in system_flow:
        st.write(f"→ {step}")

    st.divider()

    # =========================
    # WARNINGS
    # =========================
    st.subheader("⚠ Warnings")

    if warnings:
        for w in warnings:
            st.error(w)
    else:
        st.success("No warnings detected")

    st.divider()

    # =========================
    # SUGGESTIONS
    # =========================
    st.subheader("💡 Suggestions")

    for s in suggestions:
        st.write(f"- {s}")

    st.divider()

    # =========================
    # FEASIBILITY
    # =========================
    st.subheader("⚙ Feasibility Check")

    if feasibility:
        for f in feasibility:
            st.write(f"✔ {f}")
    else:
        st.success("No major issues")

    st.divider()

    # =========================
    # EXPORT
    # =========================
    export_data = {
        "ml_score": ml_score,
        "ml_category": ml_category,
        "components": known_components,
        "projects": projects,
        "warnings": warnings,
        "suggestions": suggestions,
        "system_flow": system_flow,
        "feasibility": feasibility,
    }

    st.download_button(
        "📥 Download Results (JSON)",
        data=json.dumps(export_data, indent=2),
        file_name="iot_projects.json",
        mime="application/json",
    )

else:
    st.info("Enter components to generate projects")