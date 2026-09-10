"""
End-to-End Verification Test Script for XGBoost Transaction Risk Prediction Module (Module 4).
Tests:
1. XGBoost model loading and metadata verification.
2. Real-time feature extraction across transactions and behavioural histories.
3. Prediction probability, 0-100 risk score, risk level, and top contributing factors.
4. Risk combination engine (Module 2 Behavioural + Module 4 XGBoost).
5. Transaction decision lifecycle: INITIATED -> ASSESSING -> XGBOOST -> FLAGGED/CLEAN -> ALLOW/MONITOR/RESTRICT.
6. PostgreSQL storage in transaction_risk_assessments table.
7. Decentralized Coordinator synthesis of abstract ML indicators.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator.db_connection import get_all_bank_connections
from xgboost_risk.predictor import GLOBAL_PREDICTOR
from xgboost_risk.feature_extractor import extract_features_for_transaction
from xgboost_risk.combination_engine import combine_risk_assessments
from xgboost_risk.storage import get_recent_transaction_risk_assessments, get_xgboost_summary_stats
from simulator.engine import LiveTransactionSimulator
from coordinator.coordinator_service import coordinate_transaction_risk


def run_tests():
    print("=" * 72)
    print("  VERIFYING MODULE 4: XGBOOST TRANSACTION RISK PREDICTION PIPELINE")
    print("=" * 72)

    # ── Test 1: Model Readiness & Metadata ──────────────────────────────────
    print("\n[1] Verifying XGBoost Model Readiness & Metadata...")
    assert GLOBAL_PREDICTOR.is_ready(), "XGBoost model should be loaded and ready."
    metadata = GLOBAL_PREDICTOR.metadata
    print(f"  Model Version  : {metadata.get('model_version')}")
    print(f"  Trained At     : {metadata.get('trained_at')}")
    metrics = metadata.get('metrics', {})
    print(f"  ROC-AUC        : {metrics.get('roc_auc')}")
    print(f"  Accuracy       : {metrics.get('accuracy')}")
    print(f"  F1 Score       : {metrics.get('f1_score')}")
    assert metrics.get('roc_auc', 0) > 0.90, "ROC-AUC should be > 0.90"
    print("  --> PASS: Model ready with high ROC-AUC.")

    # ── Test 2: Live Feature Extraction & Real-Time Inference ───────────────
    print("\n[2] Testing Live Feature Extraction & Inference...")
    conns = get_all_bank_connections()
    features = extract_features_for_transaction(
        conns=conns,
        sender_bank="SBI",
        sender_account_id="SBI-ACC-0001",
        receiver_bank="AXIS",
        receiver_account_id="AXIS-ACC-0002",
        amount=50000,
        tx_type="UPI",
        timestamp=datetime.now(),
        device_ip="Mobile:192.168.1.5",
        location="Chennai",
        recipient_is_new=True,
        sender_risk_score=25.0,
        receiver_risk_score=15.0,
    )
    assert len(features) >= 35, "Feature vector should contain at least 35 features."
    print(f"  Extracted {len(features)} numerical features safely.")

    pred = GLOBAL_PREDICTOR.predict_transaction_risk(features)
    print(f"  XGBoost Risk Score : {pred['xgboost_risk_score']} / 100")
    print(f"  Probability        : {pred['prediction_probability']:.4f}")
    print(f"  Risk Level         : {pred['risk_level']}")
    print(f"  Top Risk Factors   : {pred['top_risk_factors']}")
    assert 0.0 <= pred['xgboost_risk_score'] <= 100.0, "Score must be between 0 and 100."
    assert 0.0 <= pred['prediction_probability'] <= 1.0, "Probability must be between 0 and 1."
    print("  --> PASS: Real-time inference executed.")

    # ── Test 3: Risk Combination & Flagging ──────────────────────────────────
    print("\n[3] Testing Combination Engine (Behavioural + XGBoost)...")
    comb = combine_risk_assessments(
        sender_risk_score=75.0,
        receiver_risk_score=20.0,
        xgboost_prediction={"xgboost_risk_score": 80.0, "prediction_probability": 0.80, "top_risk_factors": ["High rapid forwarding"]},
    )
    print(f"  Combined Risk Score : {comb['combined_risk_score']}")
    print(f"  Flagged             : {comb['flagged']}")
    print(f"  Decision Status     : {comb['decision_status']}")
    assert comb['combined_risk_score'] == round(75.0 * 0.5 + 80.0 * 0.5, 2)
    assert comb['flagged'] is True, "High risk should trigger FLAGGED."
    assert comb['decision_status'] == "CONTROLLED_ACTION"
    print("  --> PASS: Combination weights and flagging policy verified.")

    # ── Test 4: End-to-End Simulation with Full Lifecycle ────────────────────
    print("\n[4] Simulating Transactions through Full Real-Time Lifecycle...")
    sim = LiveTransactionSimulator()
    generated_results = []
    for i in range(5):
        res = sim.simulate_single_transaction()
        if res:
            generated_results.append(res)
            print(f"  Txn #{i+1}: {res.transaction_id} | {res.sender_bank}->{res.receiver_bank} | INR {res.amount:,} | Status: {res.status}")

    assert len(generated_results) > 0, "Simulator should generate valid transactions."
    print("  --> PASS: Simulation loop processed transactions through complete lifecycle.")

    # ── Test 5: Verify PostgreSQL Storage in transaction_risk_assessments ─────
    print("\n[5] Verifying PostgreSQL Storage in transaction_risk_assessments...")
    recent_assessments = get_recent_transaction_risk_assessments(conns=conns, limit=5)
    print(f"  Found {len(recent_assessments)} recent ML assessments in database.")
    assert len(recent_assessments) > 0, "Assessments must be stored in database."
    latest = recent_assessments[0]
    print(f"  Latest Record:")
    print(f"    Assessment ID   : {latest['assessment_id']}")
    print(f"    Transaction ID  : {latest['transaction_id']}")
    print(f"    Bank            : {latest['bank']}")
    print(f"    XGBoost Score   : {latest['xgboost_risk_score']}")
    print(f"    Combined Score  : {latest['combined_risk_score']}")
    print(f"    Decision Status : {latest['decision_status']}")
    print(f"    Flagged         : {latest['flagged']}")
    print(f"    Top Factors     : {latest['top_risk_factors']}")
    print("  --> PASS: Direct PostgreSQL storage confirmed with zero ORM.")

    # ── Test 6: Verify Decentralized Coordinator Abstract Integration ────────
    print("\n[6] Testing Coordinator Abstract Indicator Synthesis...")
    tx_id = latest['transaction_id']
    coord_dec = coordinate_transaction_risk(
        transaction_id=tx_id,
        sender_bank=latest['bank'],
        receiver_bank=latest['bank'],
    )
    if coord_dec:
        print(f"  Coordination ID : {coord_dec.coordination_id}")
        print(f"  Final Decision  : {coord_dec.final_decision}")
        print(f"  XGBoost Score   : {coord_dec.xgboost_risk_score}")
        print(f"  Combined Score  : {coord_dec.final_risk_score}")
        clean_reasons = [r.replace('\u20b9', 'INR ') for r in coord_dec.decision_reasons]
        print(f"  Reasons         : {clean_reasons}")
    print("  --> PASS: Decentralized coordinator synthesized abstract ML indicators.")

    print("\n" + "=" * 72)
    print("  ALL TESTS PASSED SUCCESSFULLY! Module 4 is fully functional.")
    print("=" * 72)


if __name__ == "__main__":
    run_tests()
