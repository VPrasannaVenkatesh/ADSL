import urllib.request
import json

try:
    with urllib.request.urlopen("http://localhost:8002/api/adsl/transactions?limit=5") as response:
        tx_data = json.loads(response.read().decode())
        txs = tx_data.get("transactions", [])
        print(f"Transactions found: {len(txs)}")
        if txs:
            first_tx = txs[0]
            tx_id = first_tx["transaction_id"]
            print(f"Testing transaction: {tx_id}")
            
            graph_url = f"http://localhost:8002/api/adsl/transaction-graph/{tx_id}"
            with urllib.request.urlopen(graph_url) as g_res:
                g_data = json.loads(g_res.read().decode())
                nodes = g_data.get("nodes", [])
                edges = g_data.get("edges", [])
                print(f"Graph response status 200: {len(nodes)} nodes, {len(edges)} edges")
                print("Nodes:", [n.get("account_id") for n in nodes[:5]])
except Exception as e:
    print(f"Error testing graph API: {e}")
