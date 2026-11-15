#!/usr/bin/env python3
"""Fetch Amazon product titles for every ASIN still linked in the catalog (cached, resumable).
Amazon titles tell us exactly which product a link points to. Cache: .cache/amazon_titles.json"""
import html, json, os, re, subprocess, sys, time
ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, ".cache", "amazon_titles.json")
catalog = json.load(open(os.path.join(ROOT, "..", "site", "data", "products.json")))
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
import csv
links = {r["asin"]: int(r["links"]) for r in csv.DictReader(open(os.path.join(ROOT, "..", "amazon_inventory.csv")))}
todo = []
# most-linked products first, so matching can start on the highest-impact items
def weight(p):
    return -sum(links.get(a, 0) for a in p.get("asins", []))
for pid, p in sorted(catalog.items(), key=lambda kv: weight(kv[1])):
    if "amazon.com" in p["url"]:
        m = re.search(r"/dp/([A-Z0-9]{10})", p["url"])
        order = ([m.group(1)] if m else []) + [a for a in p.get("asins", []) if not m or a != m.group(1)]
        todo += [a for a in order[:2] if a not in cache]
print(len(todo), "titles to fetch", flush=True)
for i, asin in enumerate(todo):
    out = subprocess.run(["curl", "-s", "-L", "--compressed", "--max-time", "25", "-A", UA, "-H", "Accept-Language: en-US,en;q=0.9",
                          f"https://www.amazon.com/dp/{asin}"], capture_output=True).stdout.decode("utf-8", errors="replace")
    m = re.search(r"<title>([^<]{3,300})", out)
    t = html.unescape(m.group(1)).strip() if m else None
    if t and ("Robot Check" in t or t.startswith("Amazon.com Page Not Found") or t == "Amazon.com"):
        t = None
    cache[asin] = t
    if i % 10 == 0:
        json.dump(cache, open(CACHE, "w"), indent=0)
        print(i, "/", len(todo), "ok so far:", sum(1 for v in cache.values() if v), flush=True)
    time.sleep(1.3)
json.dump(cache, open(CACHE, "w"), indent=0)
print("done:", sum(1 for v in cache.values() if v), "titles,", sum(1 for v in cache.values() if not v), "unavailable")
