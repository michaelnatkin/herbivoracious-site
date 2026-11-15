#!/usr/bin/env python3
"""Search a merchant's own product catalog and print real product URLs (no guessing).
Works for Shopify stores (most small food/kitchen brands: Savory Spice, The Spice House, ChefShop, Masienda, Lodge,
Burlap & Barrel, Runamok...). Usage: python3 shop_search.py <domain> "<search terms>"   e.g.  shop_search.py savoryspiceshop.com "smoked paprika"
Prints: title | price | url   (these are real product pages; still mark verified only if a plain GET returns 200)."""
import json, subprocess, sys, urllib.parse
domain, term = sys.argv[1].removeprefix("www."), sys.argv[2]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
def get(url):
    return subprocess.run(["curl", "-s", "-L", "--compressed", "--max-time", "25", "-A", UA, "-w", "\n%{http_code}", url], capture_output=True).stdout.decode("utf-8", "replace")
for host in (f"www.{domain}", domain):
    q = urllib.parse.urlencode({"q": term, "resources[type]": "product", "resources[limit]": "6"})
    out = get(f"https://{host}/search/suggest.json?{q}")
    body, _, code = out.rpartition("\n")
    try:
        prods = json.loads(body)["resources"]["results"]["products"]
    except Exception:
        prods = []
    if prods:
        for p in prods:
            print(f'{p["title"][:70]} | {p.get("price", "?")} | https://{host}{p["url"].split("?")[0]}')
        break
else:
    print(f"(no results or not a Shopify store: last HTTP {code.strip()}; fall back to WebSearch)")
