"""
FastAPI Router for XGBoost Transaction Risk Prediction Module (Module 4).
Mounted at /api/xgboost
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, BackgroundTasks, HTTPException
from pydantic import BaseModel

from simulator.db_connection import get_all_bank_connections
from .trainer import train_xgboost_model
from .predictor import GLOBAL_PREDICTOR
from .storage import (
    get_recent_transaction_risk_assessments,
    get_xgboost_summary_stats,
)
from .config import MODEL_VERSION, COMBINATION_WEIGHTS, FLAG_THRESHOLDS

xgboost_router = APIRouter(prefix="/api/xgboost", tags=["XGBoost Transaction Risk"])


class TrainResponse(BaseModel):
    status: str
    message: str
    model_version: str
    metrics: Dict[str, Any]
    top_features: List[Dict[str, Any]]


@xgboost_router.post("/train", response_model=TrainResponse)
def trigger_train_model(sample_limit: int = Query(4000, ge=500, le=15000)):
    """
    Trains or retrains the XGBoost Transaction Risk model on local bank data,
    evaluates ROC-AUC and metrics, and reloads the inference engine.
    """
    try:
        metadata = train_xgboost_model(sample_limit=sample_limit)
        # Reload live model in predictor singleton
        GLOBAL_PREDICTOR.load_model()

        return TrainResponse(
            status="SUCCESS",
            message="XGBoost model trained and loaded successfully into real-time pipeline.",
            model_version=metadata.get("model_version", MODEL_VERSION),
            metrics=metadata.get("metrics", {}),
            top_features=metadata.get("top_features", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@xgboost_router.get("/model-info")
def get_model_info():
    """
    Returns current model health, metadata, training metrics, and top contributing features.
    """
    metadata = GLOBAL_PREDICTOR.metadata or {}
    return {
        "status": "READY" if GLOBAL_PREDICTOR.is_ready() else "NOT_TRAINED",
        "model_version": metadata.get("model_version", MODEL_VERSION),
        "trained_at": metadata.get("trained_at"),
        "training_samples": metadata.get("training_samples", 0),
        "test_samples": metadata.get("test_samples", 0),
        "metrics": metadata.get("metrics", {}),
        "top_features": metadata.get("top_features", []),
        "weights": COMBINATION_WEIGHTS,
        "flag_thresholds": FLAG_THRESHOLDS,
    }


@xgboost_router.get("/predictions")
def get_predictions(
    bank: str = Query("ALL", description="SBI, AXIS, IOB, or ALL"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    flagged_only: bool = Query(False),
    risk_level: Optional[str] = Query(None),
):
    """
    Returns live stored XGBoost transaction risk assessments from PostgreSQL databases.
    """
    conns = get_all_bank_connections()
    assessments = get_recent_transaction_risk_assessments(
        conns=conns,
        bank=bank,
        limit=limit,
        offset=offset,
        flagged_only=flagged_only,
        risk_level=risk_level,
    )
    return {
        "count": len(assessments),
        "bank": bank.upper(),
        "assessments": assessments,
    }


@xgboost_router.get("/summary")
def get_summary(bank: str = Query("ALL")):
    """
    Returns aggregated KPI metrics for XGBoost risk scoring across bank databases.
    """
    conns = get_all_bank_connections()
    return get_xgboost_summary_stats(conns=conns, bank=bank)


@xgboost_router.get("/autonomous-status")
def get_autonomous_learning_status():
    """
    Returns real-time operational status of the continuous self-adaptation engine,
    including current adaptation generation, sample counts, 4-class metrics, and history.
    """
    from .autonomous_learner import GLOBAL_AUTONOMOUS_LEARNER
    return GLOBAL_AUTONOMOUS_LEARNER.get_status()


@xgboost_router.post("/autonomous-adapt")
def trigger_autonomous_adaptation(sample_limit: int = Query(24000, ge=1000, le=50000)):
    """
    Triggers an immediate background autonomous learning cycle on up to 50,000 samples.
    """
    from .autonomous_learner import GLOBAL_AUTONOMOUS_LEARNER
    res = GLOBAL_AUTONOMOUS_LEARNER.execute_adaptation_cycle(
        reason="Manual Trigger via API",
        sample_limit=sample_limit,
    )
    return res
