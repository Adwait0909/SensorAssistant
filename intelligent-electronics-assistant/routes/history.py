from flask import Blueprint, request, jsonify, session
from database.models import db, ProjectHistory, Project

history_bp = Blueprint("history_api", __name__, url_prefix="/api/history")

def get_current_user_id():
    return session.get("user_id", 1)

@history_bp.route("", methods=["GET"])
def get_user_history():
    user_id = get_current_user_id()
    action_filter = request.args.get("action")
    query = ProjectHistory.query.filter_by(user_id=user_id)
    if action_filter:
        query = query.filter_by(action=action_filter)
    records = query.order_by(ProjectHistory.timestamp.desc()).all()
    
    enriched = []
    for r in records:
        proj = Project.query.filter_by(id=r.project_id).first()
        item = r.to_dict()
        item["project_name"] = proj.name if proj else r.project_id
        item["project_category"] = proj.category if proj else "General"
        item["project_difficulty"] = proj.difficulty if proj else "Beginner"
        enriched.append(item)

    return jsonify({
        "status": "success",
        "count": len(enriched),
        "data": enriched
    }), 200

@history_bp.route("", methods=["POST"])
def record_history_action():
    """
    POST /api/history
    Record project action: 'saved', 'attempted', 'completed', 'failed', 'recommendation_viewed'
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        if not data or "project_id" not in data or "action" not in data:
            return jsonify({"status": "error", "message": "project_id and action are required"}), 400

        project_id = data["project_id"]
        action = data["action"]
        notes = data.get("notes", "")

        # If saving, prevent duplicate saves
        if action == "saved":
            existing = ProjectHistory.query.filter_by(user_id=user_id, project_id=project_id, action="saved").first()
            if existing:
                return jsonify({"status": "success", "message": "Project already in your saved list"}), 200

        record = ProjectHistory(
            user_id=user_id,
            project_id=project_id,
            action=action,
            notes=notes
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Recorded action '{action}' for project {project_id}",
            "data": record.to_dict()
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to record project history: {str(e)}"}), 500

@history_bp.route("/unsave/<string:project_id>", methods=["POST", "DELETE"])
def unsave_project(project_id):
    """Remove project from saved list."""
    try:
        user_id = get_current_user_id()
        records = ProjectHistory.query.filter_by(user_id=user_id, project_id=project_id, action="saved").all()
        for r in records:
            db.session.delete(r)
        db.session.commit()
        return jsonify({"status": "success", "message": "Project removed from saved list"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to unsave project: {str(e)}"}), 500
