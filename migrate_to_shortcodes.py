#!/usr/bin/env python3
"""One-time migration: turn every Amazon link in the content into a {{< product >}} shortcode
and build the authoritative catalog (site/data/products.json, keyed by our own product id).

Usage:  python3 migrate_to_shortcodes.py          # dry run, prints a report
        python3 migrate_to_shortcodes.py --apply  # rewrite content and write the catalog
"""
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "site", "content")
DATA = os.path.join(ROOT, "site", "data")

ASIN_RES = [
    re.compile(r"/(?:dp|gp/product|o/ASIN|exec/obidos/ASIN)/([A-Z0-9]{10})"),
    re.compile(r"[?&]ASIN=([A-Z0-9]{10})"),
]
HTML_LINK = re.compile(
    r'<a\b([^>]*?)href=(["\'])(https?://(?:www\.)?amazon\.com[^"\']*)\2([^>]*)>(.*?)</a>', re.S | re.I)
MD_LINK = re.compile(r"\[([^\]\n]+)\]\((https?://(?:www\.)?amazon\.com[^)\s]*)\)")
# Hand-picked ids for key products (keyed by canonical ASIN)
ID_OVERRIDES = {"1558327452": "herbivoracious-cookbook"}
GENERIC = {"buy it", "on amazon", "like this", "basic", "this one", "here", "amazon", "check it out",
           "get it", "get one", "order", "order it", "these", "this", "that", "it", "one", "some", "them", "link"}


def asin_of(url):
    for rx in ASIN_RES:
        m = rx.search(url)
        if m:
            return m.group(1)
    return None


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def slugify(s):
    s = re.sub(r"&[a-z]+;|&#\d+;", " ", s.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > 48:  # cut at a word boundary
        s = s[:48].rsplit("-", 1)[0]
    return s


def split_front_matter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            end = text.find("\n", end + 1)
            return text[: end + 1], text[end + 1:]
    return "", text


def canonical(dedup, a):
    seen = set()
    while dedup.get(a, a) != a and a not in seen:  # follow chains to the end
        seen.add(a)
        a = dedup[a]
    return a


def load(name):
    p = os.path.join(DATA, name)
    return json.load(open(p)) if os.path.exists(p) else {}


def main(apply):
    old = load("products.json")
    dedup, cats = load("product-dedup.json"), load("product-categories.json")

    # existing shop products by ASIN
    shop = {}
    for c in old.get("categories", []):
        for p in c["products"]:
            a = asin_of(p["url"])
            if a:
                shop[a] = {**p, "category": c["slug"]}

    # pass 1: scan content
    files = sorted(glob.glob(os.path.join(CONTENT, "**", "*.md"), recursive=True))
    files = [f for f in files if "/content/shop/" not in f]
    anchors = collections.defaultdict(collections.Counter)
    seen_asins = collections.Counter()
    skipped = []
    for f in files:
        _, body = split_front_matter(open(f).read())
        for m in HTML_LINK.finditer(body):
            a = asin_of(m.group(3))
            if a:
                seen_asins[a] += 1
                anchors[a][strip_tags(m.group(5))] += 1
            else:
                skipped.append((f, m.group(3)))
        for m in MD_LINK.finditer(body):
            a = asin_of(m.group(2))
            if a:
                seen_asins[a] += 1
                anchors[a][strip_tags(m.group(1))] += 1
            else:
                skipped.append((f, m.group(2)))

    # group ASINs into products via the existing dedup map
    groups = collections.defaultdict(list)
    for a in seen_asins:
        groups[canonical(dedup, a)].append(a)

    def best_anchor(asins):
        c = collections.Counter()
        for a in asins:
            c.update(anchors[a])
        for text, _ in c.most_common():
            if text and text.lower() not in GENERIC and len(text) >= 4:
                return text
        return None

    catalog, by_asin, used_ids = {}, {}, set()
    for canon, asins in sorted(groups.items()):
        asins = sorted(asins)
        shop_entry = next((shop[a] for a in [canon] + asins if a in shop), None)
        name = shop_entry["name"] if shop_entry else best_anchor(asins)
        base = slugify(name) if name else ""
        pid = ID_OVERRIDES.get(canon) or (base if len(base) >= 4 else f"amazon-{canon.lower()}")
        n = 2
        while pid in used_ids:
            pid = f"{base or 'amazon-' + canon.lower()}-{n}"
            n += 1
        used_ids.add(pid)
        entry = {"name": name or f"Amazon item {canon}"}
        cat = shop_entry["category"] if shop_entry else None
        if cat:
            entry["category"] = cat
        entry["url"] = shop_entry["url"] if shop_entry else f"https://www.amazon.com/dp/{canon}?tag=herb-hugo-20"
        entry["original_url"] = entry["url"]
        entry["asins"] = asins
        if shop_entry and shop_entry.get("review_url"):
            entry["review_url"] = shop_entry["review_url"]
        catalog[pid] = entry
        for a in asins:
            by_asin[a] = pid

    # pass 2: rewrite content
    changed, count = 0, 0

    def tag(pid, target):
        return '{{%% product id="%s"%s %%}}' % (pid, ' target="%s"' % target if target else "")

    for f in files:
        text = open(f).read()
        fm, body = split_front_matter(text)

        def html_sub(m):
            nonlocal count
            a = asin_of(m.group(3))
            if not a:
                return m.group(0)
            attrs = m.group(1) + " " + m.group(4)
            t = re.search(r'target=["\']([^"\']+)["\']', attrs)
            count += 1
            return tag(by_asin[a], t.group(1) if t else None) + m.group(5) + "{{% /product %}}"

        def md_sub(m):
            nonlocal count
            a = asin_of(m.group(2))
            if not a:
                return m.group(0)
            count += 1
            return tag(by_asin[a], None) + m.group(1) + "{{% /product %}}"

        new = MD_LINK.sub(md_sub, HTML_LINK.sub(html_sub, body))
        if new != body:
            changed += 1
            if apply:
                open(f, "w").write(fm + new)

    print(f"files scanned: {len(files)} | files changed: {changed} | links converted: {count}")
    print(f"distinct ASINs: {len(seen_asins)} -> products: {len(catalog)} "
          f"(shop-visible: {sum('category' in e for e in catalog.values())})")
    print(f"skipped (no ASIN): {len(skipped)}")
    for f, u in skipped:
        print("   ", os.path.relpath(f, ROOT), u[:90])
    if apply:
        json.dump(dict(sorted(catalog.items())), open(os.path.join(DATA, "products.json"), "w"), indent=2)
        open(os.path.join(DATA, "products.json"), "a").write("\n")
        print("wrote site/data/products.json")


if __name__ == "__main__":
    main("--apply" in sys.argv)
