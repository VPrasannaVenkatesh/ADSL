"""
Module 3 Decentralized Risk Coordinator Test Script.
"""

import urllib.request
import json
import time

def test_pipeline():
    print("=" * 68)
    print("  TESTING MODULE 3: DECENTRALIZED RISK COORDINATOR PIPELINE")
    print("=" * 68)

    # 1. Check Coordinator API Health
    res_health = urllib.request.urlopen("http://localhost:8002/api/coordinator/health")
    print("[1] Coordinator Health:", res_health.read().decode())

    # 2. Start simulation
    req = urllib.request.Request(
        "http://localhost:8000/api/simulator/start",
        data=json.dumps({"mode": "fast"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req)
    print("[2] Simulator running... Generating live transactions...")
    time.sleep(3)

    # 3. Query Coordinated Decisions
    res_coord = urllib.request.urlopen("http://localhost:8002/api/coordinator/decisions?limit=4")
    data = json.loads(res_coord.read().decode())
    decisions = data.get("decisions", [])
    print(f"\n[3] Retrieved {len(decisions)} Coordinated Decisions from port 8002:")
    
    for d in decisions:
        print(f"\n  * [ID: {d['coordination_id']}] Tx: {d['transaction_id']}")
        print(f"    Flow       : {d['sender_bank']} ({d['sender_risk_score']}/100) -> {d['receiver_bank']} ({d['receiver_risk_score']}/100)")
        print(f"    Privacy    : Masked S={d['sender_masked_account']} | Masked R={d['receiver_masked_account']}")
        print(f"    Synthesized: Score={d['final_risk_score']}/100 | Level={d['final_risk_level']} | Decision={d['final_decision']}")
        if d.get("xgboost_risk_score") is not None:
            print(f"    ML Risk    : XGB={d['xgboost_risk_score']}/100 | Flagged={d.get('flagged', False)}")
        clean_reasons = [str(r).replace('\u20b9', 'INR ') for r in d.get('decision_reasons', [])[:2]]
        print(f"    Reasons    : {clean_reasons}")

    # 4. Query Summary
    res_sum = urllib.request.urlopen("http://localhost:8002/api/coordinator/summary")
    summary = json.loads(res_sum.read().decode())
    print("\n[4] Coordinator Summary Breakdown:")
    print("    Total Coordinated:", summary.get("total_coordinated"))
    print("    Decisions        :", summary.get("summary"))
    print("    Average Risk     :", summary.get("average_risk_score"))
    print("    By Bank Pairs    :", len(summary.get("by_pair", [])))
    print("=" * 68)

if __name__ == "__main__":
    test_pipeline()
