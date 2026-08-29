#!/usr/bin/env python3
"""
Quickly tests Alpaca Paper API Keys against the official Alpaca Paper REST API.
"""

import os
import sys
import httpx
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))
from app.config import settings

def test_keys():
    print("============================================================")
    print("ALPACA PAPER API KEY VERIFICATION UTILITY")
    print("============================================================")
    
    key = settings.ALPACA_API_KEY
    secret = settings.ALPACA_SECRET_KEY
    base_url = settings.ALPACA_BASE_URL
    is_paper = settings.ALPACA_PAPER
    
    print(f"Base URL:      {base_url}")
    print(f"Paper Mode:    {is_paper}")
    print(f"API Key:       {key[:4]}...{key[-4:] if len(key) > 8 else ''}")
    
    if not key or "DUMMY" in key:
        print("\n[INFO] Running in LOCAL PAPER SIMULATION MODE (Dummy Key detected).")
        print("To connect real Alpaca Paper trading, set ALPACA_API_KEY in apps/api/.env")
        return

    headers = {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
        "Content-Type": "application/json",
    }
    
    try:
        with httpx.Client() as client:
            resp = client.get(f"{base_url}/v2/account", headers=headers, timeout=10.0)
            if resp.status_code == 200:
                acc = resp.json()
                print("\n[SUCCESS] REAL ALPACA PAPER ACCOUNT CONNECTED!")
                print(f"  Account ID:         {acc.get('id')}")
                print(f"  Status:             {acc.get('status')}")
                print(f"  Cash:               ${float(acc.get('cash', 0)):,.2f}")
                print(f"  Equity:             ${float(acc.get('equity', 0)):,.2f}")
                print(f"  Buying Power:       ${float(acc.get('buying_power', 0)):,.2f}")
                print(f"  Options Level:      {acc.get('options_approved_level')}")
            else:
                print(f"\n[ERROR] Alpaca API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"\n[ERROR] Failed to reach Alpaca API: {e}")

if __name__ == "__main__":
    test_keys()
