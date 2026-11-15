#!/usr/bin/env python3
"""Build input-W01.json... (20 each) from products that the harvest/pick pass flagged needs_web:true.
Books first (they only need one Barnes & Noble lookup), then everything else, most-linked first."""
import glob, json, os, re
ROOT = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(ROOT, "batches")
catalog = json.load(open(os.path.join(ROOT, "..", "site", "data", "products.json")))
inputs = {}
for f in glob.glob(os.path.join(B, "input-H*.json")) + glob.glob(os.path.join(B, "input-R*.json")):
    for it in json.load(open(f)): inputs[it["id"]] = it
done = set()
for f in glob.glob(os.path.join(B, "input-W*.json")): done |= {i["id"] for i in json.load(open(f))}
matched = set()
for f in glob.glob(os.path.join(B, "batch-*.json")):
    matched |= {i["id"] for i in json.load(open(f)) if i["status"] == "match"}
rows = []
for f in glob.glob(os.path.join(B, "batch-H*.json")):
    for i in json.load(open(f)):
        if i["status"] != "match" and i.get("needs_web") and i["id"] not in done and i["id"] not in matched \
           and "amazon.com" in catalog.get(i["id"], {}).get("url", "") and i["id"] in inputs:
            rows.append(inputs[i["id"]])
rows.sort(key=lambda r: (not r["is_book"], -r["links"]))
start = len(glob.glob(os.path.join(B, "input-W*.json"))) + 1
for k in range(0, len(rows), 20):
    json.dump(rows[k:k + 20], open(os.path.join(B, f"input-W{start + k // 20:02d}.json"), "w"), indent=1)
print(f"{len(rows)} products ({sum(r['is_book'] for r in rows)} books) -> {-(-len(rows)//20)} web inputs from W{start:02d}")
