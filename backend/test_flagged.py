import requests

try:
    r = requests.get("http://127.0.0.1:8001/api/risk/flagged-accounts?limit=10", timeout=3)
    data = r.json()
    print("Flagged accounts status:", r.status_code)
    print("Count:", data.get("count"))
    print("Accounts length:", len(data.get("accounts", [])))
    if data.get("accounts"):
        print("First flagged account:", data["accounts"][0])
except Exception as e:
    print(f"Error querying flagged accounts: {e}")
