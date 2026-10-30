from flask import Blueprint, request, jsonify, session
from services.build_service import BuildService

build_bp = Blueprint("build_api", __name__, url_prefix="/api/build-progress")

def get_current_user_id():
    return session.get("user_id", 1)

@build_bp.route("/<string:project_id>", methods=["GET"])
def get_session(project_id):
    """Get active session and step progress for a project."""
    try:
        user_id = get_current_user_id()
        result = BuildService.get_or_create_session(user_id=user_id, project_id=project_id)
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 404
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to load build session: {str(e)}"}), 500

@build_bp.route("", methods=["POST"])
def update_progress():
    """
    POST /api/build-progress
    Payload: { "session_id": 1, "step_number": 2, "completed": true }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        if not data or "session_id" not in data or "step_number" not in data:
            return jsonify({"status": "error", "message": "session_id and step_number are required"}), 400

        session_id = int(data["session_id"])
        step_number = int(data["step_number"])
        completed = bool(data.get("completed", True))

        result = BuildService.update_step_progress(
            session_id=session_id,
            step_number=step_number,
            completed=completed,
            user_id=user_id
        )

        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 400

        return jsonify({
            "status": "success",
            "message": f"Step {step_number} marked as {'completed' if completed else 'pending'}",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to record build step: {str(e)}"}), 500
