from typing import List, Dict, Any, Optional
from database.models import db, Project, ProjectComponent, Component

class ProjectService:
    @staticmethod
    def get_all_projects(category: Optional[str] = None, difficulty: Optional[str] = None) -> List[Project]:
        query = Project.query
        if category and category != "All":
            query = query.filter_by(category=category)
        if difficulty and difficulty != "All":
            query = query.filter_by(difficulty=difficulty)
        return query.order_by(Project.name).all()

    @staticmethod
    def get_all(category: Optional[str] = None, difficulty: Optional[str] = None) -> List[Project]:
        return ProjectService.get_all_projects(category=category, difficulty=difficulty)

    @staticmethod
    def get_by_id(project_id: str) -> Optional[Project]:
        return Project.query.filter_by(id=project_id).first()

    @staticmethod
    def check_project_feasibility(project_id: str, available_component_names: List[str]) -> Dict[str, Any]:
        """Compute feasibility score and list missing components."""
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return {"error": "Project not found"}

        reqs = project.required_components or []
        opts = project.optional_components or []
        
        # Lowercase normalize for comparison
        available_set = {name.lower().strip() for name in available_component_names}
        
        matched_req = [c for c in reqs if c.lower().strip() in available_set]
        missing_req = [c for c in reqs if c.lower().strip() not in available_set]
        matched_opt = [c for c in opts if c.lower().strip() in available_set]
        
        total_req = len(reqs)
        match_count = len(matched_req)
        
        feasibility_score = round((match_count / total_req * 100) if total_req > 0 else 100, 1)

        # Estimate missing component cost
        missing_cost = 0.0
        for m_name in missing_req:
            comp = Component.query.filter(Component.name.ilike(m_name)).first()
            if comp and comp.cost:
                missing_cost += comp.cost
            else:
                missing_cost += 50.0  # reasonable placeholder

        return {
            "project_id": project.id,
            "project_name": project.name,
            "difficulty": project.difficulty,
            "category": project.category,
            "feasibility_score": feasibility_score,
            "total_required": total_req,
            "matched_required_count": match_count,
            "matched_components": matched_req,
            "missing_components": missing_req,
            "optional_available": matched_opt,
            "additional_cost": round(missing_cost, 2),
            "safety_rules_count": len(project.safety_rules or []),
            "dependencies": project.dependencies or {}
        }
