import pytest
from app import create_app
from config import Config
from database.models import db, User, Component, Project, DiagnosisRule, ProjectHistory, ChatHistory
from services.diagnosis_service import DiagnosisService
from services.rag_service import LocalRAGService
from services.memory_service import MemoryService
from services.recommendation_service import RecommendationService

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    OPENAI_API_KEY = None  # Explicitly test local offline RAG fallback

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Ensure base user exists
            user = User.query.filter_by(id=1).first()
            if not user:
                user = User(id=1, username="testuser", email="test@example.com", password_hash="hash")
                db.session.add(user)
                db.session.commit()
            
            # Seed test component if missing
            comp = Component.query.filter_by(id="comp-ard-uno").first()
            if not comp:
                comp = Component(
                    id="comp-ard-uno",
                    user_id=1,
                    name="Arduino Uno",
                    category="Microcontroller",
                    quantity=2,
                    voltage="5V",
                    description="ATmega328P microcontroller development board",
                    safety_notes="Do not exceed 12V DC input on VIN pin"
                )
                db.session.add(comp)
                db.session.commit()

        yield client

def test_diagnosis_service_rule_match(client):
    """Test rule-based circuit failure diagnosis matching."""
    with client.application.app_context():
        result = DiagnosisService.diagnose_issue(
            user_id=1,
            symptom_text="LED is not turning ON",
            component_name="LED"
        )
        assert result is not None
        assert "problem" in result
        assert "possible_causes" in result
        assert "diagnostic_steps" in result
        assert len(result["diagnostic_steps"]) > 0

def test_diagnosis_api_endpoint(client):
    """Test POST /api/diagnosis endpoint."""
    res = client.post("/api/diagnosis", json={
        "symptom_text": "GSM module not responding to AT commands",
        "component_name": "SIM800L GSM Module",
        "observed_symptoms": ["Serial Communication Error"]
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["priority"] in ["High", "Medium", "Low", "Critical"]

    # Check history endpoint
    hist_res = client.get("/api/diagnosis/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.get_json()
    assert hist_data["status"] == "success"
    assert len(hist_data["history"]) > 0

def test_local_rag_service(client):
    """Test TF-IDF Cosine Similarity Local RAG zero-crash answer generation."""
    with client.application.app_context():
        res = LocalRAGService.answer_question("What voltage does Arduino Uno need?", user_id=1)
        assert res is not None
        assert "query" in res
        assert "answer" in res
        assert "sources" in res
        assert res["llm_used"] is False
        assert "Local RAG Engine" in res["engine"]

def test_chatbot_api_endpoint(client):
    """Test POST /api/chat and GET /api/chat/history."""
    res = client.post("/api/chat", json={
        "message": "How do I wire an LDR sensor?"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "data" in data
    assert "answer" in data["data"]

    hist_res = client.get("/api/chat/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.get_json()
    assert hist_data["status"] == "success"
    assert len(hist_data["history"]) >= 2  # user message + assistant answer

def test_memory_service(client):
    """Test user memory profile telemetry aggregation."""
    with client.application.app_context():
        profile = MemoryService.get_user_memory_profile(user_id=1)
        assert profile is not None
        assert profile["user_id"] == 1
        assert "owned_components_count" in profile
        assert "recommendation_insight" in profile

def test_view_routes_phase4(client):
    """Test HTML rendering of Phase 4 views."""
    assert client.get("/diagnosis").status_code == 200
    assert client.get("/assistant").status_code == 200
    assert client.get("/profile").status_code == 200
    assert client.get("/my-projects").status_code == 200
