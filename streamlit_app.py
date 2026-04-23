import json
from io import StringIO

import pandas as pd
import streamlit as st

from engine.generator import (
    generate_projects,
    generate_system_flow,
    get_feasibility_issues,
    get_missing_component_suggestions,
)
from engine.matcher import classify_components, get_roles
from engine.parser import normalize_input
from engine.warnings_engine import generate_warnings


ML_RELATED = {
    "Alert": {"Safety", "IoT", "Monitoring"},
    "Safety": {"Alert", "Monitoring", "IoT"},
    "IoT": {"Monitoring", "Data Logging", "Alert"},
    "Monitoring": {"Data Logging", "IoT", "Safety"},
    "Data Logging": {"Monitoring", "IoT"},
    "Control": {"Monitoring", "Basic Output"},
    "Basic Output": {"Control"},
}


def parse_input(raw_input):
    """Normalize user component input string."""
    if not raw_input:
        return []
    return normalize_input(raw_input)


def detect_components(normalized_components):
    """Split components and classify by role."""
    known_components, unknown_components = classify_components(normalized_components)
    roles = get_roles(known_components)

    role_map = {
        "controller": [],
        "sensors": [],
        "outputs": [],
        "communication": [],
        "others": [],
    }

    for name in known_components:
        role = None
        # get_roles only returns values, not mapping; infer through simple checks from generated role list
        # by testing one-at-a-time membership.
        single_role = get_roles([name])
        if single_role:
            role = single_role[0]

        if role == "controller":
            role_map["controller"].append(name)
        elif role == "input":
            role_map["sensors"].append(name)
        elif role == "output":
            role_map["outputs"].append(name)
        elif role == "communication":
            role_map["communication"].append(name)
        else:
            role_map["others"].append(name)

    return known_components, unknown_components, roles, role_map


def _normalize_category(category_text):
    text = (category_text or "").strip().lower()
    mapping = {
        "alert": "Alert",
        "safety": "Safety",
        "iot": "IoT",
        "monitoring": "Monitoring",
        "data logging": "Data Logging",
        "datalogging": "Data Logging",
        "control": "Control",
        "basic output": "Basic Output",
    }
    return mapping.get(text, category_text.strip().title() if category_text else "")


def _ml_score(project_type, ml_category, used_count):
    normalized_ml = _normalize_category(ml_category)
    if not normalized_ml:
        return min(4, used_count)
    if project_type == normalized_ml:
        return 10 + min(4, used_count)
    if normalized_ml in ML_RELATED.get(project_type, set()) or project_type in ML_RELATED.get(normalized_ml, set()):
        return 6 + min(4, used_count)
    return 2 + min(3, used_count)


def _recommendation_from_score(score):
    if score >= 16:
        return "Highly Recommended"
    if score >= 10:
        return "Good Option"
    return "Basic Idea"


def rank_projects(known_components, roles, ml_category, mode):
    """Generate and rank projects with rule/ml/hybrid scores."""
    raw_projects = generate_projects(known_components, roles, ml_category=ml_category)
    ranked = []

    for project in raw_projects:
        used_count = len(project.get("components_used", []))
        rule_score = project.get("score", 0)
        ml_score = _ml_score(project.get("type", ""), ml_category, used_count)

        if mode == "Rule-based":
            final_score = rule_score
        elif mode == "ML":
            final_score = ml_score
        else:
            final_score = round((0.7 * rule_score) + (0.3 * ml_score), 2)

        ranked_project = {
            "name": project["name"],
            "type": project["type"],
            "description": project["description"],
            "components_used": project.get("components_used", []),
            "why": project.get("why", {}),
            "rule_score": rule_score,
            "ml_score": ml_score,
            "score": final_score,
        }
        ranked_project["recommendation"] = _recommendation_from_score(final_score)
        ranked.append(ranked_project)

    ranked.sort(
        key=lambda item: (
            item["score"],
            len(item["components_used"]),
            item["why"].get("real_world", ""),
            item["why"].get("core_completeness", ""),
        ),
        reverse=True,
    )
    return ranked


def generate_explanations(project, ml_category, mode):
    why = project.get("why", {})
    explanation = {
        "core_completeness": why.get("core_completeness", ""),
        "component_usage": why.get("component_usage", ""),
        "system_logic": why.get("system_logic", ""),
        "ml_influence": why.get("ml_influence", ""),
        "real_world": why.get("real_world", ""),
    }
    if mode != "Rule-based" and ml_category:
        explanation["ml_influence"] = f"{explanation['ml_influence']} | Mode: {mode}"
    return explanation


st.set_page_config(page_title="IoT Project Recommendation System", layout="wide")
st.title("IoT Project Recommendation System")
st.caption("Hybrid rule + ML assisted embedded project recommender")

