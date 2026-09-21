import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from coordinator.mule_network_manager import GLOBAL_MULE_NETWORKS
from coordinator.adsl_service import get_recent_adsl_transactions

print("Networks in memory:", len(GLOBAL_MULE_NETWORKS.networks))
txns = get_recent_adsl_transactions(limit=5)
print(f"Recent txns count: {len(txns)}")
if txns:
    sample_id = txns[0]["transaction_id"]
    print(f"Testing sample tx: {sample_id}")
    graph_res = GLOBAL_MULE_NETWORKS.get_subgraph_for_transaction(sample_id)
    print(f"Graph nodes: {len(graph_res.get('nodes', []))}, edges: {len(graph_res.get('edges', []))}")
    if graph_res.get('nodes'):
        print("First 3 nodes:", graph_res['nodes'][:3])
else:
    print("No transactions found in coordinator memory!")
