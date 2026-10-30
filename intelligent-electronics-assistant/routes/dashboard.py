from flask import Blueprint, render_template, session, redirect, url_for, request
from services.component_service import ComponentService
from services.project_service import ProjectService
from services.recommendation_service import RecommendationService
from services.safety_service import SafetyService
from services.cost_service import CostService
from services.dependency_service import DependencyService
from services.build_service import BuildService
from services.memory_service import MemoryService
from database.models import db, ProjectHistory, Project, UserPreference, BuildSession

dashboard_views = Blueprint("dashboard_views", __name__)

@dashboard_views.app_context_processor
def inject_system_status():
    """Inject dynamic system status based on actual app & model state."""
    from ml.predict_component import ComponentScannerPredictor
    from config import Config
    
    scanner_ready = ComponentScannerPredictor.is_model_available()
    
    return {
        "system_status": {
            "database": "Connected",
            "ml_model": "Ready",
            "rag": "Ready",
            "scanner": "Ready" if scanner_ready else "Not Trained",
            "scanner_ready": scanner_ready
        }
    }

def get_current_user_id():
    user_id = session.get("user_id")
    if not user_id:
        session["user_id"] = 1
        session["username"] = "demo"
        user_id = 1
    return user_id

@dashboard_views.route("/")
@dashboard_views.route("/dashboard")
def dashboard():
    user_id = get_current_user_id()
    components = ComponentService.get_components(user_id=user_id)
    
    # User preferences mode
    pref = UserPreference.query.filter_by(user_id=user_id).first()
    mode = pref.mode if pref else "prototype"

    # Dynamic recommendations
    recs = RecommendationService.get_recommendations(user_id=user_id, mode=mode)
    
    # Calculate real-time stats
    total_components = sum(c.quantity for c in components)
    high_feasible_recs = [r for r in recs if r["feasibility_score"] >= 50]
    saved_count = ProjectHistory.query.filter_by(user_id=user_id, action="saved").count()
    completed_count = ProjectHistory.query.filter_by(user_id=user_id, action="completed").count()

    # Dynamic calculation of potential cost saved through owned inventory parts
    total_inventory_savings = sum((c.cost or 30.0) * min(c.quantity, 2) for c in components)

    # Real-time safety hazard evaluation across recommended projects
    safety_issues_count = sum(1 for r in recs[:5] if r.get("highest_safety_severity") in ["High", "Critical"])

    # Real recent activity from database
    history = ProjectHistory.query.filter_by(user_id=user_id).order_by(ProjectHistory.timestamp.desc()).limit(6).all()
    history_items = []
    for h in history:
        proj = Project.query.filter_by(id=h.project_id).first()
        history_items.append({
            "action": h.action,
            "project_name": proj.name if proj else h.project_id,
            "timestamp": h.timestamp.strftime("%b %d, %H:%M") if h.timestamp else "Recently",
            "notes": h.notes
        })

    stats = {
        "components_available": total_components,
        "recommended_projects": len(high_feasible_recs),
        "saved_projects": saved_count,
        "projects_completed": completed_count,
        "potential_cost_saved": f"₹ {int(total_inventory_savings):,}",
        "safety_issues_detected": safety_issues_count
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        components=components[:6],
        recommended_projects=recs[:4],
        recent_activity=history_items,
        active_page="dashboard"
    )

@dashboard_views.route("/components")
def components_page():
    return render_template("components.html", active_page="components")

@dashboard_views.route("/recommendations")
@dashboard_views.route("/projects")
def projects_page():
    return render_template("projects.html", active_page="projects")

