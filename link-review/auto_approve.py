#!/usr/bin/env python3
"""Standing rule from the owner: auto-approve a proposed match when confidence is "high" AND the page loads
(primary.verified is true and not broken). Anything else stays for manual review.
Never touches an item the owner already decided. Writes decisions.json (merge) with auto: true.
Usage: python3 auto_approve.py"""
import glob, json, os
ROOT = os.path.dirname(os.path.abspath(__file__))
def run():
    path = os.path.join(ROOT, "decisions.json")
    dec = json.load(open(path)) if os.path.exists(path) else {}
    added = left = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "batches", "batch-*.json"))):
        try:
            items = json.load(open(f))
        except Exception:      # a batch file may be mid-write
            continue
        for it in items:
            if it.get("status") != "match" or it["id"] in dec:
                continue
            p = it["primary"]
            if it.get("confidence") == "high" and p.get("verified") and not p.get("broken"):
                dec[it["id"]] = {"status": "approved", "choice": 0, "auto": True, "chosen": p}
                added += 1
            else:
                left += 1
    if added:
        json.dump(dec, open(path, "w"), indent=1)
    return added, left


if __name__ == "__main__":
    added, left = run()
    print(f"auto-approved {added} new items; {left} undecided items left for manual review")
