import pytest
from app import create_app
from config import TestingConfig
from database.models import db, User, Component, Project

@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Seed minimal test user
            user = User(username="testmaker", email="test@local.io")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()
            yield client
            db.drop_all()

def test_database_initialization(client):
    """Test that users and tables initialize properly."""
    user = User.query.filter_by(username="testmaker").first()
    assert user is not None
    assert user.check_password("pass123") is True

def test_components_api(client):
    """Test full CRUD cycle of component API."""
    # 1. Create component
    res = client.post("/api/components", json={
        "name": "Arduino Uno",
        "category": "Controllers",
        "quantity": 3,
        "voltage": "5V",
        "cost": 450.0
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    comp_id = data["data"]["id"]

    # 2. List components
    res_list = client.get("/api/components")
    assert res_list.status_code == 200
    list_data = res_list.get_json()
    assert any(c["id"] == comp_id for c in list_data["data"])

    # 3. Update component quantity
    res_update = client.put(f"/api/components/{comp_id}", json={
        "quantity": 10
    })
    assert res_update.status_code == 200
    assert res_update.get_json()["data"]["quantity"] == 10

    # 4. Delete component
    res_del = client.delete(f"/api/components/{comp_id}")
    assert res_del.status_code == 200

def test_projects_api_and_feasibility(client):
    """Test project retrieval and dynamic feasibility evaluation."""
    # Add project
    proj = Project(
        id="test-light",
        name="Test Street Light",
        description="A light test project",
        category="Automation",
        difficulty="Beginner",
        required_components=["LDR", "LED"]
    )
    db.session.add(proj)
    db.session.commit()

    # Get project list
    res = client.get("/api/projects")
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1

    # Check feasibility
    res_feas = client.get(f"/api/projects/{proj.id}/feasibility")
    assert res_feas.status_code == 200
    f_data = res_feas.get_json()["data"]
    assert "feasibility_score" in f_data