@dashboard_views.route("/projects/<project_id>")
def project_detail_page(project_id):
    """Detailed single project page with dependencies, safety, cost, and build entrance."""
    user_id = get_current_user_id()
    project = ProjectService.get_by_id(project_id)
    if not project:
        return render_template("base.html", error_title="Project Not Found", error_msg=f"No project found with ID {project_id}"), 404

    pref = UserPreference.query.filter_by(user_id=user_id).first()
    mode = pref.mode if pref else "prototype"

    deps = DependencyService.analyze_project_dependencies(project_id, user_id=user_id, mode=mode)
    safety = SafetyService.evaluate_project_safety(project.to_dict())
    cost = CostService.calculate_project_cost(project_id, user_id=user_id, mode=mode)
    build_session = BuildService.get_or_create_session(user_id=user_id, project_id=project_id)
    
    is_saved = ProjectHistory.query.filter_by(user_id=user_id, project_id=project_id, action="saved").first() is not None

    return render_template(
        "project_detail.html",
        project=project,
        deps=deps,
        safety=safety,
        cost=cost,
        build_session=build_session,
        is_saved=is_saved,
        mode=mode,
        active_page="projects"
    )

@dashboard_views.route("/build/<project_id>")
def project_build_page(project_id):
    """Step-by-step interactive build guide."""
    user_id = get_current_user_id()
    project = ProjectService.get_by_id(project_id)
    if not project:
        return render_template("base.html", error_title="Project Not Found", error_msg="Project not found"), 404

    build_data = BuildService.get_or_create_session(user_id=user_id, project_id=project_id)

    return render_template(
        "build_guide.html",
        project=project,
        build_data=build_data,
        active_page="projects"
    )

@dashboard_views.route("/scanner")
def scanner_page():
    return render_template("scanner.html", active_page="scanner")

@dashboard_views.route("/wiring")
@dashboard_views.route("/wiring/<project_id>")
def wiring_page(project_id=None):
    return render_template("wiring.html", project_id=project_id, active_page="wiring")

@dashboard_views.route("/diagnosis")
def diagnosis_page():
    user_id = get_current_user_id()
    projects = ProjectService.get_all()
    components = ComponentService.get_components(user_id=user_id)
    return render_template("diagnosis.html", projects=projects, components=components, active_page="diagnosis")

@dashboard_views.route("/my-projects")
def my_projects_page():
    user_id = get_current_user_id()
    history = ProjectHistory.query.filter_by(user_id=user_id).order_by(ProjectHistory.timestamp.desc()).all()
    
    saved_projects = []
    attempted_projects = []
    completed_projects = []

    for h in history:
        p = Project.query.filter_by(id=h.project_id).first()
        if p:
            item = {"project": p, "history": h}
            if h.action == "saved" and p.id not in [x["project"].id for x in saved_projects]:
                saved_projects.append(item)
            elif h.action == "attempted" and p.id not in [x["project"].id for x in attempted_projects]:
                session = BuildSession.query.filter_by(user_id=user_id, project_id=p.id).order_by(BuildSession.started_at.desc()).first()
                item["progress"] = session.progress_percent if session else 0
                attempted_projects.append(item)
            elif h.action == "completed" and p.id not in [x["project"].id for x in completed_projects]:
                completed_projects.append(item)

    return render_template(
        "my_projects.html",
        saved_projects=saved_projects,
        attempted_projects=attempted_projects,
        completed_projects=completed_projects,
        active_page="my_projects"
    )

@dashboard_views.route("/assistant")
def assistant_page():
    return render_template("chatbot.html", active_page="assistant")

@dashboard_views.route("/profile")
def profile_page():
    user_id = get_current_user_id()
    pref = UserPreference.query.filter_by(user_id=user_id).first()
    profile_data = MemoryService.get_user_memory_profile(user_id=user_id)
    return render_template("profile.html", pref=pref, profile_data=profile_data, active_page="profile")

@dashboard_views.route("/api/user-preference/mode", methods=["POST"])
def toggle_mode():
    user_id = get_current_user_id()
    data = request.get_json() or {}
    new_mode = data.get("mode", "prototype")
    pref = UserPreference.query.filter_by(user_id=user_id).first()
    if pref:
        pref.mode = new_mode
        db.session.commit()
    return {"status": "success", "mode": new_mode}
