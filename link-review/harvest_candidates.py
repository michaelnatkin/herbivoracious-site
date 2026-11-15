#!/usr/bin/env python3
"""Step 1 of the two-step matcher: collect candidate product pages from in-network merchants' own catalogs.

For each product in the given input batch(es), derive a few search terms, query every searchable merchant
(Shopify-style stores) politely (one request per host every few seconds, backoff on 429), and save the top
hits with their merchant's EPC to .cache/candidates/<input-name>.json. A later step (an agent) picks the best
candidate per product; it needs no web search.

Usage: python3 harvest_candidates.py batches/input-06.json [more inputs...]   (resumable: skips products already done)
"""
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, ".cache", "candidates")
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
MERCH = json.load(open(os.path.join(ROOT, ".cache", "skim_merchants.json")))
# Searchable (Shopify-style) in-network merchants, best earners first; failures disable a host for the run.
HOSTS = ["nuts.com", "savoryspiceshop.com", "thespicehouse.com", "chefshop.com"]
MIN_GAP = 8.0
cool = {}   # host -> time until which we leave it alone after a 429
last, locks, dead = {}, {h: threading.Lock() for h in HOSTS}, {}


def epc(host):
    for m in MERCH:
        if "United States" in m["countries"] and any((d or "").removeprefix("www.") == host for d in m["domains"]):
            return m["epc"], m["name"]
    return None, host


def terms_for(p):
    """A few short search terms from the product's name and anchor text."""
    if p.get("search_terms"):
        return p["search_terms"]
    out = []
    def add(t):
        t = re.sub(r"\(.*?\)|[,;:].*$|\b\d+(\.\d+)?\s*(oz|lb|ounce|pound|inch|in|qt|quart|cup|g|ml|fl)\b\.?", " ", t.lower())
        t = re.sub(r"[^a-z0-9' -]", " ", t)
        t = " ".join(w for w in t.split() if w not in {"the", "a", "an", "and", "of", "for", "with", "my", "this", "that"})
        t = " ".join(t.split()[:4])
        if len(t) >= 3 and t not in out:
            out.append(t)
    for a in p.get("anchors", [])[:2]: add(a)
    add(p["name"])
    return out[:2]


def fetch(host, url):
    with locks[host]:
        if time.time() < cool.get(host, 0):
            return "", "cooling"
        wait = MIN_GAP - (time.time() - last.get(host, 0))
        if wait > 0: time.sleep(wait)
        last[host] = time.time()
        r = subprocess.run(["curl", "-s", "-L", "--compressed", "--max-time", "25", "-A", UA, "-w", "\n%{http_code}", url], capture_output=True)
        body, _, code = r.stdout.decode("utf-8", "replace").rpartition("\n")
        if code.strip() == "429":
            cool[host] = time.time() + 300   # rest this store for 5 minutes
            print(f"  429 from {host}; resting it for 5 min", flush=True)
        return body, code.strip()


def search(host, term):
    if dead.get(host, 0) >= 3: return []
    q = urllib.parse.urlencode({"q": term, "resources[type]": "product", "resources[limit]": "4"})
    for h in (f"www.{host}",):
        body, code = fetch(host, f"https://{h}/search/suggest.json?{q}")
        if code in ("cooling", "429"):
            return None
        try:
            prods = json.loads(body)["resources"]["results"]["products"]
            dead[host] = 0
            return [{"title": x["title"][:90], "price": x.get("price"), "url": f"https://{h}{x['url'].split('?')[0]}"} for x in prods]
        except Exception:
            continue
    dead[host] = dead.get(host, 0) + 1
    return []


def do_product(p):
    hits = {}
    skipped = []
    for ti, term in enumerate(terms_for(p)):
        if ti and sum(len(v["results"]) for v in hits.values()) >= 2:
            break   # the first term already found candidates
        for host in HOSTS:
            e, name = epc(host)
            res = search(host, term)
            if res is None:
                skipped.append(host); continue
            for r in res:
                hits.setdefault(host, {"merchant": name, "epc": e, "results": []})["results"].append({**r, "term": term})
    for v in hits.values():  # de-dup by url
        seen, keep = set(), []
        for r in v["results"]:
            if r["url"] not in seen: seen.add(r["url"]); keep.append(r)
        v["results"] = keep[:5]
    return {"id": p["id"], "terms": terms_for(p), "skipped_hosts": sorted(set(skipped)),
            "candidates": sorted(hits.values(), key=lambda v: -(v["epc"] or 0))}


if __name__ == "__main__":
    for path in sys.argv[1:]:
        products = json.load(open(path))
        out_path = os.path.join(OUT, os.path.basename(path))
        done = {c["id"]: c for c in json.load(open(out_path))} if os.path.exists(out_path) else {}
        todo = [p for p in products if p["id"] not in done]
        print(f"{os.path.basename(path)}: {len(todo)} to do", flush=True)
        # products are processed in parallel; per-host locks keep each merchant at one polite request at a time
        with cf.ThreadPoolExecutor(max_workers=4) as ex:
            for i, res in enumerate(ex.map(do_product, todo)):
                done[res["id"]] = res
                if i % 3 == 0:
                    json.dump(list(done.values()), open(out_path, "w"), indent=1)
                    print(f"  {len(done)}/{len(products)}  dead hosts: {[h for h, n in dead.items() if n >= 3]}", flush=True)
        json.dump(list(done.values()), open(out_path, "w"), indent=1)
    print("done")
