import os
import werkzeug.utils
from pathlib import Path
from flask import Blueprint, request, jsonify, session, current_app
from services.diagnosis_service import DiagnosisService
from database.models import db, DiagnosisHistory, ProjectHistory

diagnosis_bp = Blueprint("diagnosis", __name__, url_prefix="/api/diagnosis")

def get_current_user_id() -> int:
    return session.get("user_id", 1)

@diagnosis_bp.route("", methods=["POST"])
@diagnosis_bp.route("/analyze", methods=["POST"])
def analyze_diagnosis():
    user_id = get_current_user_id()

    image_filename = None
    if request.is_json:
        data = request.get_json() or {}
        symptom_text = data.get("symptom_text", "")
        project_id = data.get("project_id")
        component_name = data.get("component_name")
        observed_symptoms = data.get("observed_symptoms", [])
    else:
        symptom_text = request.form.get("symptom_text", "")
        project_id = request.form.get("project_id")
        component_name = request.form.get("component_name")
        symptoms_raw = request.form.get("observed_symptoms", "")
        observed_symptoms = [s.strip() for s in symptoms_raw.split(",") if s.strip()] if symptoms_raw else []

        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename:
                sec_filename = werkzeug.utils.secure_filename(file.filename)
                upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
                upload_folder.mkdir(parents=True, exist_ok=True)
                file_path = upload_folder / f"diag_{user_id}_{sec_filename}"
                file.save(file_path)
                image_filename = str(file_path.name)

    if not symptom_text:
        return jsonify({"status": "error", "message": "Please describe the observed symptom or issue."}), 400

    result = DiagnosisService.diagnose_issue(
        user_id=user_id,
        symptom_text=symptom_text,
        project_id=project_id,
        component_name=component_name,
        observed_symptoms=observed_symptoms
    )

    if image_filename:
        result["attached_image"] = image_filename

    # Log user history
    try:
        ph = ProjectHistory(
            user_id=user_id,
            project_id=project_id or "Custom Circuit",
            action="diagnosed",
            notes=f"Diagnosed symptom: '{symptom_text[:50]}...'"
        )
        db.session.add(ph)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({"status": "success", "data": result})

@diagnosis_bp.route("/history", methods=["GET"])
def get_diagnosis_history():
    user_id = get_current_user_id()
    history = DiagnosisHistory.query.filter_by(user_id=user_id).order_by(DiagnosisHistory.created_at.desc()).limit(10).all()
    
    items = []
    for h in history:
        items.append({
            "id": h.id,
            "symptom": h.symptom,
            "suggested_fix": h.suggested_fix,
            "resolved": getattr(h, "resolved", False),
            "timestamp": h.created_at.strftime("%Y-%m-%d %H:%M:%S") if h.created_at else "Recently"
        })

    return jsonify({"status": "success", "history": items})
