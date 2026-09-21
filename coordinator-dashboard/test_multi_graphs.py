import requests

r = requests.get("http://127.0.0.1:8002/api/adsl/transactions?limit=20")
txs = r.json().get("transactions", [])
print(f"Total txs fetched: {len(txs)}")
success_count = 0
for t in txs:
    tid = t["transaction_id"]
    gr = requests.get(f"http://127.0.0.1:8002/api/adsl/transaction-graph/{tid}")
    if gr.status_code == 200:
        data = gr.json()
        success_count += 1
        print(f"OK: {tid} -> {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges")
    else:
        print(f"FAIL {gr.status_code}: {tid}")
print(f"Summary: {success_count}/{len(txs)} succeeded")
