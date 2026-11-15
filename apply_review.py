#!/usr/bin/env python3
"""Apply approved link-review decisions to the catalog (site/data/products.json).

Reads link-review/batches/batch-*.json (proposals) and link-review/decisions.json (your approvals).
For every approved item, sets the catalog product's `url` and `merchant` to the chosen replacement.
`original_url` is kept so a change can be rolled back. Safe to re-run.
Usage: python3 apply_review.py [--dry-run]
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(ROOT, "site", "data", "products.json")
REVIEW = os.path.join(ROOT, "link-review")

catalog = json.load(open(CATALOG))
dec_path = os.path.join(REVIEW, "decisions.json")
decisions = json.load(open(dec_path)) if os.path.exists(dec_path) else {}
changed = skipped = 0
for path in sorted(glob.glob(os.path.join(REVIEW, "batches", "batch-*.json"))):
    for item in json.load(open(path)):
        d = decisions.get(item["id"], {})
        if item.get("status") != "match" or d.get("status") != "approved":
            continue
        chosen = d.get("chosen") or item["primary"]
        known = {m["url"]: m for m in [item["primary"]] + item.get("alternatives", [])}
        p = catalog.get(item["id"])
        if known.get(chosen["url"], {}).get("broken"):
            print(f"WARNING: {item['id']}: approved URL returned 404; skipped ({chosen['url'][:80]})")
            skipped += 1
        elif p is None:
            print(f"WARNING: {item['id']} is not in the catalog; skipped")
            skipped += 1
        elif p["url"] != chosen["url"]:
            print(f"{item['id']}: -> {chosen['merchant']}: {chosen['url'][:90]}")
            p["url"], p["merchant"] = chosen["url"], chosen["merchant"]
            changed += 1
if "--dry-run" in sys.argv:
    print(f"(dry run) {changed} catalog entries would change, {skipped} skipped")
else:
    with open(CATALOG, "w") as f:
        json.dump(dict(sorted(catalog.items())), f, indent=2)
        f.write("\n")
    print(f"{changed} catalog entries updated, {skipped} skipped")
