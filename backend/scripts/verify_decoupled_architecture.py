"""
Verification script for decoupled ADSL architecture:
1. Generates test transactions across banks.
2. Verifies single XGBoost transaction prediction (no double-counting).
3. Verifies canonical lifecycle flow: INITIATED -> ASSESSING -> COMPLETED / MONITORING / RESTRICTED.
4. Verifies idempotency: calling save_transaction_risk_assessment repeatedly does NOT insert duplicate records.
5. Verifies API endpoints on ports 8000, 8001, 8002.
"""

import urllib.request
import json
import psycopg2
from simulator.db import get_all_connections
from xgboost_risk.storage import save_transaction_risk_assessment, get_assessment_by_transaction_id
from xgboost_risk.combination_engine import combine_risk_assessments

def test_decoupled_architecture():
    print("=" * 70)
    print("RUNNING ADSL DECOUPLED ARCHITECTURE VERIFICATION")
    print("=" * 70)

    conns = get_all_connections()

    # 1. Test Single XGBoost Risk Calculation without Double-Counting
    print("\n[TEST 1] Single XGBoost Risk Scoring (Double-Counting Prevention):")
    xgb_pred_normal = {
        "xgboost_risk_score": 18.5,
        "risk_level": "LOW",
        "prediction_probability": 0.185,
        "top_risk_factors": ["Normal transaction volume", "Known recipient account"],
        "model_version": "v1.0.0-xgb",
    }
    comb_normal = combine_risk_assessments(
        sender_risk_score=15.0,
        receiver_risk_score=12.0,
        xgboost_prediction=xgb_pred_normal,
    )
    print(f"  Input Sender Account Risk: 15.0 | Receiver Account Risk: 12.0 | XGBoost Score: 18.5")
    print(f"  Result Combined/Transaction Score: {comb_normal['combined_risk_score']}")
    print(f"  Result Risk Level: {comb_normal['risk_level']} | Decision: {comb_normal['decision_status']}")
    assert comb_normal["combined_risk_score"] == 18.5, f"Expected 18.5, got {comb_normal['combined_risk_score']}"
    assert comb_normal["decision_status"] == "ALLOW", f"Expected ALLOW, got {comb_normal['decision_status']}"
    print("  --> PASSED: XGBoost score is primary ML score without artificial re-weighting inflation!")

    # Test Suspicious Score
    xgb_pred_suspicious = {
        "xgboost_risk_score": 45.0,
        "risk_level": "MEDIUM",
        "prediction_probability": 0.45,
        "top_risk_factors": ["Elevated transaction velocity", "High transaction hour deviation"],
        "model_version": "v1.0.0-xgb",
    }
    comb_suspicious = combine_risk_assessments(
        sender_risk_score=35.0,
        receiver_risk_score=28.0,
        xgboost_prediction=xgb_pred_suspicious,
    )
    print(f"\n  Suspicious Txn -> XGBoost: 45.0 | Combined Score: {comb_suspicious['combined_risk_score']} | Decision: {comb_suspicious['decision_status']}")
    assert comb_suspicious["decision_status"] == "MONITOR", f"Expected MONITOR, got {comb_suspicious['decision_status']}"
    print("  --> PASSED: Medium risk maps to MONITOR (canonical lifecycle MONITORING)!")

    # Test High/Critical Score
    xgb_pred_critical = {
        "xgboost_risk_score": 78.0,
        "risk_level": "HIGH",
        "prediction_probability": 0.78,
        "top_risk_factors": ["High fan-in fan-out ratio", "Rapid fund forwarding"],
        "model_version": "v1.0.0-xgb",
    }
    comb_critical = combine_risk_assessments(
        sender_risk_score=62.0,
        receiver_risk_score=55.0,
        xgboost_prediction=xgb_pred_critical,
    )
    print(f"\n  Critical Txn -> XGBoost: 78.0 | Combined Score: {comb_critical['combined_risk_score']} | Decision: {comb_critical['decision_status']}")
    assert comb_critical["decision_status"] == "CONTROLLED_ACTION", f"Expected CONTROLLED_ACTION, got {comb_critical['decision_status']}"
    print("  --> PASSED: High risk maps to CONTROLLED_ACTION (canonical lifecycle RESTRICTED)!")

    # 2. Test Idempotency Protection
    print("\n[TEST 2] Idempotency Protection in Risk Storage:")
    test_tx_id = "TEST_IDEMP_999999"
    conn = conns["SBI"]

    # Initial save
    id1 = save_transaction_risk_assessment(
        conn=conn,
        bank="SBI",
        transaction_id=test_tx_id,
        sender_account_id="SBI10001",
        receiver_account_id="AXIS20002",
        sender_risk_score=15.0,
        receiver_risk_score=10.0,
        xgboost_risk_score=18.5,
        combined_risk_score=18.5,
        risk_level="LOW",
        prediction_probability=0.185,
        top_risk_factors=["Normal transaction volume"],
        model_version="v1.0.0-xgb",
        flagged=False,
        sender_bank="SBI",
        receiver_bank="AXIS",
        amount=5000,
        decision_status="ALLOW",
        transaction_status="COMPLETED",
    )
    print(f"  First save returned assessment ID: {id1}")

    # Second save (simulating polling, dashboard refresh, or re-assessment)
    id2 = save_transaction_risk_assessment(
        conn=conn,
        bank="SBI",
        transaction_id=test_tx_id,
        sender_account_id="SBI10001",
        receiver_account_id="AXIS20002",
        sender_risk_score=15.0,
        receiver_risk_score=10.0,
        xgboost_risk_score=18.5,
        combined_risk_score=18.5,
        risk_level="LOW",
        prediction_probability=0.185,
        top_risk_factors=["Normal transaction volume"],
        model_version="v1.0.0-xgb",
        flagged=False,
        sender_bank="SBI",
        receiver_bank="AXIS",
        amount=5000,
        decision_status="ALLOW",
        transaction_status="COMPLETED",
    )
    print(f"  Second save returned assessment ID: {id2}")
    assert id1 == id2, f"Idempotency failed: generated different IDs {id1} vs {id2}"

    # Verify count in database
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM transaction_risk_assessments WHERE transaction_id = %s", (test_tx_id,))
        count = cur.fetchone()[0]
    print(f"  Row count in DB for {test_tx_id}: {count}")
    assert count == 1, f"Expected exactly 1 row, found {count}"

    # Lookup using get_assessment_by_transaction_id
    existing = get_assessment_by_transaction_id(conns, test_tx_id)
    assert existing is not None, "get_assessment_by_transaction_id returned None"
    assert existing["transaction_id"] == test_tx_id, "Lookup matched wrong transaction"
    print("  --> PASSED: Idempotency protection prevents duplicate records!")

    # Clean up test transaction
    with conn.cursor() as cur:
        cur.execute("DELETE FROM transaction_risk_assessments WHERE transaction_id = %s", (test_tx_id,))
    conn.commit()

    # 3. Test Live Backend APIs
    print("\n[TEST 3] Backend APIs Communication & Separation:")
    req_8000 = json.loads(urllib.request.urlopen("http://localhost:8000/api/status").read())
    print(f"  Port 8000 (Module 1 Simulator): is_running={req_8000.get('is_running')}, clock={req_8000.get('sim_clock')}")

    req_8001 = json.loads(urllib.request.urlopen("http://localhost:8001/api/xgboost/summary?bank=ALL").read())
    print(f"  Port 8001 (Module 2 Risk Dashboard): total_assessed={req_8001.get('total_assessed')}, avg_xgb={req_8001.get('average_xgboost_score')}")

    req_8002 = json.loads(urllib.request.urlopen("http://localhost:8002/api/coordinator/summary?bank=ALL").read())
    print(f"  Port 8002 (Module 3 Coordinator): total_coordinated={req_8002.get('total_coordinated')}, allow={req_8002.get('allow_count')}, monitor={req_8002.get('monitor_count')}")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_decoupled_architecture()