with st.sidebar:
    st.header("Controls")
    mode = st.radio("Ranking Mode", ["Rule-based", "ML", "Hybrid"], index=2)
    min_threshold = st.slider("Minimum Score Threshold", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
    ml_category = st.text_input("ML Predicted Category", placeholder="Monitoring / Safety / Alert / IoT")
    suggest_missing_btn = st.button("Suggest Missing Components")
    explain_btn = st.button("Explain Recommendation (AI reasoning)")

component_input = st.text_input(
    "Enter components (comma-separated)",
    placeholder="arduino, mq2, gsm, buzzer",
)

if component_input:
    normalized = parse_input(component_input)
    known_components, unknown_components, roles, role_map = detect_components(normalized)

    projects = rank_projects(known_components, roles, ml_category, mode)
    projects = [p for p in projects if p["score"] >= min_threshold]

    suggestions = get_missing_component_suggestions(roles)
    warnings = generate_warnings(known_components)
    feasibility = get_feasibility_issues(roles, known_components)
    system_flow = generate_system_flow(known_components)

    if suggest_missing_btn and "System is complete. Proceed to wiring and testing." in suggestions:
        suggestions = suggestions + ["Optional: Add WiFi/GSM dashboard for remote monitoring history"]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Detected Components")
        st.write(known_components if known_components else ["None"])
    with col2:
        st.subheader("Unknown Components")
        st.write(unknown_components if unknown_components else ["None"])

    st.subheader("Component Type Breakdown")
    type_df = pd.DataFrame(
        [
            {"type": "controller", "components": ", ".join(role_map["controller"]) or "None"},
            {"type": "sensors", "components": ", ".join(role_map["sensors"]) or "None"},
            {"type": "outputs", "components": ", ".join(role_map["outputs"]) or "None"},
            {"type": "communication", "components": ", ".join(role_map["communication"]) or "None"},
            {"type": "others", "components": ", ".join(role_map["others"]) or "None"},
        ]
    )
    st.dataframe(type_df, use_container_width=True, hide_index=True)

    st.subheader("Possible Projects (Ranked)")
    if projects:
        st.success(f"⭐ Top Recommendation: {projects[0]['name']} (Score: {projects[0]['score']})")

        for idx, project in enumerate(projects, start=1):
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### {idx}. {project['name']}")
                with c2:
                    st.metric("Score", project["score"])

                st.write(f"**Type:** {project['type']}")
                st.write(f"**Recommendation:** {project['recommendation']}")
                st.write(f"**Description:** {project['description']}")
                st.write("**Why this rank:**")
                explanation = generate_explanations(project, ml_category, mode)
                st.markdown(f"- Core completeness: {explanation['core_completeness']}")
                st.markdown(f"- Components used: {', '.join(project['components_used']) if project['components_used'] else 'None'}")
                st.markdown(f"- System logic: {explanation['system_logic']}")
                st.markdown(f"- ML influence: {explanation['ml_influence']}")
                st.markdown(f"- Real-world relevance: {explanation['real_world']}")
                if explain_btn:
                    st.info(
                        "This project ranks here due to weighted engineering fitness, "
                        "actual component utilization, and selected ranking mode influence."
                    )
    else:
        st.warning("No projects match the current threshold/mode combination.")

    st.subheader("Feasibility Issues")
    if feasibility:
        for issue in feasibility:
            st.write(f"✅ {issue}")
    else:
        st.write("✅ No major feasibility issues detected.")

    st.subheader("System Flow")
    for step in system_flow:
        st.write(f"- {step}")

    st.subheader("Suggestions")
    for suggestion in suggestions:
        st.write(f"- {suggestion}")

    st.subheader("Warnings")
    if warnings:
        for warning in warnings:
            st.markdown(f"<span style='color:red;'>⚠ {warning}</span>", unsafe_allow_html=True)
    else:
        st.write("No warnings detected.")

    export_payload = {
        "detected_components": known_components,
        "unknown_components": unknown_components,
        "projects": [
            {
                "name": p["name"],
                "score": p["score"],
                "type": p["type"],
                "recommendation": p["recommendation"],
                "description": p["description"],
                "components_used": p["components_used"],
                "why": generate_explanations(p, ml_category, mode),
            }
            for p in projects
        ],
        "feasibility_issues": feasibility,
        "system_flow": system_flow,
        "suggestions": suggestions,
        "warnings": warnings,
    }

    projects_df = pd.DataFrame(
        [
            {
                "rank": i + 1,
                "name": p["name"],
                "score": p["score"],
                "type": p["type"],
                "recommendation": p["recommendation"],
                "description": p["description"],
                "components_used": ", ".join(p["components_used"]),
            }
            for i, p in enumerate(projects)
        ]
    )
    csv_buffer = StringIO()
    projects_df.to_csv(csv_buffer, index=False)

    st.subheader("Export")
    ex1, ex2 = st.columns(2)
    with ex1:
        st.download_button(
            "Export JSON",
            data=json.dumps(export_payload, ensure_ascii=False, indent=2),
            file_name="iot_project_recommendations.json",
            mime="application/json",
        )
    with ex2:
        st.download_button(
            "Export CSV",
            data=csv_buffer.getvalue(),
            file_name="iot_project_recommendations.csv",
            mime="text/csv",
        )
else:
    st.info("Enter components to generate recommendations.")
