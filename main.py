import sys
import json

from engine.parser import normalize_input
from engine.matcher import get_roles, classify_components
from engine.generator import (
    generate_projects,
    get_missing_component_suggestions,
    generate_system_flow,
    get_feasibility_issues,
)
from engine.warnings_engine import generate_warnings

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def _safe_input():
    try:
        return input().strip()
    except EOFError:
        return ""

user_input = _safe_input()
ml_category = _safe_input()

components = normalize_input(user_input)
known_components, unknown_components = classify_components(components)
roles = get_roles(known_components)

projects = generate_projects(known_components, roles, ml_category=ml_category)
warnings = generate_warnings(known_components)
suggestions = get_missing_component_suggestions(roles)
system_flow = generate_system_flow(known_components)
feasibility_issues = get_feasibility_issues(roles, known_components)

output = {
    "detected_components": known_components,
    "unknown_components": unknown_components,
    "projects": [
        {
            "name": project["name"],
            "score": project["score"],
            "type": project["type"],
            "recommendation": project["label"],
            "description": project["description"],
            "components_used": project["components_used"],
            "why": project["why"],
        }
        for project in projects
    ],
    "feasibility_issues": feasibility_issues,
    "system_flow": system_flow,
    "suggestions": suggestions,
    "warnings": warnings,
}

print(json.dumps(output, ensure_ascii=False, indent=2))