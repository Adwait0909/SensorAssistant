import os
import math
import pickle
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml" / "model" / "recommendation_model.pkl"

class MLRecommendationScorer:
    _cached_bundle = None

    @classmethod
    def _load_model(cls):
        if cls._cached_bundle is None and MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    cls._cached_bundle = pickle.load(f)
            except Exception:
                cls._cached_bundle = None
        return cls._cached_bundle

    @classmethod
    def predict_score(cls, features: List[float]) -> float:
        """
        Predict probability score using trained Logistic Regression model.
        Features:
        [comp_util, req_avail, missing_cost_norm, difficulty, skill_match, safety_risk, affinity]
        """
        bundle = cls._load_model()
        if bundle:
            try:
                clf = bundle["model"]
                scaler = bundle["scaler"]
                scaled = scaler.transform([features])
                prob = clf.predict_proba(scaled)[0][1]
                return float(prob * 100.0)
            except Exception:
                pass

        # Robust heuristic fallback matching the ML weights
        comp_util, req_avail, missing_cost_norm, difficulty, skill_match, safety_risk, affinity = features
        raw = (
            0.40 * req_avail +
            0.20 * comp_util +
            0.15 * max(0.0, 1.0 - missing_cost_norm) +
            0.15 * skill_match +
            0.10 * affinity -
            0.15 * (safety_risk / 4.0)
        )
        # Sigmoid scaling
        score = 1.0 / (1.0 + math.exp(-6.0 * (raw - 0.45)))
        return round(score * 100.0, 1)
