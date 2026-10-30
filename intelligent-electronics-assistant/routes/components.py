from flask import Blueprint, request, jsonify, session
from services.component_service import ComponentService
from database.models import User

components_bp = Blueprint("components_api", __name__, url_prefix="/api/components")

def get_current_user_id():
    return session.get("user_id", 1)  # Default to demo user (id 1) if not logged in

@components_bp.route("", methods=["GET"])
def list_components():
    try:
        user_id = get_current_user_id()
        category = request.args.get("category")
        voltage = request.args.get("voltage")
        availability = request.args.get("availability")
        search = request.args.get("search")

        comps = ComponentService.get_components(
            user_id=user_id,
            category=category,
            voltage=voltage,
            availability=availability,
            search=search
        )
        return jsonify({
            "status": "success",
            "count": len(comps),
            "data": [c.to_dict() for c in comps]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to retrieve components: {str(e)}"}), 500

@components_bp.route("/<string:comp_id>", methods=["GET"])
def get_component(comp_id):
    comp = ComponentService.get_by_id(comp_id)
    if not comp:
        return jsonify({"status": "error", "message": "Component not found"}), 404
    return jsonify({"status": "success", "data": comp.to_dict()}), 200

@components_bp.route("", methods=["POST"])
def create_component():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"status": "error", "message": "Component name is required"}), 400

    try:
        user_id = get_current_user_id()
        comp = ComponentService.create_component(data, user_id=user_id)
        return jsonify({
            "status": "success",
            "message": "Component saved successfully",
            "data": comp.to_dict()
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not create component: {str(e)}"}), 500

@components_bp.route("/<string:comp_id>", methods=["PUT"])
def update_component(comp_id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    try:
        comp = ComponentService.update_component(comp_id, data)
        if not comp:
            return jsonify({"status": "error", "message": "Component not found"}), 404
        return jsonify({
            "status": "success",
            "message": "Component updated successfully",
            "data": comp.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to update component: {str(e)}"}), 500

@components_bp.route("/<string:comp_id>", methods=["DELETE"])
def delete_component(comp_id):
    try:
        success = ComponentService.delete_component(comp_id)
        if not success:
            return jsonify({"status": "error", "message": "Component not found"}), 404
        return jsonify({"status": "success", "message": "Component deleted"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to delete component: {str(e)}"}), 500
