import pytest
from app import create_app
from config import TestingConfig
from database.models import db, User, Component, Project, ProjectHistory, BuildSession, BuildStep
from services.recommendation_service import RecommendationService
from services.dependency_service import DependencyService
from services.safety_service import SafetyService
from services.cost_service import CostService
from services.build_service import BuildService

@pytest.fixture
def app_and_client():
    app = create_app(TestingConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Seed test user
            user = User(username="maker1", email="maker1@test.io", skill_level="Beginner")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            # Seed sample project with steps and safety rules
            proj = Project(
                id="proj-auto-light",
                name="Automatic Street Light",
                description="LDR based night lighting",
                category="Home Automation",
                difficulty="Beginner",
                estimated_cost=550.0,
                required_components=["Arduino Uno", "LDR", "LED", "Resistor"],
                optional_components=["Relay"],
                dependencies={"resistor_for_led": "220 ohm series"},
                wiring_rules=["LED Anode to Pin 13"],
                safety_rules=["Do not short 5V to GND"],
                steps=[
                    {
                        "step_number": 1,
                        "title": "Power Rails",
                        "description": "Connect 5V and GND",
                        "components_involved": ["Arduino Uno"],
                        "expected_result": "5V available"
                    },
                    {
                        "step_number": 2,
                        "title": "Wire LDR",
                        "description": "Wire LDR voltage divider",
                        "components_involved": ["LDR", "Resistor"],
                        "expected_result": "A0 reads voltage"
                    }
                ]
            )
            db.session.add(proj)

            # Seed user components: has Arduino and LDR, lacks LED and Resistor
            c1 = Component(id="c-uno", user_id=user.id, name="Arduino Uno", category="Controllers", quantity=1, cost=450.0)
            c2 = Component(id="c-ldr", user_id=user.id, name="LDR", category="Sensors", quantity=3, cost=15.0)
            db.session.add_all([c1, c2])
            db.session.commit()

            yield app, client, user, proj
            db.drop_all()

def test_dependency_analysis(app_and_client):
    """Test detection of available, missing, and alternative components."""
    app, client, user, proj = app_and_client
    with app.app_context():
        res = DependencyService.analyze_project_dependencies(proj.id, user_id=user.id, mode="prototype")
        assert res["feasibility_percent"] == 50.0  # 2 of 4 components available
        
        avail_names = [c["name"] for c in res["available_components"]]
        assert "Arduino Uno" in avail_names
        assert "LDR" in avail_names

        missing_names = [m["name"] for m in res["missing_components"]]
        assert "LED" in missing_names
        assert "Resistor" in missing_names

def test_safety_engine_evaluation(app_and_client):
    """Test safety rule engine detects hazards and missing series resistors."""
    app, client, user, proj = app_and_client
    with app.app_context():
        safety = SafetyService.evaluate_project_safety(proj.to_dict())
        assert "status" in safety
        assert safety["warning_count"] > 0
        # Warnings should include LED resistor guideline and custom project safety rule
        titles = [w["title"] for w in safety["warnings"]]
        assert any("Resistor" in t or "Safety" in t or "Circuit" in t for t in titles)

def test_cost_calculation_prototype_vs_production(app_and_client):
    """Test cost service for prototype and production modes."""
    app, client, user, proj = app_and_client
    with app.app_context():
        cost_proto = CostService.calculate_project_cost(proj.id, user_id=user.id, mode="prototype")
        assert cost_proto["current_component_cost"] > 0
        assert cost_proto["additional_required_cost"] > 0
        assert cost_proto["total_project_cost"] == cost_proto["current_component_cost"] + cost_proto["additional_required_cost"]

def test_recommendation_scoring_and_explanation(app_and_client):
    """Test multi-factor recommendation engine and WHY explanation."""
    app, client, user, proj = app_and_client
    with app.app_context():
        recs = RecommendationService.get_recommendations(user_id=user.id, mode="prototype")
        assert len(recs) >= 1
        rec = recs[0]
        assert "recommendation_score" in rec
        assert "feasibility_score" in rec
        assert 0 <= rec["feasibility_score"] <= 100
        assert len(rec["explanation"]) > 5
        assert "Prototype model" in rec["model_disclaimer"]

def test_interactive_build_progress(app_and_client):
    """Test start build session, step verification, and completion recording."""
    app, client, user, proj = app_and_client
    with app.app_context():
        # 1. Create/get session
        session_data = BuildService.get_or_create_session(user.id, proj.id)
        session_id = session_data["session_id"]
        assert session_data["progress_percent"] == 0
        assert len(session_data["steps"]) == 2

        # 2. Complete Step 1
        update_1 = BuildService.update_step_progress(session_id, step_number=1, completed=True, user_id=user.id)
        assert update_1["progress_percent"] == 50
        assert update_1["status"] == "in_progress"

        # 3. Complete Step 2 -> 100% completion
        update_2 = BuildService.update_step_progress(session_id, step_number=2, completed=True, user_id=user.id)
        assert update_2["progress_percent"] == 100
        assert update_2["status"] == "completed"

        # Verify completed milestone logged in ProjectHistory
        completed_hist = ProjectHistory.query.filter_by(user_id=user.id, project_id=proj.id, action="completed").first()
        assert completed_hist is not None

def test_api_endpoints_phase2(app_and_client):
    """Test all Phase 2 REST API endpoints."""
    app, client, user, proj = app_and_client
    
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["username"] = user.username

    # 1. POST /api/recommendations
    res_rec = client.post("/api/recommendations", json={"mode": "prototype"})
    assert res_rec.status_code == 200
    assert res_rec.get_json()["status"] == "success"

    # 2. GET /api/projects/<id>/dependencies
    res_dep = client.get(f"/api/projects/{proj.id}/dependencies")
    assert res_dep.status_code == 200
    assert res_dep.get_json()["data"]["feasibility_percent"] == 50.0

    # 3. GET /api/projects/<id>/safety
    res_saf = client.get(f"/api/projects/{proj.id}/safety")
    assert res_saf.status_code == 200
    assert "warnings" in res_saf.get_json()["data"]

    # 4. GET /api/projects/<id>/cost
    res_cost = client.get(f"/api/projects/{proj.id}/cost?mode=prototype")
    assert res_cost.status_code == 200
    assert "total_project_cost" in res_cost.get_json()["data"]

    # 5. POST /api/build-progress
    # First get session
    res_get_sess = client.get(f"/api/build-progress/{proj.id}")
    sess_id = res_get_sess.get_json()["data"]["session_id"]

    res_step = client.post("/api/build-progress", json={
        "session_id": sess_id,
        "step_number": 1,
        "completed": True
    })
    assert res_step.status_code == 200
    assert res_step.get_json()["data"]["progress_percent"] == 50

    # 6. POST & GET /api/history
    res_save = client.post("/api/history", json={
        "project_id": proj.id,
        "action": "saved",
        "notes": "Testing save action"
    })
    assert res_save.status_code == 201

    res_hist = client.get("/api/history")
    assert res_hist.status_code == 200
    hist_items = res_hist.get_json()["data"]
    assert any(h["project_id"] == proj.id for h in hist_items)
