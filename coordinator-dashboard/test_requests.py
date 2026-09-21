import requests
import json

try:
    r = requests.get("http://127.0.0.1:8002/api/adsl/transactions?limit=2", timeout=3)
    data = r.json()
    txs = data.get("transactions", [])
    print(f"Transactions count: {len(txs)}")
    if txs:
        tx_id = txs[0]["transaction_id"]
        print(f"First tx: {tx_id}")
        gr = requests.get(f"http://127.0.0.1:8002/api/adsl/transaction-graph/{tx_id}", timeout=3)
        g_data = gr.json()
        print("Graph keys:", list(g_data.keys()))
        print("Graph nodes count:", len(g_data.get("nodes", [])))
        print("Graph edges count:", len(g_data.get("edges", [])))
        if g_data.get("nodes"):
            print("First node:", g_data["nodes"][0])
except Exception as e:
    print(f"Error: {e}")
