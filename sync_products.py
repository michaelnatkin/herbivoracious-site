#!/usr/bin/env python3
"""Publish step for product links. Runs from the pre-commit hook (and by hand).

The catalog (site/data/products.json) is the single source of truth: each product has our own id,
a name, a category, and its current URL. Posts reference products with a shortcode:

    {{% product id="maldon-sea-salt" %}}Maldon salt{{% /product %}}

To change where a product links, edit its "url" in the catalog. Nothing in the posts changes.

This script:
  1. Converts raw affiliate links in content into product shortcodes, creating catalog entries for
     new products (Amazon links, and links to merchants listed in merchant_domains.txt
     or already present in the catalog).
  2. Categorizes new products with Claude (needs ANTHROPIC_API_KEY; otherwise left uncategorized).
  3. Fails if any shortcode refers to a product id that is not in the catalog.
"""
import glob
import json
import os
import re
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "site", "content")
CATALOG = os.path.join(ROOT, "site", "data", "products.json")
EXTRA_DOMAINS = os.path.join(ROOT, "merchant_domains.txt")
AMAZON_TAG = "herb-hugo-20"

ASIN_RES = [
    re.compile(r"/(?:dp|gp/product|o/ASIN|exec/obidos/ASIN)/([A-Z0-9]{10})"),
    re.compile(r"[?&]ASIN=([A-Z0-9]{10})"),
]
HTML_LINK = re.compile(r'<a\b([^>]*?)href=(["\'])(https?://[^"\']+)\2([^>]*)>(.*?)</a>', re.S | re.I)
MD_LINK = re.compile(r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)")
SHORTCODE_ID = re.compile(r'\{\{[<%]\s*product\s+id="([^"]+)"')
GENERIC = {"buy it", "on amazon", "like this", "basic", "this one", "here", "amazon", "check it out",
           "get it", "get one", "order", "order it", "these", "this", "that", "it", "one", "some", "them", "link"}

CATEGORIES = {
    "knives-sharpening": "Knives & Sharpening",
    "cookware-appliances": "Cookware & Appliances",
    "bakeware-tools": "Bakeware & Tools",
    "kitchen-gadgets": "Kitchen Gadgets",
    "spices-seasonings": "Spices & Seasonings",
    "asian-pantry": "Asian Pantry",
    "mexican-latin-pantry": "Mexican & Latin Pantry",
    "middle-eastern-indian-pantry": "Middle Eastern & Indian Pantry",
    "cheese-dairy": "Cheese & Dairy",
    "condiments-sauces": "Condiments & Sauces",
    "oils-vinegars": "Oils & Vinegars",
    "grains-pasta-legumes": "Grains, Pasta & Legumes",
    "sweeteners-chocolate": "Sweeteners & Chocolate",
    "pantry-staples": "Pantry Staples",
    "books": "Books",
}

CATEGORY_ORDER = list(CATEGORIES.keys())



def categorize_with_llm(uncategorized_products):
    """Call Anthropic API to categorize products. Returns {product_id: category_slug}."""
    try:
        import anthropic
    except ImportError:
        print("  WARNING: anthropic package not installed, cannot categorize")
        return {}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  WARNING: ANTHROPIC_API_KEY not set, cannot categorize")
        return {}

    client = anthropic.Anthropic()

    # Build product list for the prompt
    id_list = list(uncategorized_products.keys())
    product_lines = []
    for i, asin in enumerate(id_list):
        product_lines.append(f"{i}: {uncategorized_products[pid]['name']}")

    slug_list = "\n".join(f"- {slug}: {CATEGORIES[slug]}" for slug in CATEGORY_ORDER)

    prompt = f"""Categorize each product into exactly one category. Products are from a vegetarian food blog's affiliate shop.

CATEGORIES (use the slug):
{slug_list}

PRODUCTS (index: name):
{chr(10).join(product_lines)}

Return a JSON object mapping product index (as string) to category slug. Example:
{{"0": "spices-seasonings", "1": "cookware-appliances", "2": "books"}}

Rules:
- Every product must be assigned exactly one category
- Knives, sharpening steels, knife holders -> knives-sharpening
- Pans, pots, Dutch ovens, blenders, food processors, stand mixers, juicers, dehydrators, smokers -> cookware-appliances
- Baking pans, tart pans, baking mats, pastry tools, cookie cutters, cake rings -> bakeware-tools
- Thermometers, scales, peelers, graters, spatulas, tongs, mandolines, mortars, spinners, shears -> kitchen-gadgets
- Gochujang, miso, soy sauce, kecap manis, tofu skin, kombu, nori, sesame paste, yuzu, dashi, rice -> asian-pantry
- Achiote, masa, dried Mexican chiles (guajillo, pasilla, ancho, chipotle, morita), Mexican oregano -> mexican-latin-pantry
- Tamarind, asafoetida, ras el hanout, za'atar, harissa, Aleppo pepper, sumac, pomegranate molasses, chana dal, fenugreek, amchoor -> middle-eastern-indian-pantry
- Cheeses (ricotta, gouda, chevre, pecorino), buttermilk powder -> cheese-dairy
- Hot sauce, mustard, jam, chutney, preserved lemons, pickles, sriracha -> condiments-sauces
- Olive oil, sesame oil, vinegar, balsamic, rosewater -> oils-vinegars
- Flour, pasta, noodles, lentils, polenta, farro, couscous, beans, panko, bread crumbs -> grains-pasta-legumes
- Sugar, maple syrup, jaggery, sorghum, chocolate, honey, molasses, espresso powder -> sweeteners-chocolate
- Salt, canned tomatoes, broth, dried mushrooms, agar agar, xanthan gum, tapioca maltodextrin, coconut cream, tea, freeze-dried fruit -> pantry-staples
- Cookbooks, food writing, recipe books -> books
- When in doubt about spices: if it's clearly associated with a specific cuisine (Asian, Mexican, Middle Eastern/Indian), put it there. Otherwise use spices-seasonings.

Return ONLY the JSON object, no other text."""

    print(f"  Calling Claude API to categorize {len(id_list)} products...")
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)

    assignments = json.loads(text)

    # Map back from index to ASIN
    result = {}
    for idx_str, slug in assignments.items():
        idx = int(idx_str)
        if idx < len(id_list):
            pid = id_list[idx]
            if slug in CATEGORIES:
                result[pid] = slug
            else:
                print(f"  WARNING: Unknown category '{slug}' for '{uncategorized_products[pid]['name']}', using pantry-staples")
                result[pid] = "pantry-staples"
    return result




