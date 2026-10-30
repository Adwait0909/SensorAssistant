from typing import List, Dict, Any, Optional
from database.models import db, User, Component, Project, ProjectHistory, BuildSession, UserPreference

class MemoryService:
    @staticmethod
    def get_user_memory_profile(user_id: int) -> Dict[str, Any]:
        """
        Track maker workshop memory telemetry:
        - components owned
        - projects attempted
        - projects completed
        - saved projects
        - preferred difficulty
        - historical category distribution
        """
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {"error": "User not found"}

        components = Component.query.filter_by(user_id=user_id).all()
        history = ProjectHistory.query.filter_by(user_id=user_id).order_by(ProjectHistory.timestamp.desc()).all()

        owned_comps = [c.name for c in components if c.quantity > 0]
        completed_records = [h for h in history if h.action == "completed"]
        attempted_records = [h for h in history if h.action == "attempted"]
        saved_records = [h for h in history if h.action == "saved"]

        completed_ids = list({h.project_id for h in completed_records})
        attempted_ids = list({h.project_id for h in attempted_records})
        saved_ids = list({h.project_id for h in saved_records})

        pref = UserPreference.query.filter_by(user_id=user_id).first()

        # Category frequency analysis
        category_counts = {}
        for h in completed_records:
            proj = Project.query.filter_by(id=h.project_id).first()
            if proj:
                category_counts[proj.category] = category_counts.get(proj.category, 0) + 1

        # Determine skill progression signal
        mcu_built = set()
        for cid in completed_ids:
            p = Project.query.filter_by(id=cid).first()
            if p:
                for req in (p.required_components or []):
                    if "Arduino" in req or "ESP32" in req or "Raspberry" in req:
                        mcu_built.add(req)

        recommendation_insight = ""
        if len(completed_ids) >= 2 and "Arduino Uno" in mcu_built and "ESP32" not in mcu_built:
            recommendation_insight = "Based on your completed Arduino beginner projects, future recommendations prioritize ESP32 projects with a gradual increase in difficulty."
        elif len(completed_ids) == 0:
            recommendation_insight = "Welcome to your workshop! Recommendations start with fundamental beginner projects using your available parts."
        else:
            recommendation_insight = f"Based on your {len(completed_ids)} completed projects, recommendations adapt to your expanding component inventory."

        return {
            "user_id": user.id,
            "username": user.username,
            "skill_level": user.skill_level,
            "mode": pref.mode if pref else "prototype",
            "owned_components_count": len(owned_comps),
            "owned_components": owned_comps,
            "completed_projects_count": len(completed_ids),
            "completed_project_ids": completed_ids,
            "attempted_projects_count": len(attempted_ids),
            "saved_projects_count": len(saved_ids),
            "category_distribution": category_counts,
            "recommendation_insight": recommendation_insight
        }
