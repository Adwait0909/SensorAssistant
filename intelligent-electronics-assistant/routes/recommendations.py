from flask import Blueprint, request, jsonify, session
from services.recommendation_service import RecommendationService

recommendations_bp = Blueprint("recommendations_api", __name__, url_prefix="/api/recommendations")

@recommendations_bp.route("", methods=["POST", "GET"])
def get_recommendations():
    """
    POST /api/recommendations
    Generate multi-factor recommendations with transparent ML suitability scoring (0-100)
    grounded in the user's entered component set.
    """
    try:
        user_id = session.get("user_id", 1)
        data = request.get_json(silent=True) or {}
        mode = data.get("mode") or request.args.get("mode", "prototype")
        
        # User entered components (array of strings, or comma-separated string)
        custom_components = data.get("components") or data.get("custom_components") or request.args.get("components")

        recommendations = RecommendationService.get_recommendations(
            user_id=user_id, 
            mode=mode, 
            custom_components=custom_components
        )
        
        return jsonify({
            "status": "success",
            "count": len(recommendations),
            "mode": mode,
            "components_evaluated": custom_components,
            "disclaimer": "ML Score directly evaluates how well the project suits the entered components set.",
            "data": recommendations
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to generate recommendations: {str(e)}"}), 500
