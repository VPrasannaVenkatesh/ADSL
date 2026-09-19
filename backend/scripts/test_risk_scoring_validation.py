"""
Validation script for Transaction Filtering and Continuous XGBoost Feature-Processing Logic.
Tests all 7 explicit test cases required by Section 22:
- CASE 1: Normal personal transaction -> LOW -> COMPLETED
- CASE 2: Large legitimate business transaction -> LOW/MEDIUM (NOT HIGH) -> Expected based on business behaviour
- CASE 3: New beneficiary + moderate transaction deviation -> MEDIUM -> MONITORING
- CASE 4: Repeated rapid transactions + unusual device + unusual location -> HIGH -> HONEYPOT + LIEN
- CASE 5: Fan-in + rapid forwarding + multiple counterparties -> HIGH -> HONEYPOT -> NetworkX/GNN
- CASE 6: Medium-risk transaction followed by normal behaviour -> MONITORING -> GENUINE -> COMPLETED
- CASE 7: Medium-risk transaction followed by suspicious mule behaviour -> MONITORING -> HONEYPOT -> ADSL
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from simulator.db_connection import get_all_bank_connections
from xgboost_risk.predictor import GLOBAL_PREDICTOR
from xgboost_risk.feature_extractor import extract_features_for_transaction
from coordinator.adsl_service import process_adsl_transaction
from coordinator.monitoring_manager import GLOBAL_MONITORING_MANAGER
from xgboost_risk.storage import get_recent_transaction_risk_assessments


def run_all_validation_cases():
    print("=" * 80)
    print("  EXECUTING SECTION 22 FINAL VALIDATION: 7 REALISTIC TEST SCENARIOS")
    print("=" * 80)

    conns = get_all_bank_connections()

    # Find genuine personal accounts and business accounts from SBI and AXIS
    sbi_conn = conns["SBI"]
    with sbi_conn.cursor() as cur:
        cur.execute("""
            SELECT a.account_id, a.home_location FROM accounts a
            LEFT JOIN behaviour_history bh ON a.account_id = bh.account_id AND bh.behaviour_date = CURRENT_DATE
            WHERE a.account_type = 'PERSONAL' AND a.account_status = 'ACTIVE'
              AND COALESCE(bh.transaction_count, 0) = 0
            LIMIT 1
        """)
        row1 = cur.fetchone()
        personal_acc_1, personal_loc_1 = row1[0], row1[1]

        cur.execute("""
            SELECT a.account_id, a.home_location FROM accounts a
            LEFT JOIN behaviour_history bh ON a.account_id = bh.account_id AND bh.behaviour_date = CURRENT_DATE
            WHERE a.account_type = 'PERSONAL' AND a.account_status = 'ACTIVE'
              AND COALESCE(bh.transaction_count, 0) = 0
              AND a.account_id != %s
            LIMIT 1
        """, (personal_acc_1,))
        row2 = cur.fetchone()
        personal_acc_2, personal_loc_2 = row2[0], row2[1]

        cur.execute("""
            SELECT a.account_id, a.home_location FROM accounts a
            WHERE a.account_type = 'BUSINESS' AND a.account_status = 'ACTIVE'
            LIMIT 1
        """)
        row_b1 = cur.fetchone()
        biz_acc_1, biz_loc_1 = row_b1[0], row_b1[1]

        cur.execute("""
            SELECT a.account_id, a.home_location FROM accounts a
            WHERE a.account_type = 'BUSINESS' AND a.account_status = 'ACTIVE'
            OFFSET 1 LIMIT 1
        """)
        row_b2 = cur.fetchone()
        biz_acc_2, biz_loc_2 = row_b2[0], row_b2[1]

    print(f"Test Accounts identified:")
    print(f"  • Personal 1: {personal_acc_1} ({personal_loc_1}) | Personal 2: {personal_acc_2} ({personal_loc_2})")
    print(f"  • Business 1: {biz_acc_1} ({biz_loc_1}) | Business 2: {biz_acc_2} ({biz_loc_2})\n")

    results = []

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 1: Normal Personal Transaction
    # Expected: LOW Risk (Score <= 30.0), Status: COMPLETED
    # ──────────────────────────────────────────────────────────────────────────
    print("─" * 80)
    print("[CASE 1] Normal Personal Transaction (Small everyday domestic transfer)")
    tx1_data = {
        "transaction_id": f"TXN-VAL-C1-{int(time.time()*1000)}",
        "sender_bank": "SBI",
        "sender_account_id": personal_acc_1,
        "receiver_bank": "SBI",
        "receiver_account_id": personal_acc_2,
        "amount": 2500,
        "transaction_type": "UPI",
        "transaction_timestamp": datetime.now().replace(hour=14).isoformat(),
        "device_ip": "Mobile:192.168.1.5",
        "location": personal_loc_1,
        "recipient_is_new": False,
    }
    res1 = process_adsl_transaction(tx1_data)
    print(f"  → Numerical XGBoost Score: {res1['risk_score']:.1f}")
    print(f"  → Risk Level: {res1['risk_level']}")
    print(f"  → Status: {res1['status']}")
    print(f"  → Key Signals: {res1.get('risk_reasons', [])[:2]}")

    c1_pass = (res1['risk_score'] <= 30.0 and res1['risk_level'] == 'LOW' and res1['status'] == 'COMPLETED')
    results.append(("CASE 1: Normal personal transaction", c1_pass, f"Score: {res1['risk_score']:.1f}, Status: {res1['status']}"))
    assert c1_pass, f"Case 1 failed: {res1}"

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 2: Large Legitimate Business Transaction
    # Expected: LOW or MEDIUM Risk (Score <= 60.0, NOT HIGH), Status: COMPLETED or MONITORING
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 80)
    print("[CASE 2] Large Legitimate Business Transaction (₹450,000 corporate payment)")
    tx2_data = {
        "transaction_id": f"TXN-VAL-C2-{int(time.time()*1000)}",
        "sender_bank": "SBI",
        "sender_account_id": biz_acc_1,
        "receiver_bank": "AXIS",
        "receiver_account_id": biz_acc_2,
        "amount": 450000,
        "transaction_type": "NEFT",
        "transaction_timestamp": datetime.now().replace(hour=14, minute=30).isoformat(),
        "device_ip": "Laptop:10.0.0.12",
        "location": biz_loc_1,
        "recipient_is_new": False,
    }
    res2 = process_adsl_transaction(tx2_data)
    print(f"  → Numerical XGBoost Score: {res2['risk_score']:.1f}")
    print(f"  → Risk Level: {res2['risk_level']}")
    print(f"  → Status: {res2['status']}")
    print(f"  → Key Signals: {res2.get('risk_reasons', [])[:2]}")

    c2_pass = (res2['risk_score'] <= 60.0 and res2['risk_level'] != 'HIGH' and res2['status'] != 'HONEYPOT')
    results.append(("CASE 2: Large legitimate business transaction", c2_pass, f"Score: {res2['risk_score']:.1f}, Level: {res2['risk_level']} (Not High)"))
    assert c2_pass, f"Case 2 failed: Large business transaction incorrectly flagged as High: {res2}"

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 3: New Beneficiary + Moderate Transaction Deviation
    # Expected: MEDIUM Risk (31.0 - 60.0), Status: MONITORING
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 80)
    print("[CASE 3] New Beneficiary + Moderate Transaction Deviation (₹32,000 to new recipient)")
    # Generate a fresh new recipient account ID
    tx3_data = {
        "transaction_id": f"TXN-VAL-C3-{int(time.time()*1000)}",
        "sender_bank": "SBI",
        "sender_account_id": personal_acc_1,
        "receiver_bank": "AXIS",
        "receiver_account_id": personal_acc_2,
        "amount": 32000,
        "transaction_type": "IMPS",
        "transaction_timestamp": datetime.now().replace(hour=15).isoformat(),
        "device_ip": "Mobile:192.168.1.5",
        "location": personal_loc_1,
        "recipient_is_new": True,  # New beneficiary
    }
    res3 = process_adsl_transaction(tx3_data)
    print(f"  → Numerical XGBoost Score: {res3['risk_score']:.1f}")
    print(f"  → Risk Level: {res3['risk_level']}")
    print(f"  → Status: {res3['status']}")
    print(f"  → Key Signals: {res3.get('risk_reasons', [])[:3]}")

    c3_pass = (30.0 < res3['risk_score'] <= 60.0 and res3['risk_level'] == 'MEDIUM' and res3['status'] == 'MONITORING')
    results.append(("CASE 3: New beneficiary + moderate deviation", c3_pass, f"Score: {res3['risk_score']:.1f}, Status: {res3['status']}"))
    assert c3_pass, f"Case 3 failed: Expected MEDIUM / MONITORING: {res3}"

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 4: Repeated Rapid Transactions + Unusual Device + Unusual Location
    # Expected: HIGH Risk (Score > 60.0), Status: HONEYPOT + LIEN APPLIED
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 80)
    print("[CASE 4] Repeated Rapid Transactions + Unusual Device + Location Deviation")
    # Simulate an account experiencing rapid velocity burst, new device, and new location
    tx4_data = {
        "transaction_id": f"TXN-VAL-C4-{int(time.time()*1000)}",
        "sender_bank": "SBI",
        "sender_account_id": personal_acc_1,
        "receiver_bank": "IOB",
        "receiver_account_id": personal_acc_2,
        "amount": 75000,
        "transaction_type": "UPI",
        "transaction_timestamp": datetime.now().replace(hour=2, minute=15).isoformat(),
        "device_ip": "Other:185.220.101.5",  # foreign anomalous device
        "location": "Kolkata",               # foreign location
        "recipient_is_new": True,
    }
    # Pass simulated behavioral velocity spike directly to test predictor accuracy
    feat4 = extract_features_for_transaction(
        conns=conns,
        sender_bank="SBI",
        sender_account_id=personal_acc_1,
        receiver_bank="IOB",
        receiver_account_id=personal_acc_2,
        amount=75000,
        tx_type="UPI",
        timestamp=datetime.now().replace(hour=2, minute=15),
        device_ip="Other:185.220.101.5",
        location="Kolkata",
        recipient_is_new=True,
    )
    feat4["sender_tx_1h"] = 6.0
    feat4["sender_burst_ratio"] = 4.2
    feat4["sender_velocity_ratio"] = 5.0
    feat4["sender_device_changes"] = 3.0
    feat4["sender_location_changes"] = 2.0
    feat4["device_location_anomaly"] = 1.0
    feat4["is_location_deviation"] = 1.0
    feat4["is_new_device"] = 1.0
    feat4["is_night"] = 1.0
    feat4["is_unusual_hour"] = 1.0
    feat4["sender_behavioural_risk_score"] = 78.0

    pred4 = GLOBAL_PREDICTOR.predict_transaction_risk(feat4)
    tx4_data["xgboost_risk_score"] = pred4["xgboost_risk_score"]
    tx4_data["risk_level"] = pred4["risk_level"]
    tx4_data["risk_reasons"] = pred4["top_risk_factors"]
    res4 = process_adsl_transaction(tx4_data)

    print(f"  → Numerical XGBoost Score: {res4['risk_score']:.1f}")
    print(f"  → Risk Level: {res4['risk_level']}")
    print(f"  → Status: {res4['status']}")
    print(f"  → Lien Applied: {res4.get('lien_applied')}")
    print(f"  → Key Signals: {res4.get('risk_reasons', [])[:3]}")

    c4_pass = (res4['risk_score'] > 60.0 and res4['risk_level'] == 'HIGH' and res4['status'] in ('HONEYPOT', 'RESTRICTED') and res4.get('lien_applied'))
    results.append(("CASE 4: Repeated rapid + unusual device/location", c4_pass, f"Score: {res4['risk_score']:.1f}, Status: {res4['status']}, Lien: {res4.get('lien_applied')}"))
    assert c4_pass, f"Case 4 failed: Expected HIGH / HONEYPOT + LIEN: {res4}"

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 5: Fan-In + Rapid Forwarding + Multiple Counterparties (Mule Network)
    # Expected: HIGH Risk (Score > 60.0), Status: HONEYPOT -> NetworkX/GNN Analysis
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 80)
    print("[CASE 5] Fan-In + Rapid Forwarding + Multiple Counterparties (Mule Layering)")
    feat5 = extract_features_for_transaction(
        conns=conns,
        sender_bank="SBI",
        sender_account_id=personal_acc_2,
        receiver_bank="AXIS",
        receiver_account_id=personal_acc_1,
        amount=88000,
        tx_type="IMPS",
        timestamp=datetime.now(),
        device_ip="Mobile:192.168.1.99",
        location="Chennai",
        recipient_is_new=True,
    )
    feat5["network_rapid_forwarding"] = 1.0
    feat5["network_short_dwell_flag"] = 1.0
    feat5["receiver_fan_in"] = 5.0
    feat5["sender_fan_out"] = 4.0
    feat5["sender_short_dwell_count"] = 3.0
    feat5["sender_forwarded_amount"] = 84000.0
    feat5["sender_behavioural_risk_score"] = 78.0

    pred5 = GLOBAL_PREDICTOR.predict_transaction_risk(feat5)
    tx5_data = {
        "transaction_id": f"TXN-VAL-C5-{int(time.time()*1000)}",
        "sender_bank": "SBI",
        "sender_account_id": personal_acc_2,
        "receiver_bank": "AXIS",
        "receiver_account_id": personal_acc_1,
        "amount": 88000,
        "transaction_type": "IMPS",
        "transaction_timestamp": datetime.now().isoformat(),
        "device_ip": "Mobile:192.168.1.99",
        "location": "Chennai",
        "recipient_is_new": True,
        "xgboost_risk_score": pred5["xgboost_risk_score"],
        "risk_level": pred5["risk_level"],
        "risk_reasons": pred5["top_risk_factors"],
    }
    res5 = process_adsl_transaction(tx5_data)

    print(f"  → Numerical XGBoost Score: {res5['risk_score']:.1f}")
    print(f"  → Risk Level: {res5['risk_level']}")
    print(f"  → Status: {res5['status']}")
    print(f"  → GNN / Mule Network Tracked: {res5.get('mule_network_id') or res5.get('deep_analysis_performed')}")
    print(f"  → Key Signals: {res5.get('risk_reasons', [])[:3]}")

    c5_pass = (res5['risk_score'] > 60.0 and res5['risk_level'] == 'HIGH' and res5['status'] in ('HONEYPOT', 'RESTRICTED') and res5.get('deep_analysis_performed'))
    results.append(("CASE 5: Fan-in + rapid forwarding mule", c5_pass, f"Score: {res5['risk_score']:.1f}, Status: {res5['status']}, Graph Analysis: True"))
    assert c5_pass, f"Case 5 failed: Expected HIGH / HONEYPOT: {res5}"

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 6: Medium-Risk Transaction followed by Normal Behaviour
    # Expected: MONITORING -> GENUINE -> NORMAL TRANSACTION FLOW (COMPLETED)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 80)
    print("[CASE 6] Medium-Risk Transaction followed by Genuine Normal Behaviour")
    monitored_account = f"ACC-MON-{int(time.time())%10000}"
    tx6_initial_id = f"TXN-VAL-C6-INIT-{int(time.time()*1000)}"

    # 6A. Initial Medium-Risk Transaction -> enters MONITORING
    tx6_data = {
        "transaction_id": tx6_initial_id,
        "sender_bank": "SBI",
        "sender_account_id": monitored_account,
        "receiver_bank": "SBI",
        "receiver_account_id": personal_acc_1,
        "amount": 35000,
        "transaction_type": "UPI",
        "transaction_timestamp": datetime.now().isoformat(),
        "device_ip": "Mobile:192.168.1.1",
        "location": "Chennai",
        "recipient_is_new": True,
    }
    res6_init = process_adsl_transaction(tx6_data)
    print(f"  6A. Initial Transaction Status: {res6_init['status']} (Risk Score: {res6_init['risk_score']:.1f})")

    # 6B. Subsequent Transaction with Normal Domestic Behaviour
    tx6_followup_id = f"TXN-VAL-C6-SUB-{int(time.time()*1000)}"
    tx6_sub = {
        "transaction_id": tx6_followup_id,
        "sender_bank": "SBI",
        "sender_account_id": monitored_account,
        "receiver_bank": "SBI",
        "receiver_account_id": personal_acc_1,
        "amount": 1500,  # normal small grocery/utility payment
        "transaction_type": "UPI",
        "transaction_timestamp": datetime.now().isoformat(),
        "device_ip": "Mobile:192.168.1.1",
        "location": "Chennai",
        "recipient_is_new": False,
    }
    res6_sub = process_adsl_transaction(tx6_sub)
    print(f"  6B. Follow-up Transaction Status: {res6_sub['status']} (Risk Score: {res6_sub['risk_score']:.1f})")

    time.sleep(0.5)
    # Check case outcome in monitoring manager
    mon_case6 = GLOBAL_MONITORING_MANAGER.get_case_for_account(monitored_account)
    status6 = mon_case6.get("status") if mon_case6 else "NOT_FOUND"
    outcome6 = mon_case6.get("final_outcome") if mon_case6 else None
    print(f"  6C. Monitoring Case Resolution: Status={status6}, Outcome={outcome6}")

    c6_pass = (mon_case6 is not None and status6 in ('RESOLVED_AS_GENUINE', 'RESOLVED_GENUINE'))
    results.append(("CASE 6: Medium-risk resolved to GENUINE", c6_pass, f"Outcome: {outcome6}, Status: {status6}"))
    assert c6_pass, f"Case 6 failed: {mon_case6}"

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 7: Medium-Risk Transaction followed by Suspicious Mule Behaviour
    # Expected: MONITORING -> HONEYPOT -> ADSL Network Analysis
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 80)
    print("[CASE 7] Medium-Risk Transaction followed by Suspicious Mule Behaviour")
    mule_watch_acc = f"ACC-MULE-{int(time.time())%10000}"
    tx7_initial_id = f"TXN-VAL-C7-INIT-{int(time.time()*1000)}"

    # 7A. Initial Medium-Risk Transaction
    tx7_data = {
        "transaction_id": tx7_initial_id,
        "sender_bank": "SBI",
        "sender_account_id": mule_watch_acc,
        "receiver_bank": "AXIS",
        "receiver_account_id": personal_acc_2,
        "amount": 40000,
        "transaction_type": "UPI",
        "transaction_timestamp": datetime.now().isoformat(),
        "device_ip": "Mobile:192.168.1.20",
        "location": "Chennai",
        "recipient_is_new": True,
    }
    res7_init = process_adsl_transaction(tx7_data)
    print(f"  7A. Initial Transaction Status: {res7_init['status']} (Risk Score: {res7_init['risk_score']:.1f})")

    # 7B. Follow-up Transaction with Rapid Forwarding & Foreign Device (Mule Hop)
    feat7 = extract_features_for_transaction(
        conns=conns,
        sender_bank="SBI",
        sender_account_id=mule_watch_acc,
        receiver_bank="IOB",
        receiver_account_id=personal_acc_1,
        amount=79000,
        tx_type="IMPS",
        timestamp=datetime.now(),
        device_ip="Other:103.25.4.1",
        location="Mumbai",
        recipient_is_new=True,
    )
    feat7["network_rapid_forwarding"] = 1.0
    feat7["network_short_dwell_flag"] = 1.0
    feat7["sender_short_dwell_count"] = 2.0
    feat7["sender_tx_1h"] = 5.0
    feat7["sender_burst_ratio"] = 3.8
    feat7["device_location_anomaly"] = 1.0
    feat7["is_new_device"] = 1.0
    feat7["is_location_deviation"] = 1.0
    feat7["sender_behavioural_risk_score"] = 82.0

    pred7 = GLOBAL_PREDICTOR.predict_transaction_risk(feat7)
    tx7_sub = {
        "transaction_id": f"TXN-VAL-C7-MULE-{int(time.time()*1000)}",
        "sender_bank": "SBI",
        "sender_account_id": mule_watch_acc,
        "receiver_bank": "IOB",
        "receiver_account_id": personal_acc_1,
        "amount": 79000,
        "transaction_type": "IMPS",
        "transaction_timestamp": datetime.now().isoformat(),
        "device_ip": "Other:103.25.4.1",
        "location": "Mumbai",
        "recipient_is_new": True,
        "xgboost_risk_score": pred7["xgboost_risk_score"],
        "risk_level": pred7["risk_level"],
        "risk_reasons": pred7["top_risk_factors"],
    }
    res7_sub = process_adsl_transaction(tx7_sub)
    print(f"  7B. Follow-up Transaction Status: {res7_sub['status']} (Risk Score: {res7_sub['risk_score']:.1f})")

    time.sleep(0.5)
    mon_case7 = GLOBAL_MONITORING_MANAGER.get_case_for_account(mule_watch_acc)
    status7 = mon_case7.get("status") if mon_case7 else "NOT_FOUND"
    outcome7 = mon_case7.get("final_outcome") if mon_case7 else None
    print(f"  7C. Monitoring Case Resolution: Status={status7}, Outcome={outcome7}")

    c7_pass = (mon_case7 is not None and status7 in ('ESCALATED_TO_HIGH_RISK', 'ESCALATED'))
    results.append(("CASE 7: Medium-risk escalated to HONEYPOT", c7_pass, f"Outcome: {outcome7}, Status: {status7}"))
    assert c7_pass, f"Case 7 failed: {mon_case7}"

    # ──────────────────────────────────────────────────────────────────────────
    # SUMMARY REPORT
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  FINAL VALIDATION RESULTS SUMMARY")
    print("=" * 80)
    all_passed = True
    for title, passed, details in results:
        mark = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False
        print(f"  {mark:8} | {title:48} | {details}")

    print("=" * 80)
    if all_passed:
        print("  ALL 7 VALIDATION CASES PASSED WITH 100% SUCCESS!")
    else:
        print("  ONE OR MORE CASES FAILED. REVIEW DETAILS ABOVE.")
    print("=" * 80)


if __name__ == "__main__":
    run_all_validation_cases()
