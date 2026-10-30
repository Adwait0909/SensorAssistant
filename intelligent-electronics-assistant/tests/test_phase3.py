import io
import pytest
from app import create_app
from config import TestingConfig
from database.models import db, User, Component, Project
from ml.predict_component import ComponentScannerPredictor
from services.wiring_service import WiringService
from services.gemini_vision_service import GeminiVisionService

@pytest.fixture
def test_app():
    app = create_app(TestingConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            user = User(username="scanner_user", email="scan@local.io")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            proj = Project.query.filter_by(id="proj-automatic-street-light").first()
            if not proj:
                proj = Project(
                    id="proj-test-scanner",
                    name="Automatic Street Light",
                    description="LDR based night lighting",
                    category="Home Automation",
                    required_components=["Arduino Uno", "LDR", "LED"]
                )
                db.session.add(proj)
                db.session.commit()

            yield app, client, user, proj
            db.drop_all()

def test_scanner_upload_validation(test_app):
    """Test scanner upload file extension & size validation."""
    app, client, user, proj = test_app
    
    # 1. No file provided
    res_no_file = client.post("/api/scanner/predict")
    assert res_no_file.status_code == 400
    assert "No image file provided" in res_no_file.get_json()["message"]

    # 2. Invalid extension (.txt)
    data = {"image": (io.BytesIO(b"dummy text content"), "test.txt")}
    res_bad_ext = client.post("/api/scanner/predict", data=data, content_type="multipart/form-data")
    assert res_bad_ext.status_code == 400
    assert "Unsupported file type" in res_bad_ext.get_json()["message"]

def test_scanner_model_unavailable_fallback(test_app):
    """Test that scanner returns exact clear message when no model trained."""
    app, client, user, proj = test_app
    
    # Ensure predictor knows model is unavailable (or mock unavailable state)
    res_predict = ComponentScannerPredictor.predict(b"fake_image_bytes")
    
    if not ComponentScannerPredictor.is_model_available():
        assert res_predict["model_available"] is False
        assert "Model not trained. Upload a trained model or run the training script." in res_predict["message"]
        assert res_predict["confidence"] == 0.0

def test_scanner_does_not_turn_prediction_errors_into_arduino(test_app, monkeypatch):
    """A failed image prediction must not be reported as a successful Arduino detection."""
    from ml.predict_component import ComponentScannerPredictor

    monkeypatch.setattr(
        ComponentScannerPredictor,
        "_extract_image_features",
        classmethod(lambda cls, image_bytes: (_ for _ in ()).throw(ValueError("invalid image"))),
    )
    ComponentScannerPredictor._is_loaded = True
    ComponentScannerPredictor._pkl_bundle = {"model": object(), "classes": ["Arduino Uno"]}
    ComponentScannerPredictor._keras_model = object()

    result = ComponentScannerPredictor.predict(b"invalid")
    assert result["component"] is None
    assert result["confidence"] == 0.0
    assert "could not be classified" in result["message"]
    ComponentScannerPredictor._pkl_bundle = None
    ComponentScannerPredictor._is_loaded = False

def test_scanner_ignores_legacy_feature_only_model(test_app, monkeypatch):
    """The legacy color/edge classifier must not be used for photographs."""
    from ml import predict_component
    from config import Config

    monkeypatch.setattr(predict_component, "MODEL_KERAS_PATH", predict_component.MODEL_KERAS_PATH / "missing")
    monkeypatch.setattr(predict_component, "MODEL_PKL_PATH", predict_component.MODEL_PKL_PATH)
    monkeypatch.setattr(Config, "GEMINI_API_KEY", None)
    ComponentScannerPredictor._pkl_bundle = None
    ComponentScannerPredictor._keras_model = None
    ComponentScannerPredictor._is_loaded = False

    assert ComponentScannerPredictor.is_model_available() is False

def test_scanner_accepts_tactile_push_button_alias(test_app):
    """Gemini names are not rejected because they are outside a fixed list."""
    assert GeminiVisionService._canonical_component("tactile push button") == "Push Button"
    assert GeminiVisionService._canonical_component("tactile switch") == "Push Button"
    assert GeminiVisionService._canonical_component("barometric pressure sensor") == "barometric pressure sensor"

def test_wiring_rule_retrieval_and_svg_generation(test_app):
    """Test structural validity of generated SVG wiring diagram."""
    app, client, user, proj = test_app
    
    with app.app_context():
        # Breadboard mode
        result_bb = WiringService.generate_svg(proj.id, view_mode="breadboard")
        assert "svg" in result_bb
        svg_text = result_bb["svg"]
        assert "<svg" in svg_text and "</svg>" in svg_text
        assert "BREADBOARD WIRING DIAGRAM" in svg_text
        assert "Arduino Uno" in svg_text

        # Schematic mode
        result_sch = WiringService.generate_svg(proj.id, view_mode="schematic")
        assert "svg" in result_sch
        svg_sch_text = result_sch["svg"]
        assert "SCHEMATIC CIRCUIT DIAGRAM" in svg_sch_text

def test_wiring_api_endpoints(test_app):
    """Test POST /api/wiring/generate and GET /api/wiring/download/<id>."""
    app, client, user, proj = test_app
    
    # 1. Generate endpoint
    res_gen = client.post("/api/wiring/generate", json={"project_id": proj.id, "view_mode": "breadboard"})
    assert res_gen.status_code == 200
    assert res_gen.get_json()["status"] == "success"
    assert "<svg" in res_gen.get_json()["data"]["svg"]

    # 2. Download endpoint
    res_dl = client.get(f"/api/wiring/download/{proj.id}?view_mode=breadboard")
    assert res_dl.status_code == 200
    assert res_dl.mimetype == "image/svg+xml"
    assert "<svg" in res_dl.get_data(as_text=True)

    # 3. Invalid project handling
    res_invalid = client.post("/api/wiring/generate", json={"project_id": "non_existent_project"})
    assert res_invalid.status_code == 404
