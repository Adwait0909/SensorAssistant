from ml.predictor import predict_score, score_to_category

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
# MAIN PIPELINE
# =========================
def process_input(user_input: str) -> dict:
    
    # =========================
    # 1. ML PREDICTION
    # =========================
    ml_score = predict_score(user_input)
    components = normalize_input(user_input)
    ml_category = score_to_category(ml_score)

    # =========================
    # 2. PARSE INPUT
    # =========================
    

    known_components, unknown_components = classify_components(components)

    roles = get_roles(known_components)

    # =========================
    # 3. PROJECT GENERATION
    # =========================
    projects = generate_projects(
        known_components,
        roles,
        ml_category=ml_category   # IMPORTANT FIX
    )

    # =========================
    # 4. AUXILIARY OUTPUTS
    # =========================
    warnings = generate_warnings(known_components)

    suggestions = get_missing_component_suggestions(roles)

    system_flow = generate_system_flow(known_components)

    feasibility_issues = get_feasibility_issues(roles, known_components)

    # =========================
    # 5. FINAL OUTPUT
    # =========================
    return {
        "detected_components": known_components,
        "unknown_components": unknown_components,
        "ml_score": ml_score,
        "ml_category": ml_category,
        "projects": projects,
        "feasibility_issues": feasibility_issues,
        "system_flow": system_flow,
        "suggestions": suggestions,
        "warnings": warnings,
    }