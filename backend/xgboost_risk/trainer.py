"""
Continuous XGBoost Model Trainer and Evaluator.
Trains an XGBRegressor on continuous risk targets (0.0 to 100.0) with RMSE optimization:
- Computes regression metrics (RMSE, MAE, R2)
- Evaluates 3-tier risk classification accuracy (LOW <= 30, MEDIUM 31-60, HIGH > 60)
- Ranks feature importances across all 68 canonical features
- Persists model artifact and metadata
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, classification_report
import xgboost as xgb

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .config import (
    MODEL_PATH,
    METADATA_PATH,
    MODEL_VERSION,
    FEATURE_NAMES,
    RISK_LEVELS,
    XGBOOST_HYPERPARAMS,
    score_to_risk_level,
)
from .dataset_generator import generate_training_dataset


def train_xgboost_model(sample_limit: int = 24000) -> Dict[str, Any]:
    """
    Orchestrates continuous dataset generation, XGBRegressor training,
    multi-metric evaluation, and model artifact persistence.
    """
    print("=" * 72)
    print(f"  Training Continuous XGBoost Risk Regressor [{MODEL_VERSION}]")
    print(f"  Target: Continuous Risk Score [0.0 - 100.0] | 3 Tiers: LOW, MEDIUM, HIGH")
    print("=" * 72)

    # 1. Generate Continuous Dataset
    X_df, y_arr = generate_training_dataset(sample_limit=sample_limit)

    # 2. Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y_arr, test_size=0.20, random_state=42
    )

    hyperparams = dict(XGBOOST_HYPERPARAMS)

    print(f"[Trainer] Fitting XGBRegressor on {len(X_train)} samples across {len(FEATURE_NAMES)} features...")
    model = xgb.XGBRegressor(**hyperparams)
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # 3. Evaluate Regression Performance
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0.0, 100.0)

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    # 4. Evaluate 3-Tier Classification Accuracy
    true_tiers = [score_to_risk_level(s) for s in y_test]
    pred_tiers = [score_to_risk_level(s) for s in y_pred]
    
    tier_accuracy = float(np.mean([t == p for t, p in zip(true_tiers, pred_tiers)]))

    print("\n[Trainer] Continuous Regression Results:")
    print(f"  Root Mean Squared Error (RMSE) : {rmse:.3f}")
    print(f"  Mean Absolute Error (MAE)     : {mae:.3f}")
    print(f"  R² Goodness of Fit            : {r2:.4f}")
    print(f"  3-Tier Risk Accuracy          : {tier_accuracy*100:.2f}%")

    # Sample predictions distribution check
    sample_preds = y_pred[:15].round(1).tolist()
    print(f"\n  Sample Continuous Predictions : {sample_preds}")

    # 5. Feature Importances
    importances = model.feature_importances_
    feat_importance_list = []
    for name, imp in zip(FEATURE_NAMES, importances):
        feat_importance_list.append({
            "feature": name,
            "importance": float(round(imp, 5))
        })
    feat_importance_list.sort(key=lambda x: x["importance"], reverse=True)

    print("\n[Trainer] Top 10 Contributing Features:")
    for item in feat_importance_list[:10]:
        print(f"  - {item['feature']:32}: {item['importance']:.4f}")

    # 6. Persist Model & Metadata
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save_model(MODEL_PATH)
    print(f"\n[Trainer] Continuous XGBoost Model saved successfully to {MODEL_PATH}")

    metadata = {
        "model_version": MODEL_VERSION,
        "model_type": "XGBRegressor",
        "trained_at": datetime.now().isoformat(),
        "total_dataset_size": len(X_df),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "num_features": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "risk_levels": RISK_LEVELS,
        "metrics": {
            "rmse": round(rmse, 3),
            "mae": round(mae, 3),
            "r2_score": round(r2, 4),
            "tier_accuracy": round(tier_accuracy, 4),
        },
        "top_features": feat_importance_list[:15],
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[Trainer] Metadata saved to {METADATA_PATH}")

    return metadata


if __name__ == "__main__":
    train_xgboost_model()
