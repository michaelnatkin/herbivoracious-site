#!/usr/bin/env python3
"""Record products found by browsing merchants' own search pages, then build batches/batch-C01.json.
  python3 chrome_pick.py add <id> <kind> <confidence> "<merchant>" "<product>" "<url>" <epc|-> <rate|-> "<price|->" "<note>"
  python3 chrome_pick.py nomatch <id> "<reason>"
  python3 chrome_pick.py build
URLs come from a real browser's search results (the page is linked from the merchant's own site), so verified=true."""
import glob, json, os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, ".cache", "chrome_picks.jsonl")
MERCH = {"Sur La Table": (0.06, 9), "iHerb.com": (0.13, 15), "Weee!": (None, None), "ChefShop.com": (None, 7)}

def num(x): return None if x in ("-", "", None) else float(x)

if sys.argv[1] == "add":
    _, _, id_, kind, conf, merchant, product, url, epc, rate, price, note = sys.argv
    e, r = MERCH.get(merchant, (None, None))
    rec = {"id": id_, "kind": kind, "confidence": conf, "primary": {"merchant": merchant, "product": product, "url": url,
           "epc": num(epc) if num(epc) is not None else e, "rate": num(rate) if num(rate) is not None else r,
           "price": None if price == "-" else price, "verified": True, "verified_by": "browser search page"}, "note": note}
    open(LOG, "a").write(json.dumps(rec) + "\n")
elif sys.argv[1] == "nomatch":
    open(LOG, "a").write(json.dumps({"id": sys.argv[2], "no_match": True, "reason": sys.argv[3]}) + "\n")
elif sys.argv[1] == "build":
    inputs = {}
    for f in glob.glob(os.path.join(ROOT, "batches", "input-*.json")):
        for it in json.load(open(f)): inputs.setdefault(it["id"], it)
    recs = {}
    for line in open(LOG):
        r = json.loads(line); recs[r["id"]] = r          # later entries win
    out = []
    for id_, r in recs.items():
        src = inputs.get(id_, {"name": id_, "anchors": [], "asins": [], "links": 0, "posts": 0, "amazon_titles": [], "example_post": ""})
        amazon = {"asins": src["asins"], "title": (src["amazon_titles"] or [src["name"]])[0], "anchors": src["anchors"],
                  "links": src["links"], "posts": src["posts"], "example_post": src["example_post"]}
        if r.get("no_match"):
            out.append({"id": id_, "name": src["name"], "status": "no_match", "reason": r["reason"], "needs_web": False, "amazon": amazon})
        else:
            out.append({"id": id_, "name": src["name"], "status": "match", "kind": r["kind"], "confidence": r["confidence"], "amazon": amazon,
                        "primary": r["primary"], "alternatives": [], "note": r["note"]})
    json.dump(out, open(os.path.join(ROOT, "batches", "batch-C01.json"), "w"), indent=1)
    print(len(out), "items in batch-C01.json;", sum(o["status"] == "match" for o in out), "matches")
