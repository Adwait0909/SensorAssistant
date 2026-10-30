from flask import Blueprint, request, jsonify, session
from services.project_service import ProjectService
from services.dependency_service import DependencyService
from services.safety_service import SafetyService
from services.cost_service import CostService
from services.component_service import ComponentService
from database.models import Project

projects_bp = Blueprint("projects_api", __name__, url_prefix="/api/projects")

def get_current_user_id():
    return session.get("user_id", 1)

@projects_bp.route("", methods=["GET"])
def list_projects():
    try:
        category = request.args.get("category")
        difficulty = request.args.get("difficulty")
        projects = ProjectService.get_all_projects(category=category, difficulty=difficulty)
        return jsonify({
            "status": "success",
            "count": len(projects),
            "data": [p.to_dict() for p in projects]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to list projects: {str(e)}"}), 500

@projects_bp.route("/<string:project_id>", methods=["GET"])
def get_project(project_id):
    project = ProjectService.get_by_id(project_id)
    if not project:
        return jsonify({"status": "error", "message": "Project not found"}), 404
    return jsonify({"status": "success", "data": project.to_dict()}), 200

@projects_bp.route("/<string:project_id>/dependencies", methods=["GET"])
def get_dependencies(project_id):
    try:
        user_id = get_current_user_id()
        mode = request.args.get("mode", "prototype")
        analysis = DependencyService.analyze_project_dependencies(project_id, user_id=user_id, mode=mode)
        if "error" in analysis:
            return jsonify({"status": "error", "message": analysis["error"]}), 404
        return jsonify({"status": "success", "data": analysis}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Dependency analysis failed: {str(e)}"}), 500

@projects_bp.route("/<string:project_id>/safety", methods=["GET"])
def get_safety(project_id):
    try:
        project = ProjectService.get_by_id(project_id)
        if not project:
            return jsonify({"status": "error", "message": "Project not found"}), 404
        safety = SafetyService.evaluate_project_safety(project.to_dict())
        return jsonify({"status": "success", "data": safety}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Safety analysis failed: {str(e)}"}), 500

@projects_bp.route("/<string:project_id>/cost", methods=["GET"])
def get_cost(project_id):
    try:
        user_id = get_current_user_id()
        mode = request.args.get("mode", "prototype")
        cost = CostService.calculate_project_cost(project_id, user_id=user_id, mode=mode)
        if "error" in cost:
            return jsonify({"status": "error", "message": cost["error"]}), 404
        return jsonify({"status": "success", "data": cost}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Cost calculation failed: {str(e)}"}), 500

@projects_bp.route("/<string:project_id>/feasibility", methods=["GET"])
def check_feasibility(project_id):
    try:
        user_id = get_current_user_id()
        comps = ComponentService.get_components(user_id=user_id)
        user_component_names = [c.name for c in comps if c.quantity > 0]
        result = ProjectService.check_project_feasibility(project_id, user_component_names)
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to evaluate feasibility: {str(e)}"}), 500
