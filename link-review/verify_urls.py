#!/usr/bin/env python3
"""Second-pass URL check for batches. Re-tests every replacement URL that is not yet verified, slowly
(per-host throttle, retries on 429) and updates the batch files in place:
  200            -> verified: true
  404 / 410      -> broken: true (and a broken primary is swapped with the first working alternative)
  403 / other    -> left unverified (the merchant's bot protection blocks automated checks)
Usage: python3 verify_urls.py [batch-NN.json ...]   (default: all batches)"""
import glob, json, os, subprocess, sys, time
from urllib.parse import urlparse
ROOT = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
last = {}

def check(url):
    host = urlparse(url).hostname
    for attempt in range(3):
        wait = 3.0 - (time.time() - last.get(host, 0))
        if wait > 0: time.sleep(wait)
        last[host] = time.time()
        code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "--compressed", "--max-time", "25", "-w", "%{http_code}",
                               "-A", UA, "-H", "Accept-Language: en-US,en;q=0.9", url], capture_output=True, text=True).stdout.strip()
        if code != "429": return code
        time.sleep(15 * (attempt + 1))
    return "429"

files = [os.path.join(ROOT, "batches", f) for f in sys.argv[1:]] or sorted(glob.glob(os.path.join(ROOT, "batches", "batch-*.json")))
tally = {}
for path in files:
    items = json.load(open(path)); changed = False
    for it in items:
        if it.get("status") != "match": continue
        for m in [it["primary"]] + it.get("alternatives", []):
            if m.get("verified") or m.get("broken"): continue
            code = check(m["url"]); tally[code] = tally.get(code, 0) + 1
            if code == "200": m["verified"] = True; changed = True
            elif code in ("404", "410"): m["broken"] = True; m["verified"] = False; changed = True
        if it["primary"].get("broken"):
            ok = [a for a in it.get("alternatives", []) if not a.get("broken")]
            if ok:
                bad = it["primary"]; it["primary"] = ok[0]
                it["alternatives"] = [bad] + [a for a in it["alternatives"] if a is not ok[0]]
                it["note"] = (it.get("note", "") + " (Original first choice returned 404, so the alternative was promoted.)").strip()
                changed = True
    if changed: json.dump(items, open(path, "w"), indent=1)
    print(os.path.basename(path), "checked", flush=True)
print("status codes:", tally)
