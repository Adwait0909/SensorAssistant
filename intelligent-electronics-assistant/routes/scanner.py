import os
import io
import werkzeug.utils
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ml.predict_component import ComponentScannerPredictor

scanner_bp = Blueprint("scanner_api", __name__, url_prefix="/api/scanner")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@scanner_bp.route("/predict", methods=["POST"])
def predict_image():
    """
    POST /api/scanner/predict
    Expects multipart/form-data with key 'image' or 'file'.
    Secure validation: extension, file size, filename sanitization.
    """
    if "image" not in request.files and "file" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No image file provided in request",
            "model_available": ComponentScannerPredictor.is_model_available()
        }), 400

    file = request.files.get("image") or request.files.get("file")
    if not file or file.filename == "":
        return jsonify({
            "status": "error",
            "message": "Selected file is empty",
            "model_available": ComponentScannerPredictor.is_model_available()
        }), 400

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return jsonify({
            "status": "error",
            "message": f"Unsupported file type. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
            "model_available": ComponentScannerPredictor.is_model_available()
        }), 400

    try:
        image_bytes = file.read()
        if len(image_bytes) > MAX_FILE_SIZE:
            return jsonify({
                "status": "error",
                "message": "File exceeds maximum size limit of 16MB",
                "model_available": ComponentScannerPredictor.is_model_available()
            }), 400

        # Execute ML prediction pipeline
        prediction_result = ComponentScannerPredictor.predict(image_bytes)
        
        return jsonify({
            "status": "success" if prediction_result.get("model_available") else "model_not_trained",
            "data": prediction_result
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error scanning image: {str(e)}",
            "model_available": ComponentScannerPredictor.is_model_available()
        }), 500
