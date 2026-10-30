import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from database.models import Component, Project
from services.component_service import ComponentService

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

class DependencyService:
    _alternatives_cache = None

    @classmethod
    def _load_alternatives(cls) -> Dict[str, List[Dict[str, Any]]]:
        if cls._alternatives_cache is None:
            alt_path = DATA_DIR / "alternatives.json"
            if alt_path.exists():
                with open(alt_path, "r", encoding="utf-8") as f:
                    cls._alternatives_cache = json.load(f)
            else:
                cls._alternatives_cache = {}
        return cls._alternatives_cache

    @classmethod
    def get_component_alternatives(cls, component_name: str, mode: str = "prototype") -> List[Dict[str, Any]]:
        """Retrieve compatible alternative components filtered by mode."""
        alts_map = cls._load_alternatives()
        clean_name = component_name.strip()
        matching = alts_map.get(clean_name, [])
        if not matching:
            # try fuzzy matching
            for k, v in alts_map.items():
                if k.lower() in clean_name.lower() or clean_name.lower() in k.lower():
                    matching = v
                    break
        
        if mode and mode != "all":
            return [alt for alt in matching if alt.get("mode") == mode or "mode" not in alt]
        return matching

    @classmethod
    def analyze_project_dependencies(cls, project_id: str, user_id: Optional[int] = None, mode: str = "prototype", custom_components: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze dependencies for a given project:
        - Available components (with stock count)
        - Missing components (with alternative options)
        - Optional components
        - Supporting electrical dependencies (e.g. pullups, decoupling, drivers)
        """
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return {"error": f"Project '{project_id}' not found"}

        user_comp_map = {}

        if custom_components is not None:
            # Match directly against user entered custom component names
            for comp_str in custom_components:
                if isinstance(comp_str, str) and comp_str.strip():
                    c_clean = comp_str.strip()
                    norm_name = ComponentService.normalize_name(c_clean)
                    user_comp_map[norm_name.lower().strip()] = {
                        "name": norm_name,
                        "quantity": 1,
                        "voltage": "5V",
                        "cost": 50.0
                    }
                    user_comp_map[c_clean.lower().strip()] = {
                        "name": norm_name,
                        "quantity": 1,
                        "voltage": "5V",
                        "cost": 50.0
                    }
        else:
            user_comps = ComponentService.get_components(user_id=user_id)
            # Normalize available names and map to component model
            for c in user_comps:
                if c.quantity > 0:
                    user_comp_map[c.name.lower().strip()] = {
                        "name": c.name,
                        "quantity": c.quantity,
                        "voltage": c.voltage or "5V",
                        "cost": c.cost or 40.0
                    }
                    # Also include aliases
                    for a in (c.aliases or []):
                        user_comp_map[a.lower().strip()] = {
                            "name": c.name,
                            "quantity": c.quantity,
                            "voltage": c.voltage or "5V",
                            "cost": c.cost or 40.0
                        }

        req_components = project.required_components or []
        opt_components = project.optional_components or []

        available_list = []
        missing_list = []
        optional_list = []

        # Check required
        for req in req_components:
            req_clean = req.lower().strip()
            # Direct or alias match
            matched_comp = None
            if req_clean in user_comp_map:
                matched_comp = user_comp_map[req_clean]
            else:
                # Substring match (e.g. 'Arduino' in 'Arduino Uno', 'MQ-2' in 'MQ-2 Gas Sensor')
                for k, comp_dict in user_comp_map.items():
                    if k in req_clean or req_clean in k:
                        matched_comp = comp_dict
                        break

            if matched_comp and matched_comp["quantity"] > 0:
                available_list.append({
                    "name": req,
                    "matched_as": matched_comp["name"],
                    "stock": matched_comp["quantity"],
                    "status": "available",
                    "voltage": matched_comp["voltage"],
                    "cost": matched_comp["cost"],
                    "indicator": "✓ Available"
                })
            else:
                alternatives = cls.get_component_alternatives(req, mode=mode)
                missing_list.append({
                    "name": req,
                    "status": "missing",
                    "indicator": "⚠ Missing",
                    "alternatives": alternatives
                })

        # Check optional
        for opt in opt_components:
            opt_clean = opt.lower().strip()
            is_avail = opt_clean in user_comp_map or any(opt_clean in k for k in user_comp_map)
            optional_list.append({
                "name": opt,
                "status": "available" if is_avail else "optional_missing",
                "indicator": "○ Optional"
            })

        # Parse supporting dependencies
        supporting_deps = []
        raw_deps = project.dependencies or {}
        for dep_key, dep_desc in raw_deps.items():
            supporting_deps.append({
                "key": dep_key,
                "description": dep_desc
            })

        total_req = len(req_components)
        avail_count = len(available_list)
        feasibility_percent = round((avail_count / total_req * 100) if total_req > 0 else 100, 1)

        return {
            "project_id": project.id,
            "project_name": project.name,
            "feasibility_percent": feasibility_percent,
            "summary": f"{avail_count}/{total_req} components available",
            "available_components": available_list,
            "missing_components": missing_list,
            "optional_components": optional_list,
            "supporting_dependencies": supporting_deps,
            "all_required_met": len(missing_list) == 0
        }
