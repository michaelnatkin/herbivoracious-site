#!/usr/bin/env python3
"""Merge 'ASIN|title' lines (read from a real browser on Amazon pages) into .cache/amazon_titles_browser.json; print the next ASINs to fetch."""
import html, json, os, sys
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "amazon_titles_browser.json")
cur = json.load(open(P)) if os.path.exists(P) else {}
for line in sys.stdin.read().splitlines():
    if "|" in line:
        a, t = line.split("|", 1); cur[a.strip()] = html.unescape(t.strip()) or None
    elif line.strip(): cur[line.strip()] = None
json.dump(cur, open(P, "w"), indent=0)
todo = [a for a in json.load(open(os.path.join(os.path.dirname(P), "amazon_rest.json"))) if a not in cur]
print(len(cur), "saved;", len(todo), "left"); print(json.dumps(todo[:12]))
