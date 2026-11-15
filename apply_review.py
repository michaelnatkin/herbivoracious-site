#!/usr/bin/env python3
"""Apply approved link-review decisions to the catalog (site/data/products.json).

Reads link-review/approved.json (entries with user_status == "approved"), finds every catalog
product whose `asins` contains one of the entry's Amazon ids, and points it at the chosen merchant URL.
`original_url` is kept so a change can be rolled back.  Usage: python3 apply_review.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(ROOT, "site", "data", "products.json")
APPROVED = os.path.join(ROOT, "link-review", "approved.json")

catalog = json.load(open(CATALOG))
by_asin = {a: pid for pid, p in catalog.items() for a in p.get("asins", [])}
changed = 0
for e in json.load(open(APPROVED)):
    if e.get("user_status") != "approved":
        print(f"skip #{e['id']} (status: {e.get('user_status')})")
        continue
    pids = sorted({by_asin[a] for a in e["asins"] if a in by_asin})
    missing = [a for a in e["asins"] if a not in by_asin]
    if missing:
        sys.exit(f"ERROR: #{e['id']}: Amazon ids not in catalog: {missing}")
    for pid in pids:
        p = catalog[pid]
        if p["url"] != e["url"]:
            print(f"#{e['id']} {pid}: {p['url'][:60]} -> {e['merchant']}: {e['url'][:70]}")
            p["url"], p["merchant"] = e["url"], e["merchant"]
            changed += 1
if "--dry-run" in sys.argv:
    print(f"(dry run) {changed} catalog entries would change")
else:
    json.dump(dict(sorted(catalog.items())), open(CATALOG, "w"), indent=2)
    open(CATALOG, "a").write("\n")
    print(f"{changed} catalog entries updated")
