"""
Multi-Class XGBoost Transaction Risk Predictor (Module 4).
Thread-safe singleton model loader and real-time inference engine.
Performs 4-class prediction:
  - NORMAL
  - SUSPICIOUS
  - MULE_FLOW
  - CRITICAL_FRAUD
Computes fine-grained probability distribution, calibrated continuous risk score (0-100),
risk level, and human-readable contributing risk factors.
"""

import os
import json
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
import xgboost as xgb

from .config import (
    MODEL_PATH,
    METADATA_PATH,
    MODEL_VERSION,
    FEATURE_NAMES,
    RISK_CLASSES,
    NUM_CLASSES,
    score_to_risk_level,
)
from .feature_extractor import features_to_vector


class XGBoostTransactionPredictor:
    """
    Singleton inference engine for multi-class transaction risk prediction.
    """
    _instance: Optional["XGBoostTransactionPredictor"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(XGBoostTransactionPredictor, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.model: Optional[xgb.XGBClassifier] = None
        self.metadata: Dict[str, Any] = {}
        self.load_model()
        self._initialized = True

    def load_model(self) -> bool:
        """Loads or hot-reloads the trained XGBoost model and metadata from disk."""
        with self._lock:
            if os.path.exists(MODEL_PATH):
                try:
                    loaded_model = xgb.XGBClassifier()
                    loaded_model.load_model(MODEL_PATH)
                    self.model = loaded_model
                    print(f"[XGBoostPredictor] Loaded active model from {MODEL_PATH}")

                    if os.path.exists(METADATA_PATH):
                        with open(METADATA_PATH, "r", encoding="utf-8") as f:
                            self.metadata = json.load(f)
                    return True
                except Exception as e:
                    print(f"[XGBoostPredictor] Error loading model: {e}")
                    return False
            else:
                print(f"[XGBoostPredictor] No model found at {MODEL_PATH}. Training required.")
                self.model = None
                return False

    def is_ready(self) -> bool:
        return self.model is not None

    def predict_transaction_risk(self, features_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Executes real-time multi-class transaction risk scoring.
        Returns:
            - xgboost_risk_score (0.0 to 100.0)
            - risk_level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
            - predicted_class ('NORMAL', 'SUSPICIOUS', 'MULE_FLOW', 'CRITICAL_FRAUD')
            - class_probabilities (dict of 4 class probabilities)
            - prediction_probability (max probability)
            - top_risk_factors (list of explainable factor strings)
            - model_version (str)
            - prediction_timestamp (str)
        """
        now_ts = datetime.now().isoformat()

        # Fallback if model not trained yet
        if not self.is_ready():
            return {
                "xgboost_risk_score": 15.0,
                "risk_level": "LOW",
                "predicted_class": "NORMAL",
                "class_probabilities": {"NORMAL": 0.85, "SUSPICIOUS": 0.10, "MULE_FLOW": 0.04, "CRITICAL_FRAUD": 0.01},
                "prediction_probability": 0.85,
                "top_risk_factors": ["Heuristic baseline applied (ML model uninitialized)"],
                "model_version": "v0.0.0-fallback",
                "prediction_timestamp": now_ts,
            }

        vector = features_to_vector(features_dict)
        X_input = np.array([vector], dtype=float)

        try:
            proba_raw = self.model.predict_proba(X_input)[0]

            # Handle both multi-class and legacy binary checkpoints gracefully
            if len(proba_raw) >= 4:
                p_norm = float(proba_raw[0])
                p_susp = float(proba_raw[1])
                p_mule = float(proba_raw[2])
                p_crit = float(proba_raw[3])
                class_probs = {
                    "NORMAL": round(p_norm, 4),
                    "SUSPICIOUS": round(p_susp, 4),
                    "MULE_FLOW": round(p_mule, 4),
                    "CRITICAL_FRAUD": round(p_crit, 4),
                }
                pred_idx = int(np.argmax(proba_raw))
                predicted_class = RISK_CLASSES[pred_idx] if pred_idx < len(RISK_CLASSES) else "NORMAL"
                # Calibrated continuous 0-100 composite risk score matching Section 10 distribution:
                # Normal: 8-25, Slightly unusual: 30-45, Moderately suspicious: 46-60, High: 61-85, Fraud: 86-100
                base_risk = 8.0 + (1.0 - p_norm) * 14.0
                risk_score = round(float(base_risk + p_susp * 38.0 + p_mule * 68.0 + p_crit * 85.0), 2)
            else:
                p_pos = float(proba_raw[1])
                p_neg = float(proba_raw[0])
                class_probs = {
                    "NORMAL": round(p_neg, 4),
                    "SUSPICIOUS": round(p_pos * 0.5, 4),
                    "MULE_FLOW": round(p_pos * 0.5, 4),
                    "CRITICAL_FRAUD": 0.0,
                }
                predicted_class = "SUSPICIOUS" if p_pos >= 0.50 else "NORMAL"
                risk_score = round(10.0 + p_pos * 85.0, 2)

            risk_score = min(max(risk_score, 0.0), 100.0)
            risk_level = score_to_risk_level(risk_score)

            # Determine explainable risk factors
            top_factors = self._extract_top_contributing_factors(features_dict, risk_score)

            return {
                "xgboost_risk_score": risk_score,
                "risk_level": risk_level,
                "predicted_class": predicted_class,
                "class_probabilities": class_probs,
                "prediction_probability": round(float(np.max(proba_raw)), 4),
                "top_risk_factors": top_factors,
                "model_version": self.metadata.get("model_version", MODEL_VERSION),
                "prediction_timestamp": now_ts,
            }
        except Exception as e:
            print(f"[XGBoostPredictor] Inference error: {e}")
            return {
                "xgboost_risk_score": 20.0,
                "risk_level": "LOW",
                "predicted_class": "NORMAL",
                "class_probabilities": {"NORMAL": 0.80, "SUSPICIOUS": 0.15, "MULE_FLOW": 0.05, "CRITICAL_FRAUD": 0.0},
                "prediction_probability": 0.80,
                "top_risk_factors": [f"Inference error: {str(e)[:50]}"],
                "model_version": MODEL_VERSION,
                "prediction_timestamp": now_ts,
            }

    def _extract_top_contributing_factors(
        self,
        features_dict: Dict[str, float],
        risk_score: float,
    ) -> List[str]:
        """
        Extracts explainable factors based on high-impact anomaly features and contextual profile baselines.
        """
        factors: List[str] = []
        is_biz = features_dict.get("is_business", 0.0) == 1.0
        ratio = features_dict.get("amount_vs_turnover_ratio", 0.0)

        if is_biz and ratio <= 0.25 and risk_score < 40.0:
            factors.append(f"Genuine business payment within expected monthly turnover ({ratio*100:.1f}% of baseline)")

        if not is_biz and ratio >= 1.5:
            factors.append(f"Amount is {ratio:.1f}× higher than personal monthly expected baseline")

        if features_dict.get("is_within_operating_hours", 1.0) == 0.0 and features_dict.get("amount", 0) >= 20000:
            factors.append("Transaction initiated outside regular account operating hours")

        if features_dict.get("network_rapid_forwarding", 0) == 1.0:
            factors.append("Structured rapid fund forwarding pattern detected")

        if features_dict.get("sender_amount_vs_avg_ratio", 1.0) >= 3.0 and not is_biz:
            factors.append(f"Transaction amount is {features_dict.get('sender_amount_vs_avg_ratio', 1.0):.1f}× higher than sender historical average")

        if features_dict.get("sender_tx_1h", 0) >= 4 or features_dict.get("sender_velocity_ratio", 1.0) >= 3.0:
            factors.append("Abnormal transaction frequency / velocity surge")

        if features_dict.get("recipient_is_new", 0) == 1.0 and (risk_score >= 35.0 or not is_biz):
            factors.append("First-time recipient transfer")

        if features_dict.get("receiver_fan_in", 0) >= 3 or features_dict.get("sender_fan_in", 0) >= 3:
            factors.append("Account acting as high fan-in collection point")

        if features_dict.get("sender_fan_out", 0) >= 3:
            factors.append(f"High fan-out dispersal ({int(features_dict.get('sender_fan_out', 0))} concurrent beneficiaries)")

        if features_dict.get("sender_device_changes", 0) >= 2 or features_dict.get("device_is_other", 0) == 1.0:
            factors.append("Unusual device fingerprint switch")

        if features_dict.get("is_cross_bank", 0) == 1.0 and (risk_score >= 50.0 or features_dict.get("recipient_is_new", 0) == 1.0):
            factors.append("Cross-bank transmission path")

        if features_dict.get("network_short_dwell_flag", 0) == 1.0:
            factors.append("Abnormally short dwell time (< 60s between incoming and outgoing transfer)")

        if features_dict.get("network_amount_splitting", 0) == 1.0 or features_dict.get("sender_amount_split_count", 0) >= 2:
            factors.append("Structured smurfing / threshold evasion pattern detected")

        if features_dict.get("is_night", 0) == 1.0 and features_dict.get("amount", 0) >= 30000:
            factors.append("High-value transfer during anomalous night hours (23:00-05:00)")

        if features_dict.get("sender_behavioural_risk_score", 0) >= 60.0:
            factors.append(f"Elevated sender behavioural risk ({features_dict.get('sender_behavioural_risk_score', 0):.1f}/100)")

        if not factors and risk_score < 30.0:
            factors.append("Standard expected transaction profile")

        return factors


# Singleton Predictor
GLOBAL_PREDICTOR = XGBoostTransactionPredictor()
