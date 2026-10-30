import os
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "ml" / "model"
MODEL_PATH = MODEL_DIR / "recommendation_model.pkl"

def train_model():
    """
    Train a Logistic Regression recommendation model based on:
    - component_utilisation (0.0 to 1.0)
    - required_avail_ratio (0.0 to 1.0)
    - missing_cost_normalized (0.0 to 1.0)
    - difficulty_level (1: Beginner, 2: Intermediate, 3: Advanced)
    - user_skill_match (0.0 to 1.0)
    - safety_risk_level (1: Low, 2: Medium, 3: High, 4: Critical)
    - previous_completion_affinity (0.0 to 1.0)
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Synthetic training distribution reflecting maker project feasibility decisions
    np.random.seed(42)
    n_samples = 400

    comp_util = np.random.uniform(0.1, 1.0, n_samples)
    req_avail = np.random.uniform(0.0, 1.0, n_samples)
    missing_cost = np.random.uniform(0.0, 1.0, n_samples)
    difficulty = np.random.choice([1, 2, 3], size=n_samples, p=[0.4, 0.4, 0.2])
    skill_match = np.random.uniform(0.2, 1.0, n_samples)
    safety_risk = np.random.choice([1, 2, 3, 4], size=n_samples, p=[0.5, 0.3, 0.15, 0.05])
    affinity = np.random.uniform(0.0, 1.0, n_samples)

    # Calculate probability score reflecting real engineering feasibility
    score_metric = (
        0.35 * req_avail +
        0.20 * comp_util +
        0.15 * (1.0 - missing_cost) +
        0.15 * skill_match +
        0.10 * affinity -
        0.15 * (safety_risk / 4.0)
    )
    # Binary classification label: 1 if recommended, 0 otherwise
    labels = (score_metric >= 0.48).astype(int)

    X = np.column_stack([
        comp_util,
        req_avail,
        missing_cost,
        difficulty,
        skill_match,
        safety_risk,
        affinity
    ])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf = LogisticRegression(C=1.0, max_iter=200, random_state=42)
    clf.fit(X_scaled, labels)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": clf, "scaler": scaler}, f)

    print(f"[SUCCESS] Recommendation Logistic Regression model trained and saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
