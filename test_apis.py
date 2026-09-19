import urllib.request
import json

def test(name, url, method="GET", data=None):
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            req.add_header("Content-Type", "application/json")
            data_bytes = json.dumps(data).encode("utf-8")
            res = urllib.request.urlopen(req, data=data_bytes, timeout=15)
        else:
            res = urllib.request.urlopen(req, timeout=15)
        body = json.loads(res.read().decode("utf-8"))
        print(f"[SUCCESS] {name}: {str(body)[:120]}...")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")

if __name__ == "__main__":
    print("Testing Bank Risk API (8001)...")
    test("Bank Risk Profile", "http://localhost:8001/risk/account/SBI-ACC-0001")
    test("Bank All Profiles", "http://localhost:8001/api/risk/profiles?bank=SBI&limit=5")

    print("\nTesting Simulator API (8000)...")
    test("Active Bank Status", "http://localhost:8000/api/simulator/active-bank")
    test("Switch Active Bank to AXIS", "http://localhost:8000/api/simulator/active-bank", method="POST", data={"bank": "AXIS"})
    test("Switch Active Bank to SBI", "http://localhost:8000/api/simulator/active-bank", method="POST", data={"bank": "SBI"})

    print("\nTesting ADSL API (8002)...")
    test("ADSL Mule Networks", "http://localhost:8002/api/adsl/mule-networks")
    test("ADSL Under Review", "http://localhost:8002/api/adsl/under-review")

    print("\nTesting ADSL Transaction Processing...")
    sample_normal_tx = {
        "transaction_id": "TEST-NORM-001",
        "sender_account": "SBI-ACC-0001",
        "receiver_account": "SBI-ACC-0002",
        "sender_bank": "SBI",
        "receiver_bank": "SBI",
        "amount": 250.0,
        "transaction_type": "TRANSFER",
        "timestamp": "2026-09-07T12:00:00"
    }
    test("ADSL Fast-Path Allow", "http://localhost:8002/adsl/transaction", method="POST", data=sample_normal_tx)

    sample_suspicious_tx = {
        "transaction_id": "TEST-SUSP-001",
        "sender_account": "SBI-ACC-0003",
        "receiver_account": "AXIS-ACC-0005",
        "sender_bank": "SBI",
        "receiver_bank": "AXIS",
        "amount": 490000.0,
        "transaction_type": "TRANSFER",
        "timestamp": "2026-09-07T12:00:01"
    }
    test("ADSL Suspicious Processing", "http://localhost:8002/adsl/transaction", method="POST", data=sample_suspicious_tx)
