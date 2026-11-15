#!/usr/bin/env python3
"""Build input batches for the matching agents: link-review/batches/input-NN.json (20 products each),
most-linked first, only products still linked to Amazon and not already queued.
Usage: python3 make_worklist.py [--size 20] [--only-ready]   (ready = Amazon titles fetched)"""
import csv, glob, json, os, re, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
size = int(sys.argv[sys.argv.index("--size") + 1]) if "--size" in sys.argv else 20
catalog = json.load(open(os.path.join(ROOT, "..", "site", "data", "products.json")))
titles = json.load(open(os.path.join(ROOT, ".cache", "amazon_titles.json"))) if os.path.exists(os.path.join(ROOT, ".cache", "amazon_titles.json")) else {}
inv = {r["asin"]: r for r in csv.DictReader(open(os.path.join(ROOT, "..", "amazon_inventory.csv")))}
queued = set()
for f in glob.glob(os.path.join(ROOT, "batches", "input-*.json")):
    queued |= {i["id"] for i in json.load(open(f))}
rows = []
for pid, p in catalog.items():
    if "amazon.com" not in p["url"] or pid in queued:
        continue
    asins = p.get("asins", [])
    cur = re.search(r"/dp/([A-Z0-9]{10})", p["url"])
    first = ([cur.group(1)] if cur else []) + [a for a in asins if not cur or a != cur.group(1)]
    attempted = all(a in titles for a in first[:2])
    if "--only-ready" in sys.argv and not attempted:
        continue
    rs = [inv[a] for a in asins if a in inv]
    anchors = sorted({x.strip() for r in rs for x in r["all_anchors"].split(";") if x.strip()})[:6]
    rows.append({
        "id": pid, "name": p["name"], "current_amazon_url": p["url"],
        "is_book": any(re.fullmatch(r"\d{9}[\dX]", a) for a in asins),
        "amazon_titles": [titles[a] for a in first[:2] if titles.get(a)],
        "anchors": anchors, "asins": asins,
        "links": sum(int(r["links"]) for r in rs), "posts": sum(int(r["posts"]) for r in rs),
        "example_post": rs[0]["example_post"].replace("site/content/posts/", "").replace("site/content/", "").replace(".md", "") if rs else "",
    })
rows.sort(key=lambda r: -r["links"])
start = len(glob.glob(os.path.join(ROOT, "batches", "input-*.json"))) + 1
for i in range(0, len(rows), size):
    n = start + i // size
    json.dump(rows[i:i + size], open(os.path.join(ROOT, "batches", f"input-{n:02d}.json"), "w"), indent=1)
print(f"{len(rows)} products -> {-(-len(rows)//size)} new input batches (starting at {start:02d}); links covered: {sum(r['links'] for r in rows)}")
