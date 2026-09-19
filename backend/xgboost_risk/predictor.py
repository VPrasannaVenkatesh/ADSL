"""
Continuous XGBoost Transaction Risk Predictor (Module 4).
Thread-safe singleton model loader and real-time inference engine.
Computes fine-grained continuous risk score (0.0 to 100.0), assigns 3-tier risk level:
  - LOW (0 - 30.0)
  - MEDIUM (30.1 - 60.0)
  - HIGH (60.1 - 100.0)
and derives explainable contributing risk factors.
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
    RISK_LEVELS,
    score_to_risk_level,
    score_to_decision,
)
from .feature_extractor import features_to_vector


class XGBoostTransactionPredictor:
    """
    Singleton inference engine for continuous transaction risk prediction.
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
        self.model: Optional[xgb.XGBRegressor] = None
        self.metadata: Dict[str, Any] = {}
        self.load_model()
        self._initialized = True

    def load_model(self) -> bool:
        """Loads or hot-reloads the trained XGBoost model and metadata from disk."""
        with self._lock:
            if os.path.exists(MODEL_PATH):
                try:
                    loaded_model = xgb.XGBRegressor()
                    loaded_model.load_model(MODEL_PATH)
                    self.model = loaded_model
                    print(f"[XGBoostPredictor] Loaded continuous model from {MODEL_PATH}")

                    if os.path.exists(METADATA_PATH):
                        with open(METADATA_PATH, "r", encoding="utf-8") as f:
                            self.metadata = json.load(f)
                    return True
                except Exception as e:
                    print(f"[XGBoostPredictor] Error loading model: {e}")
                    # Attempt fallback loading as Booster
                    try:
                        booster = xgb.Booster()
                        booster.load_model(MODEL_PATH)
                        self.model = booster
                        print(f"[XGBoostPredictor] Loaded booster fallback from {MODEL_PATH}")
                        return True
                    except Exception as e2:
                        print(f"[XGBoostPredictor] Booster fallback failed: {e2}")
                        self.model = None
                        return False
            else:
                print(f"[XGBoostPredictor] No model found at {MODEL_PATH}. Training required.")
                self.model = None
                return False

    def is_ready(self) -> bool:
        return self.model is not None

    def predict_transaction_risk(self, features_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Executes real-time continuous transaction risk scoring.
        Returns:
            - xgboost_risk_score: float (0.0 to 100.0, rounded to 1 decimal place)
            - risk_level: str ('LOW', 'MEDIUM', 'HIGH')
            - decision_action: str ('ALLOW', 'MONITOR', 'HONEYPOT')
            - predicted_class: str ('NORMAL', 'SUSPICIOUS', 'MULE_FLOW')
            - top_risk_factors: list of explainable factor strings
            - model_version: str
            - prediction_timestamp: str
        """
        now_ts = datetime.now().isoformat()

        # Fallback heuristic if model not trained yet
        if not self.is_ready():
            return {
                "xgboost_risk_score": 15.0,
                "risk_level": "LOW",
                "decision_action": "ALLOW",
                "predicted_class": "NORMAL",
                "prediction_probability": 0.85,
                "top_risk_factors": ["Heuristic baseline applied (ML model uninitialized)"],
                "model_version": "v0.0.0-fallback",
                "prediction_timestamp": now_ts,
            }

        vector = features_to_vector(features_dict)
        X_input = np.array([vector], dtype=float)

        try:
            if isinstance(self.model, xgb.Booster):
                dmat = xgb.DMatrix(X_input, feature_names=FEATURE_NAMES)
                raw_pred = float(self.model.predict(dmat)[0])
            else:
                raw_pred = float(self.model.predict(X_input)[0])

            # Ensure prediction is clipped cleanly to [0.0, 100.0] and rounded to 1 decimal place
            risk_score = round(float(np.clip(raw_pred, 0.0, 100.0)), 1)
            risk_level = score_to_risk_level(risk_score)
            decision_action = score_to_decision(risk_score)

            # Map to descriptive class label
            if risk_level == "HIGH":
                predicted_class = "MULE_FLOW"
            elif risk_level == "MEDIUM":
                predicted_class = "SUSPICIOUS"
            else:
                predicted_class = "NORMAL"

            # Derive explainable risk factors
            top_factors = self._extract_top_contributing_factors(features_dict, risk_score)

            # Confidence / proxy probability based on score extremity
            if risk_score <= 30.0:
                prob = round(1.0 - (risk_score / 60.0), 3)
            elif risk_score >= 60.0:
                prob = round(0.50 + ((risk_score - 60.0) / 80.0), 3)
            else:
                prob = round(0.50 + abs(risk_score - 45.0) / 60.0, 3)
            prob = max(0.50, min(0.99, prob))

            return {
                "xgboost_risk_score": risk_score,
                "risk_level": risk_level,
                "decision_action": decision_action,
                "predicted_class": predicted_class,
                "prediction_probability": prob,
                "top_risk_factors": top_factors,
                "model_version": self.metadata.get("model_version", MODEL_VERSION),
                "prediction_timestamp": now_ts,
            }

        except Exception as e:
            print(f"[XGBoostPredictor] Inference error: {e}")
            return {
                "xgboost_risk_score": 20.0,
                "risk_level": "LOW",
                "decision_action": "ALLOW",
                "predicted_class": "NORMAL",
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
        Extracts explainable factors based on feature signals and contextual profile baselines.
        """
        factors: List[str] = []
        is_biz = features_dict.get("is_business", 0.0) == 1.0
        turnover_ratio = features_dict.get("amount_vs_turnover_ratio", 0.0)
        amt = features_dict.get("amount", 0.0)

        # Business Context
        if is_biz:
            if turnover_ratio <= 0.35 and risk_score <= 40.0:
                factors.append(f"Legitimate business payment within expected turnover ({turnover_ratio*100:.1f}% of baseline)")
            elif turnover_ratio > 0.75:
                factors.append(f"Business payment represents {turnover_ratio*100:.0f}% of expected monthly turnover")
        else:
            # Personal Amount Ratio
            amt_vs_avg = features_dict.get("sender_amount_vs_avg_ratio", 1.0)
            if amt_vs_avg >= 3.0:
                factors.append(f"Amount is {amt_vs_avg:.1f}× higher than sender historical average")
            elif amt_vs_avg >= 2.0 and risk_score > 30.0:
                factors.append(f"Amount is {amt_vs_avg:.1f}× higher than typical personal transfers")

        # Balance drain
        balance_pct = features_dict.get("transfer_percentage_of_balance", 0.0)
        if balance_pct >= 0.70:
            factors.append(f"Transfer drains {balance_pct*100:.0f}% of account balance")

        # Beneficiary Analysis
        is_new_bene = features_dict.get("recipient_is_new", 0.0) == 1.0
        bene_freq = features_dict.get("beneficiary_usage_frequency", 1.0)
        if is_new_bene:
            factors.append("First-time beneficiary transfer")
        elif bene_freq == 1.0 and risk_score > 35.0:
            factors.append("Rarely used beneficiary counterparty")

        # Timing / Hour Analysis
        if features_dict.get("is_unusual_hour", 0.0) == 1.0 and amt >= 20000:
            factors.append("Transaction initiated outside regular account operating hours")
        elif features_dict.get("is_night", 0.0) == 1.0 and amt >= 25000:
            factors.append("Transfer occurred during anomalous night hours (23:00–05:00)")

        # Velocity & Burst Analysis
        tx_1h = features_dict.get("sender_tx_1h", 0.0)
        burst_ratio = features_dict.get("sender_burst_ratio", 1.0)
        min_int = features_dict.get("sender_min_interval_sec", 3600.0)
        if tx_1h >= 5 or (min_int <= 45.0 and tx_1h >= 3):
            factors.append(f"Transaction burst: {int(tx_1h)} transactions in last 1 hour (interval: {int(min_int)}s)")
        elif tx_1h >= 3 or burst_ratio >= 2.5:
            factors.append(f"Velocity surge: {int(tx_1h)} transactions recently ({burst_ratio:.1f}× baseline)")

        # Device & Location Analysis
        if features_dict.get("device_location_anomaly", 0.0) == 1.0:
            factors.append("Combined anomaly: Unrecognized device used from a new geographical location")
        else:
            if features_dict.get("is_new_device", 0.0) == 1.0 or features_dict.get("sender_device_changes", 0.0) >= 2:
                factors.append("Unusual or newly recognized device fingerprint")
            if features_dict.get("is_location_deviation", 0.0) == 1.0:
                factors.append("Geographical location deviation from account baseline")

        # Mule & Network Flow Signals
        if features_dict.get("network_rapid_forwarding", 0.0) == 1.0:
            factors.append("Structured rapid fund forwarding pattern detected")
        if features_dict.get("network_short_dwell_flag", 0.0) == 1.0:
            factors.append("Short dwell-time: Incoming funds dispatched within minutes")
        if features_dict.get("network_amount_splitting", 0.0) == 1.0 or features_dict.get("sender_amount_split_count", 0.0) >= 2:
            factors.append("Structured amount splitting / smurfing pattern detected")
        if features_dict.get("receiver_fan_in", 0.0) >= 3 or features_dict.get("sender_fan_in", 0.0) >= 3:
            factors.append(f"Fan-in collection pattern ({int(features_dict.get('receiver_fan_in', 0))} convergent inflows)")
        if features_dict.get("sender_fan_out", 0.0) >= 3:
            factors.append(f"High fan-out dispersal ({int(features_dict.get('sender_fan_out', 0))} concurrent beneficiaries)")
        if features_dict.get("network_cycle_detected", 0.0) == 1.0:
            factors.append("Circular flow / multi-hop transaction cycle detected")

        # Sender Behavioral Risk
        if features_dict.get("sender_behavioural_risk_score", 0.0) >= 60.0:
            factors.append(f"Elevated sender behavioural risk ({features_dict.get('sender_behavioural_risk_score', 0):.1f}/100)")

        # Fallback for clean low-risk profile
        if not factors and risk_score <= 30.0:
            factors.append("Standard expected transaction profile")

        return factors[:5]


# Singleton Predictor
GLOBAL_PREDICTOR = XGBoostTransactionPredictor()
