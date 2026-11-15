#!/usr/bin/env python3
"""Search the cached Skimlinks merchant list (US merchants only), best EPC first.

  python3 merchants.py search "sur la table"     # by name or domain substring
  python3 merchants.py domain surlatable.com     # exact domain lookup
  python3 merchants.py top "Kitchenware" 20      # top merchants in a vertical

The cache (.cache/skim_merchants.json) comes from the Skimlinks Merchant API (see project notes);
EPC = average earnings per click, the number we rank by.
"""
import json, os, sys
M = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "skim_merchants.json")))
US = [m for m in M if "United States" in m["countries"]]

def show(ms, n=15):
    for m in sorted(ms, key=lambda m: -(m["epc"] or 0))[:n]:
        print(f'{m["name"][:38]:38} EPC={m["epc"] if m["epc"] is not None else "n/a":<5} rate={m["rate"]}%  {", ".join(d for d in m["domains"][:3] if d)}')
    if not ms: print("(no match)")

cmd, arg = sys.argv[1], sys.argv[2].lower()
if cmd == "search":
    show([m for m in US if arg in m["name"].lower() or any(arg.replace(" ", "") in (d or "") for d in m["domains"])])
elif cmd == "domain":
    show([m for m in US if any(arg == (d or "").removeprefix("www.") for d in m["domains"])])
elif cmd == "top":
    show([m for m in US if any(arg in v.lower() for v in m["verticals"])], int(sys.argv[3]) if len(sys.argv) > 3 else 15)
