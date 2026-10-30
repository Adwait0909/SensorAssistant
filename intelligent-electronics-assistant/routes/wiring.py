from flask import Blueprint, request, jsonify, Response
from services.wiring_service import WiringService

wiring_bp = Blueprint("wiring_api", __name__, url_prefix="/api/wiring")


@wiring_bp.route("/generate", methods=["POST"])
def generate_diagram():
    """
    POST /api/wiring/generate
    Body: { "project_id": "proj-automatic-street-light", "view_mode": "breadboard" }
    Returns: { status, data: { svg, valid, checks, components_used, ... } }
    """
    data = request.get_json() or {}
    project_id = data.get("project_id") or request.args.get("project_id")
    view_mode  = data.get("view_mode")  or request.args.get("view_mode", "breadboard")

    if not project_id:
        return jsonify({"status": "error", "message": "project_id is required"}), 400

    try:
        result = WiringService.generate_svg(project_id, view_mode=view_mode)
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 404
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to generate diagram: {e}"}), 500


@wiring_bp.route("/both", methods=["POST"])
def generate_both():
    """
    POST /api/wiring/both
    Body: { "project_id": "..." }
    Returns both SVGs + validation in one request.
    """
    data = request.get_json() or {}
    project_id = data.get("project_id") or request.args.get("project_id")

    if not project_id:
        return jsonify({"status": "error", "message": "project_id is required"}), 400

    try:
        result = WiringService.generate_both_views(project_id)
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 404
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to generate diagrams: {e}"}), 500


@wiring_bp.route("/download/<string:project_id>", methods=["GET"])
def download_svg(project_id):
    """Download SVG file directly."""
    view_mode = request.args.get("view_mode", "breadboard")
    result = WiringService.generate_svg(project_id, view_mode=view_mode)
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]}), 404

    return Response(
        result["svg"],
        mimetype="image/svg+xml",
        headers={"Content-Disposition": f"attachment; filename={project_id}_{view_mode}_wiring.svg"}
    )
