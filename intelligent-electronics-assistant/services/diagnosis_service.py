import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from database.models import db, DiagnosisRule, DiagnosisHistory, Project, Component

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

class DiagnosisService:
    _rules_cache = None

    @classmethod
    def _load_rules(cls) -> List[Dict[str, Any]]:
        if cls._rules_cache is None:
            rules_path = DATA_DIR / "diagnosis_rules.json"
            if rules_path.exists():
                with open(rules_path, "r", encoding="utf-8") as f:
                    cls._rules_cache = json.load(f)
            else:
                cls._rules_cache = []
        return cls._rules_cache

    @classmethod
    def diagnose_issue(
        cls,
        user_id: Optional[int],
        symptom_text: str,
        project_id: Optional[str] = None,
        component_name: Optional[str] = None,
        observed_symptoms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze circuit failure using:
        1. Rule-based troubleshooting & knowledge base matching
        2. Component specifications
        3. Known failure patterns
        4. Structured step-by-step diagnostic resolution (teaches troubleshooting)
        """
        rules = cls._load_rules()
        query_text = (symptom_text or "").lower()
        if observed_symptoms:
            query_text += " " + " ".join(observed_symptoms).lower()
        if component_name:
            query_text += " " + component_name.lower()

        matched_rule = None
        best_score = 0

        for r in rules:
            score = 0
            symptom_pattern = r.get("symptom", "").lower()
            comp_pattern = r.get("component", "").lower()
            prob_pattern = r.get("problem", "").lower()

            if comp_pattern and comp_pattern in query_text:
                score += 30
            if symptom_pattern and any(word in query_text for word in symptom_pattern.split()):
                score += 40
            if prob_pattern and any(word in query_text for word in prob_pattern.split()):
                score += 20

            if score > best_score:
                best_score = score
                matched_rule = r

        # Retrieve project context if provided
        project_obj = Project.query.filter_by(id=project_id).first() if project_id else None

        if matched_rule and best_score >= 20:
            problem = matched_rule.get("problem", matched_rule.get("symptom"))
            causes = matched_rule.get("causes", [])
            priority = matched_rule.get("priority", "Medium")
            tests = matched_rule.get("tests_to_perform", [])
            steps = matched_rule.get("steps", [])
            comp_ref = matched_rule.get("component", component_name or "General")
        else:
            # Fallback rule-based synthesis for unmatched custom symptoms
            comp_ref = component_name or "Component"
            problem = f"Observed malfunction on {comp_ref}: '{symptom_text}'"
            priority = "Medium"
            causes = [
                f"Loose connection or poor solder joint on {comp_ref} terminals",
                "Unstable power supply voltage or common ground path missing",
                "Pin assignment mismatch between firmware code and physical wiring",
                "ESD damage or thermal overload on component IC"
            ]
            tests = [
                "Measure DC operating voltage at component VCC and GND pins using multimeter",
                "Verify continuity of all signal jumper wires",
                "Inspect micro-controller serial monitor logs for error tracebacks"
            ]
            steps = [
                "Power Off: disconnect battery/USB power source before modifying connections.",
                "Inspect Pinout: verify signal, power, and ground leads match project schematic.",
                "Check Grounding: confirm common ground lead connects microcontroller and external modules.",
                "Re-test: apply power and observe if status indicators illuminate."
            ]

        # Record diagnosis history in database
        try:
            record = DiagnosisHistory(
                user_id=user_id,
                symptom=symptom_text,
                suggested_fix="; ".join(steps[:2])
            )
            db.session.add(record)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return {
            "problem": problem,
            "component": comp_ref,
            "project_name": project_obj.name if project_obj else "Custom Circuit",
            "priority": priority,
            "possible_causes": causes,
            "tests_to_perform": tests,
            "diagnostic_steps": steps,
            "matched_by": "Rule-based & specification analysis" if matched_rule else "Synthesized diagnostic engine"
        }