def asin_of(url):
    for rx in ASIN_RES:
        m = rx.search(url)
        if m:
            return m.group(1)
    return None


def host_of(url):
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def slugify(s):
    s = re.sub(r"&[a-z]+;|&#\d+;", " ", s.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > 48:
        s = s[:48].rsplit("-", 1)[0]
    return s


def split_front_matter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            end = text.find("\n", end + 1)
            return text[: end + 1], text[end + 1:]
    return "", text


def main():
    with open(CATALOG) as f:
        catalog = json.load(f)
    by_asin = {a: pid for pid, p in catalog.items() for a in p.get("asins", [])}
    by_url = {p["url"].split("?")[0].lower(): pid for pid, p in catalog.items()}
    domains = {host_of(p["url"]) for p in catalog.values()} - {"amazon.com"}
    if os.path.exists(EXTRA_DOMAINS):
        domains |= {l.strip().lower() for l in open(EXTRA_DOMAINS) if l.strip() and not l.startswith("#")}

    new_products, edited, converted = {}, [], 0

    def product_for(url, anchor):
        """Find or create the catalog entry for a raw link. Returns (id, is_new) or None to skip."""
        asin = asin_of(url) if host_of(url) == "amazon.com" else None
        if asin:
            if asin in by_asin:
                return by_asin[asin]
            clean = f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
            entry = {"name": anchor or f"Amazon item {asin}", "url": clean, "original_url": clean, "asins": [asin]}
        elif host_of(url) in domains:
            key = url.split("?")[0].lower()
            if key in by_url:
                return by_url[key]
            entry = {"name": anchor or host_of(url), "url": url, "original_url": url}
        else:
            return None
        base = slugify(entry["name"]) if anchor and anchor.lower() not in GENERIC else ""
        pid = base if len(base) >= 4 else (f"amazon-{asin.lower()}" if asin else slugify(host_of(url)))
        n = 2
        while pid in catalog:
            pid = f"{base or pid.rsplit('-', 1)[0]}-{n}"
            n += 1
        catalog[pid] = entry
        new_products[pid] = entry
        if asin:
            by_asin[asin] = pid
        by_url[entry["url"].split("?")[0].lower()] = pid
        return pid

    def tag(pid, attrs):
        t = re.search(r'target=["\']([^"\']+)["\']', attrs)
        return '{{%% product id="%s"%s %%}}' % (pid, ' target="%s"' % t.group(1) if t else "")

    files = [f for f in sorted(glob.glob(os.path.join(CONTENT, "**", "*.md"), recursive=True)) if "/content/shop/" not in f]
    used = {}
    for f in files:
        text = open(f).read()
        fm, body = split_front_matter(text)

        def html_sub(m):
            nonlocal converted
            pid = product_for(m.group(3).replace("&amp;", "&"), strip_tags(m.group(5)))
            if not pid:
                return m.group(0)
            converted += 1
            return tag(pid, m.group(1) + " " + m.group(4)) + m.group(5) + "{{% /product %}}"

        def md_sub(m):
            nonlocal converted
            pid = product_for(m.group(2), strip_tags(m.group(1)))
            if not pid:
                return m.group(0)
            converted += 1
            return tag(pid, "") + m.group(1) + "{{% /product %}}"

        new_body = MD_LINK.sub(md_sub, HTML_LINK.sub(html_sub, body))
        if new_body != body:
            open(f, "w").write(fm + new_body)
            edited.append(os.path.relpath(f, ROOT))
        for pid in SHORTCODE_ID.findall(new_body):
            used.setdefault(pid, set()).add(os.path.relpath(f, ROOT))

    # categorize new products
    if new_products:
        uncat = {pid: p for pid, p in new_products.items() if not p.get("category")}
        if uncat:
            try:
                for pid, cat in categorize_with_llm(uncat).items():
                    catalog[pid]["category"] = cat
            except Exception as e:  # keep going; uncategorized products simply don't appear in the shop
                print(f"  WARNING: categorization failed ({e}); new products left uncategorized")
        with open(CATALOG, "w") as f:
            json.dump(dict(sorted(catalog.items())), f, indent=2)
            f.write("\n")

    # validate
    missing = {pid: sorted(fs) for pid, fs in used.items() if pid not in catalog}
    for pid, fs in missing.items():
        print(f"ERROR: unknown product id \"{pid}\" used in: {', '.join(fs)}")
    print(f"sync_products: {converted} link(s) converted in {len(edited)} file(s); {len(new_products)} new product(s); "
          f"{len(catalog)} products in catalog")
    for pid, p in new_products.items():
        print(f"  + {pid}: {p['name']} ({p.get('category', 'uncategorized')})")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
