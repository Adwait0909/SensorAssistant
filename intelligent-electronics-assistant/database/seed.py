import json
from pathlib import Path
from database.models import (
    db, User, Component, ComponentAlias, Project, ProjectComponent,
    WiringRule, SafetyRule, DiagnosisRule, ProjectHistory, UserPreference
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def seed_database():
    """Seed initial data into database if empty."""
    print("[INFO] Checking and seeding database...")

    # 1. Seed Demo User
    demo_user = User.query.filter_by(username="demo").first()
    if not demo_user:
        print("  - Creating demo user 'demo'...")
        demo_user = User(
            username="demo",
            email="demo@electronics.local",
            role="maker",
            skill_level="Beginner"
        )
        demo_user.set_password("demo123")
        db.session.add(demo_user)
        db.session.commit()
        
        # User preferences
        pref = UserPreference(
            user_id=demo_user.id,
            mode="prototype",
            preferred_difficulty="Beginner",
            theme="dark"
        )
        db.session.add(pref)
        db.session.commit()

    # 2. Seed Aliases
    aliases_file = DATA_DIR / "aliases.json"
    if aliases_file.exists():
        with open(aliases_file, "r", encoding="utf-8") as f:
            aliases_data = json.load(f)
            for alias, standard_name in aliases_data.items():
                if not ComponentAlias.query.filter_by(alias=alias.lower()).first():
                    db.session.add(ComponentAlias(alias=alias.lower(), standard_name=standard_name))
        db.session.commit()

    # 3. Seed Components
    components_file = DATA_DIR / "components.json"
    if components_file.exists():
        with open(components_file, "r", encoding="utf-8") as f:
            comp_list = json.load(f)
            for c_data in comp_list:
                existing = Component.query.filter_by(id=c_data["id"]).first()
                if not existing:
                    comp = Component(
                        id=c_data["id"],
                        user_id=demo_user.id,
                        name=c_data["name"],
                        category=c_data["category"],
                        sub_category=c_data.get("sub_category"),
                        quantity=c_data.get("quantity", 1),
                        voltage=c_data.get("voltage", "5V"),
                        current_rating=c_data.get("current_rating"),
                        description=c_data.get("description"),
                        aliases=c_data.get("aliases", []),
                        datasheet_url=c_data.get("datasheet_url"),
                        cost=c_data.get("cost", 0.0),
                        availability=c_data.get("availability", "In Stock"),
                        safety_notes=c_data.get("safety_notes")
                    )
                    db.session.add(comp)
        db.session.commit()

    # 4. Seed Projects
    projects_file = DATA_DIR / "projects.json"
    if projects_file.exists():
        with open(projects_file, "r", encoding="utf-8") as f:
            proj_list = json.load(f)
            for p_data in proj_list:
                existing = Project.query.filter_by(id=p_data["id"]).first()
                if not existing:
                    proj = Project(
                        id=p_data["id"],
                        name=p_data["name"],
                        description=p_data["description"],
                        category=p_data["category"],
                        difficulty=p_data.get("difficulty", "Beginner"),
                        estimated_cost=p_data.get("estimated_cost", 0.0),
                        required_components=p_data.get("required_components", []),
                        optional_components=p_data.get("optional_components", []),
                        dependencies=p_data.get("dependencies", {}),
                        wiring_rules=p_data.get("wiring_rules", []),
                        safety_rules=p_data.get("safety_rules", []),
                        steps=p_data.get("steps", []),
                        testing_steps=p_data.get("testing_steps", []),
                        expected_output=p_data.get("expected_output"),
                        possible_failures=p_data.get("possible_failures", [])
                    )
                    db.session.add(proj)
                    
                    # Associate components
                    for req_comp in p_data.get("required_components", []):
                        db.session.add(ProjectComponent(
                            project_id=p_data["id"],
                            component_name=req_comp,
                            is_required=True,
                            quantity=1
                        ))
                    for opt_comp in p_data.get("optional_components", []):
                        db.session.add(ProjectComponent(
                            project_id=p_data["id"],
                            component_name=opt_comp,
                            is_required=False,
                            quantity=1
                        ))
        db.session.commit()

    # 5. Seed Wiring Rules
    wiring_file = DATA_DIR / "wiring_rules.json"
    if wiring_file.exists():
        with open(wiring_file, "r", encoding="utf-8") as f:
            w_rules = json.load(f)
            for wr in w_rules:
                rule_id = wr.get("id")
                comp_target = wr.get("component") or wr.get("project_id", "General")
                rule_text = wr.get("rule") or json.dumps(wr.get("connections", []))
                if rule_id and not WiringRule.query.filter_by(id=rule_id).first():
                    db.session.add(WiringRule(id=rule_id, component=comp_target, rule=rule_text))
        db.session.commit()

    # 6. Seed Safety Rules
    safety_file = DATA_DIR / "safety_rules.json"
    if safety_file.exists():
        with open(safety_file, "r", encoding="utf-8") as f:
            s_rules = json.load(f)
            for sr in s_rules:
                if not SafetyRule.query.filter_by(id=sr["id"]).first():
                    db.session.add(SafetyRule(id=sr["id"], target=sr["target"], risk_level=sr.get("risk_level", "Medium"), rule=sr["rule"]))
        db.session.commit()

    # 7. Seed Diagnosis Rules
    diag_file = DATA_DIR / "diagnosis_rules.json"
    if diag_file.exists():
        with open(diag_file, "r", encoding="utf-8") as f:
            d_rules = json.load(f)
            for dr in d_rules:
                if not DiagnosisRule.query.filter_by(id=dr["id"]).first():
                    db.session.add(DiagnosisRule(id=dr["id"], symptom=dr["symptom"], causes=dr.get("causes", []), steps=dr.get("steps", [])))
        db.session.commit()

    # 8. Seed Sample Activity / History for Demo User
    if not ProjectHistory.query.filter_by(user_id=demo_user.id).first():
        db.session.add(ProjectHistory(
            user_id=demo_user.id,
            project_id="proj-automatic-street-light",
            action="completed",
            notes="Successfully tested with LDR and 220 ohm resistor."
        ))
        db.session.add(ProjectHistory(
            user_id=demo_user.id,
            project_id="proj-smart-dustbin",
            action="attempted",
            notes="Assembled servo and HC-SR04 sensor."
        ))
        db.session.commit()

    print("[SUCCESS] Database seeding completed.")
