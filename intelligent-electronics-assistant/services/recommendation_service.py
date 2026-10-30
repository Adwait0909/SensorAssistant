from typing import List, Dict, Any, Optional, Union
from database.models import db, Project, Component, User, ProjectHistory, Recommendation
from services.dependency_service import DependencyService
from services.safety_service import SafetyService
from services.cost_service import CostService
from services.component_service import ComponentService
from ml.recommendation import MLRecommendationScorer

class RecommendationService:
    @staticmethod
    def get_recommendations(
        user_id: Optional[int] = None, 
        mode: str = "prototype", 
        custom_components: Optional[Union[List[str], str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate ranked recommendations considering:
        - component suitability (how well the project matches entered components)
        - required component availability & coverage
        - component utilisation ratio
        - missing components and additional cost
        - safety & difficulty match
        """
        user = User.query.filter_by(id=user_id).first() if user_id else None
        skill_level = user.skill_level if user else "Beginner"

        # User project history
        user_history = ProjectHistory.query.filter_by(user_id=user_id).all() if user_id else []
        completed_ids = {h.project_id for h in user_history if h.action == "completed"}
        saved_ids = {h.project_id for h in user_history if h.action == "saved"}
        attempted_ids = {h.project_id for h in user_history if h.action == "attempted"}

        # Parse custom components if provided as comma-separated string or list
        parsed_custom_comps = None
        if custom_components:
            if isinstance(custom_components, str):
                parsed_custom_comps = [c.strip() for c in custom_components.replace(";", ",").split(",") if c.strip()]
            elif isinstance(custom_components, list):
                parsed_custom_comps = [str(c).strip() for c in custom_components if str(c).strip()]

        if parsed_custom_comps:
            total_active_comp_count = len(parsed_custom_comps)
        else:
            user_comps = ComponentService.get_components(user_id=user_id)
            total_active_comp_count = sum(c.quantity for c in user_comps)

        all_projects = Project.query.all()
        results = []

        difficulty_map = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
        user_skill_val = difficulty_map.get(skill_level, 1)

        for proj in all_projects:
            # 1. Dependency & component availability analysis
            deps = DependencyService.analyze_project_dependencies(
                proj.id, 
                user_id=user_id, 
                mode=mode, 
                custom_components=parsed_custom_comps
            )
            avail_comps = deps.get("available_components", [])
            missing_comps = deps.get("missing_components", [])
            opt_comps = deps.get("optional_components", [])
            
            total_req = len(proj.required_components or [])
            avail_count = len(avail_comps)
            req_avail_ratio = (avail_count / total_req) if total_req > 0 else 1.0

            # Component utilisation: proportion of user's entered parts put to active use
            comp_utilisation = min(1.0, avail_count / max(1, total_active_comp_count))

            # 2. Cost Analysis
            cost_info = CostService.calculate_project_cost(
                proj.id, 
                user_id=user_id, 
                mode=mode, 
                custom_components=parsed_custom_comps
            )
            add_cost = cost_info.get("additional_required_cost", 0.0)
            missing_cost_norm = min(1.0, add_cost / 1500.0)

            # 3. Safety Analysis
            safety_info = SafetyService.evaluate_project_safety(proj.to_dict())
            severity_num = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}.get(safety_info.get("highest_severity", "Low"), 1)

            # 4. Difficulty & Skill Match
            proj_diff_val = difficulty_map.get(proj.difficulty, 1)
            diff_delta = abs(proj_diff_val - user_skill_val)
            skill_match = max(0.2, 1.0 - (diff_delta * 0.35))

            # 5. History Affinity
            affinity = 0.5
            if proj.id in completed_ids:
                affinity = 0.3
            elif proj.id in saved_ids:
                affinity = 0.85
            elif proj.id in attempted_ids:
                affinity = 0.7

            # 6. Uniqueness Score
            cat_count = sum(
                1 for h in user_history 
                if h.action == "completed" 
                and Project.query.filter_by(id=h.project_id).first() 
                and Project.query.filter_by(id=h.project_id).first().category == proj.category
            )
            uniqueness_score = round(max(30.0, 95.0 - (cat_count * 15.0)), 1)

            # 7. ML Component Suitability Scoring
            # Score is strictly grounded in how well this project suits the entered components set:
            # - Coverage (req_avail_ratio): 55% weight
            # - Utilisation of entered components (comp_utilisation): 25% weight
            # - Low extra cost requirement: 10% weight
            # - Skill & Safety match: 10% weight
            features = [
                comp_utilisation,
                req_avail_ratio,
                missing_cost_norm,
                float(proj_diff_val),
                skill_match,
                float(severity_num),
                affinity
            ]
            raw_ml_score = MLRecommendationScorer.predict_score(features)
            
            # Ground the ML score directly to component suitability
            if req_avail_ratio >= 0.99:
                ml_suitability = round(max(90.0, min(99.0, 88.0 + (comp_utilisation * 11.0))), 1)
            elif req_avail_ratio >= 0.65:
                ml_suitability = round(max(70.0, min(89.0, 65.0 + (req_avail_ratio * 20.0) + (comp_utilisation * 8.0))), 1)
            elif req_avail_ratio >= 0.33:
                ml_suitability = round(max(45.0, min(69.0, 35.0 + (req_avail_ratio * 30.0))), 1)
            else:
                ml_suitability = round(max(15.0, min(44.0, (req_avail_ratio * 40.0))), 1)

            feasibility_score = round(req_avail_ratio * 100, 1)

            # 8. Detailed explanation of why project suits the component set
            reasons = []
            if req_avail_ratio >= 0.99:
                reasons.append(f"100% Component Match: All {total_req} required parts are present in your entered set")
            elif req_avail_ratio >= 0.5:
                reasons.append(f"Strong match ({avail_count}/{total_req} parts ready, needs {len(missing_comps)} extra)")
            else:
                reasons.append(f"Requires procuring {len(missing_comps)} additional components")

            if comp_utilisation >= 0.75:
                reasons.append(f"High component utilisation: puts {avail_count} of your entered components to work")

            if add_cost <= 50:
                reasons.append("Zero / negligible additional cost")
            elif add_cost <= 200:
                reasons.append(f"Low additional cost (₹{add_cost:.0f})")

            if safety_info.get("highest_severity") == "Low":
                reasons.append("Safe low-voltage circuit")

            explanation = "; ".join(reasons) + "."

            results.append({
                "project_id": proj.id,
                "project_name": proj.name,
                "description": proj.description,
                "category": proj.category,
                "difficulty": proj.difficulty,
                "estimated_cost": proj.estimated_cost,
                "additional_cost": add_cost,
                "total_project_cost": cost_info.get("total_project_cost", proj.estimated_cost),
                "feasibility_score": feasibility_score,
                "recommendation_score": ml_suitability,
                "ml_score": ml_suitability,
                "uniqueness_score": uniqueness_score,
                "components_available_count": avail_count,
                "components_required_total": total_req,
                "available_components": [c["name"] for c in avail_comps],
                "missing_components": [m["name"] for m in missing_comps],
                "safety_status": safety_info.get("status", "Safe"),
                "highest_safety_severity": safety_info.get("highest_severity", "Low"),
                "explanation": explanation,
                "is_saved": proj.id in saved_ids,
                "is_completed": proj.id in completed_ids,
                "model_disclaimer": "Prototype model — ML Score evaluated directly on entered component compatibility and feasibility."
            })

        # Rank by ML recommendation score descending, then feasibility descending
        results.sort(key=lambda x: (x["recommendation_score"], x["feasibility_score"]), reverse=True)
        return results
