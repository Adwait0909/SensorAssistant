import json
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

class SafetyService:
    _rules_cache = None

    @classmethod
    def _load_rules(cls) -> List[Dict[str, Any]]:
        if cls._rules_cache is None:
            rules_path = DATA_DIR / "safety_rules.json"
            if rules_path.exists():
                with open(rules_path, "r", encoding="utf-8") as f:
                    cls._rules_cache = json.load(f)
            else:
                cls._rules_cache = []
        return cls._rules_cache

    @classmethod
    def evaluate_project_safety(cls, project_dict: Dict[str, Any], available_components: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Evaluate safety for a project given its required components and wiring rules.
        Detects:
        - excessive_voltage
        - incorrect_motor_supply
        - unsupported_current_draw
        - gsm_power
        - unsafe_relay_usage
        - missing_resistor
        - regulator_limitations
        - reverse_polarity
        - short_circuit
        - power_mismatch
        """
        rules = cls._load_rules()
        req_components = project_dict.get("required_components", [])
        opt_components = project_dict.get("optional_components", [])
        all_project_comps = set([c.lower().strip() for c in (req_components + opt_components)])
        
        wiring_rules_text = " ".join(project_dict.get("wiring_rules", [])).lower()
        project_desc = project_dict.get("description", "").lower()

        matched_warnings = []
        highest_severity = "Low"
        severity_rank = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}

        for rule in rules:
            target = rule.get("target", "").lower().strip()
            cat = rule.get("category", "")
            risk = rule.get("risk_level", "Medium")

            # Check if this rule's target component is used in this project
            target_present = any(target in comp for comp in all_project_comps)

            if target_present:
                # Specific contextual check
                warning_triggered = True

                # Missing resistor check for LED
                if cat == "missing_resistor" and target == "led":
                    # If resistor is explicitly listed as a required component, warning is advisory/info
                    has_resistor = any("resistor" in c for c in all_project_comps)
                    explanation = rule["rule"]
                    if has_resistor:
                        explanation += " Note: Current project includes series resistors in bill of materials."
                    
                    matched_warnings.append({
                        "id": rule["id"],
                        "category": cat,
                        "risk_level": risk if not has_resistor else "Low",
                        "title": rule.get("title", "Safety Warning"),
                        "explanation": explanation
                    })
                    if severity_rank.get(risk, 0) > severity_rank.get(highest_severity, 0) and not has_resistor:
                        highest_severity = risk
                    continue

                # Motor current check
                if cat == "incorrect_motor_supply":
                    warning_triggered = True

                if warning_triggered:
                    matched_warnings.append({
                        "id": rule["id"],
                        "category": cat,
                        "risk_level": risk,
                        "title": rule.get("title", "Safety Alert"),
                        "explanation": rule["rule"]
                    })
                    if severity_rank.get(risk, 0) > severity_rank.get(highest_severity, 0):
                        highest_severity = risk

        # Also incorporate any project-specific safety_rules defined in projects.json
        custom_rules = project_dict.get("safety_rules", [])
        for cr in custom_rules:
            matched_warnings.append({
                "id": "proj-custom-safety",
                "category": "project_guideline",
                "risk_level": "Medium",
                "title": "Circuit Rule",
                "explanation": cr
            })

        status_label = "Low Risk"
        if highest_severity == "Critical":
            status_label = "Critical Risk"
        elif highest_severity == "High":
            status_label = "High Risk"
        elif highest_severity == "Medium":
            status_label = "Moderate Risk"

        return {
            "status": status_label,
            "highest_severity": highest_severity,
            "warning_count": len(matched_warnings),
            "warnings": matched_warnings,
            "disclaimer": "Do not present dangerous electronics instructions as guaranteed safe. Always verify pin voltage and supply polarity before energizing."
        }
