from typing import List, Dict, Any, Optional
from database.models import Component, Project
from services.dependency_service import DependencyService
from services.component_service import ComponentService

class CostService:
    @staticmethod
    def calculate_project_cost(project_id: str, user_id: Optional[int] = None, mode: str = "prototype", custom_components: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calculate:
        - Current component cost (components already owned in inventory)
        - Additional required cost (cost to acquire missing components)
        - Total project cost
        - Low-cost alternatives depending on mode (Prototype vs Production)
        """
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return {"error": f"Project '{project_id}' not found"}

        dep_analysis = DependencyService.analyze_project_dependencies(project_id, user_id=user_id, mode=mode, custom_components=custom_components)
        available_comps = dep_analysis.get("available_components", [])
        missing_comps = dep_analysis.get("missing_components", [])

        # Catalog lookup helper for default pricing
        all_catalog = Component.query.all()
        catalog_map = {c.name.lower().strip(): c.cost for c in all_catalog if c.cost}

        # 1. Cost of components already owned
        current_component_cost = 0.0
        for comp in available_comps:
            cost = comp.get("cost")
            if cost is None or cost == 0.0:
                cost = catalog_map.get(comp["name"].lower().strip(), 30.0)
            current_component_cost += float(cost)

        # 2. Cost of missing components
        additional_required_cost = 0.0
        missing_cost_breakdown = []
        for m in missing_comps:
            name = m["name"]
            base_cost = catalog_map.get(name.lower().strip(), 60.0)
            
            # Check if there is an alternative for the selected mode
            alts = m.get("alternatives", [])
            recommended_alt = None
            if alts:
                # pick lowest cost for prototype, or highest reliability for production
                if mode == "prototype":
                    recommended_alt = min(alts, key=lambda x: x.get("cost", 999999))
                else:
                    recommended_alt = alts[0]

            item_cost = recommended_alt["cost"] if (recommended_alt and "cost" in recommended_alt) else base_cost
            additional_required_cost += float(item_cost)

            missing_cost_breakdown.append({
                "component": name,
                "standard_cost": base_cost,
                "selected_cost": item_cost,
                "recommended_alternative": recommended_alt
            })

        total_project_cost = current_component_cost + additional_required_cost

        return {
            "project_id": project.id,
            "project_name": project.name,
            "mode": mode,
            "current_component_cost": round(current_component_cost, 2),
            "additional_required_cost": round(additional_required_cost, 2),
            "total_project_cost": round(total_project_cost, 2),
            "savings_from_inventory": round(current_component_cost, 2),
            "missing_breakdown": missing_cost_breakdown,
            "cost_saving_tip": "Prototype mode prioritizes lower cost compatible alternatives, while Production mode selects industrial-grade components."
        }
