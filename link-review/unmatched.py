#!/usr/bin/env python3
"""Build harvest inputs (batches/input-H01.json, ...) for every Amazon-linked product that has no accepted match yet:
products whose batch result was no_match, plus products from input batches that have no result file yet
(except inputs whose agent is still running: pass --skip-input NN). 20 per file, most-linked first."""
import glob, json, os, re, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(ROOT, "batches")
skip = {sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--skip-input"}
catalog = json.load(open(os.path.join(ROOT, "..", "site", "data", "products.json")))
matched = set()
for f in glob.glob(os.path.join(B, "batch-*.json")):
    matched |= {i["id"] for i in json.load(open(f)) if i["status"] == "match"}
for f in glob.glob(os.path.join(B, "input-H*.json")):   # already queued for harvest
    matched |= {i["id"] for i in json.load(open(f))}
rows = {}
for f in sorted(glob.glob(os.path.join(B, "input-[0-9]*.json"))):
    nn = re.search(r"input-(\d+)", f).group(1)
    if nn in skip:
        continue
    for it in json.load(open(f)):
        if it["id"] not in matched and "amazon.com" in catalog.get(it["id"], {}).get("url", "") and it["id"] not in rows:
            rows[it["id"]] = it
rows = sorted(rows.values(), key=lambda r: -r["links"])
start = len(glob.glob(os.path.join(B, "input-H*.json"))) + 1
for i in range(0, len(rows), 20):
    json.dump(rows[i:i + 20], open(os.path.join(B, f"input-H{start + i // 20:02d}.json"), "w"), indent=1)
print(f"{len(rows)} products -> {-(-len(rows)//20)} harvest inputs (H{start:02d}...); links covered: {sum(r['links'] for r in rows)}")
