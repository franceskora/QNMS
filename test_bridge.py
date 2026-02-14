import requests
import time

# 1. Configuration - MUST MATCH YOUR isaac_bridge.py
BREV_IP = "13.220.232.5"  # <--- Double check this IP!
PORT = 5000
BASE_URL = f"http://{BREV_IP}:{PORT}"

def run_diagnostics():
    print(f"🚀 STARTING QNMS NETWORK DIAGNOSTIC...")
    print(f"📡 TARGET: {BASE_URL}")
    print("-" * 40)

    # TEST 1: Ping Telemetry (GET)
    try:
        print("🔍 TEST 1: Pinging Telemetry...")
        t1 = time.time()
        resp = requests.get(f"{BASE_URL}/telemetry", timeout=5)
        t2 = time.time()
        print(f"✅ SUCCESS: Received status {resp.status_code} in {t2-t1:.2f}s")
        print(f"📊 DATA: {resp.json()}")
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {str(e)}")

    print("-" * 40)

    # TEST 2: Send Repair Command (POST)
    try:
        print("🔍 TEST 2: Sending Repair Command (This takes ~4-8 seconds)...")
        payload = {"command": "deploy_nano_agent", "params": {"target": "Stage_0"}}
        t1 = time.time()
        resp = requests.post(f"{BASE_URL}/command", json=payload, timeout=15)
        t2 = time.time()
        print(f"✅ SUCCESS: Received status {resp.status_code} in {t2-t1:.2f}s")
        print(f"🤖 RESPONSE: {resp.json()}")
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {str(e)}")

if __name__ == "__main__":
    run_diagnostics()