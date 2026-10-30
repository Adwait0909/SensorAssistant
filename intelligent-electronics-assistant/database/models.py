from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), default="maker")
    skill_level = db.Column(db.String(30), default="Beginner")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    components = db.relationship("Component", backref="owner", lazy=True, cascade="all, delete-orphan")
    build_sessions = db.relationship("BuildSession", backref="user", lazy=True, cascade="all, delete-orphan")
    history = db.relationship("ProjectHistory", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "skill_level": self.skill_level,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Component(db.Model):
    __tablename__ = "components"

    id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    sub_category = db.Column(db.String(80), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    voltage = db.Column(db.String(50), default="5V")
    current_rating = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    aliases = db.Column(db.JSON, default=list)
    datasheet_url = db.Column(db.String(300), nullable=True)
    cost = db.Column(db.Float, default=0.0)
    availability = db.Column(db.String(50), default="In Stock")
    safety_notes = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "category": self.category,
            "sub_category": self.sub_category,
            "quantity": self.quantity,
            "voltage": self.voltage,
            "current_rating": self.current_rating,
            "description": self.description,
            "aliases": self.aliases or [],
            "datasheet_url": self.datasheet_url,
            "cost": self.cost,
            "availability": self.availability,
            "safety_notes": self.safety_notes
        }

class ComponentAlias(db.Model):
    __tablename__ = "component_aliases"

    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(100), unique=True, nullable=False, index=True)
    standard_name = db.Column(db.String(150), nullable=False)

class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    difficulty = db.Column(db.String(50), default="Beginner")
    estimated_cost = db.Column(db.Float, default=0.0)
    required_components = db.Column(db.JSON, default=list)
    optional_components = db.Column(db.JSON, default=list)
    dependencies = db.Column(db.JSON, default=dict)
    wiring_rules = db.Column(db.JSON, default=list)
    safety_rules = db.Column(db.JSON, default=list)
    steps = db.Column(db.JSON, default=list)
    testing_steps = db.Column(db.JSON, default=list)
    expected_output = db.Column(db.Text, nullable=True)
    possible_failures = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "difficulty": self.difficulty,
            "estimated_cost": self.estimated_cost,
            "required_components": self.required_components or [],
            "optional_components": self.optional_components or [],
            "dependencies": self.dependencies or {},
            "wiring_rules": self.wiring_rules or [],
            "safety_rules": self.safety_rules or [],
            "steps": self.steps or [],
            "testing_steps": self.testing_steps or [],
            "expected_output": self.expected_output,
            "possible_failures": self.possible_failures or []
        }

class ProjectComponent(db.Model):
    __tablename__ = "project_components"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(100), db.ForeignKey("projects.id"), nullable=False)
    component_name = db.Column(db.String(150), nullable=False)
    is_required = db.Column(db.Boolean, default=True)
    quantity = db.Column(db.Integer, default=1)

class WiringRule(db.Model):
    __tablename__ = "wiring_rules"

    id = db.Column(db.String(100), primary_key=True)
    component = db.Column(db.String(150), nullable=False)
    rule = db.Column(db.Text, nullable=False)

class SafetyRule(db.Model):
    __tablename__ = "safety_rules"

    id = db.Column(db.String(100), primary_key=True)
    target = db.Column(db.String(150), nullable=False)
    risk_level = db.Column(db.String(50), default="Medium")
    rule = db.Column(db.Text, nullable=False)

class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    project_id = db.Column(db.String(100), db.ForeignKey("projects.id"), nullable=False)
    feasibility_score = db.Column(db.Float, default=0.0)
    matching_components = db.Column(db.JSON, default=list)
    missing_components = db.Column(db.JSON, default=list)
    additional_cost = db.Column(db.Float, default=0.0)
    recommendation_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BuildSession(db.Model):
    __tablename__ = "build_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.String(100), db.ForeignKey("projects.id"), nullable=False)
    progress_percent = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="in_progress")
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

class BuildStep(db.Model):
    __tablename__ = "build_steps"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("build_sessions.id"), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)

class DiagnosisRule(db.Model):
    __tablename__ = "diagnosis_rules"

    id = db.Column(db.String(100), primary_key=True)
    symptom = db.Column(db.String(255), nullable=False)
    causes = db.Column(db.JSON, default=list)
    steps = db.Column(db.JSON, default=list)

class DiagnosisHistory(db.Model):
    __tablename__ = "diagnosis_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    symptom = db.Column(db.String(255), nullable=False)
    suggested_fix = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProjectHistory(db.Model):
    __tablename__ = "project_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.String(100), db.ForeignKey("projects.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'attempted', 'completed', 'failed', 'saved'
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "action": self.action,
            "notes": self.notes,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class UserPreference(db.Model):
    __tablename__ = "user_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mode = db.Column(db.String(30), default="prototype")  # prototype or production
    preferred_difficulty = db.Column(db.String(30), default="Beginner")
    theme = db.Column(db.String(30), default="dark")
