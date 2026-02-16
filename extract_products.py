#!/usr/bin/env python3
"""Extract Amazon affiliate products from blog posts and amazon_links.md into products.json."""

import json
import os
import re
import glob
from collections import defaultdict

SITE_DIR = os.path.join(os.path.dirname(__file__), "site")
CONTENT_DIR = os.path.join(SITE_DIR, "content")
POSTS_DIR = os.path.join(CONTENT_DIR, "posts")
OUTPUT_FILE = os.path.join(SITE_DIR, "data", "products.json")
AMAZON_LINKS_FILE = os.path.join(os.path.dirname(__file__), "amazon_links.md")

# ASIN regex: 10-char alphanumeric Amazon product ID
ASIN_RE = re.compile(r'/(?:dp|gp/product)/([A-Z0-9]{10})')

# Products to remove by ASIN (non-food, novelty, duplicates to merge)
ASIN_BLOCKLIST = set()

# Junk name patterns — products with these names get filtered out
JUNK_NAME_PATTERNS = re.compile(
    r'(?i)'
    r'^Product [A-Z0-9]+$|'           # "Product B0076NOGWW"
    r'^great item$|'
    r'^from a can$|'
    r'^this version$|'
    r'^simple and inexpensive$|'
    r'^expensive paraphenalia$|'
    r'^more expensive .* model$|'
    r'^better ideas$|'
    r'^basic \$\d+ model$|'
    r'^get one right now$|'
    r'^here on Amazon$|'
    r'^or you can find it on Amazon$|'
    r'^you can jump right over to Amazon|'
    r'^from ChefShop on Amazon$|'
    r'^from the area of Puy$|'
    r'^just soft-boiled$|'
    r'^smaller quantities$|'
    r'^this enormous roll$|'
    r'^this one from Beaufor$|'
    r'^dessert recipe$|'
    r'^flat-stanleyish$|'
    r'^clean dishtowel$|'
    r'^lovely, if pricey|'
    r'^a set like this|'
    r'^Karen and Andrew$|'
    r'^7 piece nylon and wooden|'
    r'^8 piece Unison non-stick|'
    r'^airlock$|'
    r'^novelty beer cozy$'
)

# Non-food/non-cooking items to remove
NON_FOOD_NAMES = re.compile(
    r'(?i)'
    r'Nikon D7000|'
    r'Terex AL-5L LED Light Tower|'
    r'True Blood|'
    r'I Like You.*Hospitality|'
    r'Roasting in Hell.s Kitchen|'      # Not a cookbook, it's a memoir
    r'Top Chef'
)

# Names that are too short/generic to be useful (brand-only, single words)
GENERIC_SHORT_NAMES = {
    "shun", "plenty", "silpat", "bourdain", "ina garten",
    "jaques pepin", "daniel boulud", "bill buford",
    "edward espe brown", "food & wine", "food &amp; wine",
    "frantoia", "corningware",
}

# Duplicate product mappings: keep the best ASIN, remove the rest
# Maps "remove this ASIN" -> "keep this ASIN instead"
# (We'll handle name-based dedup in merge_products)


def extract_asin(url):
    """Extract ASIN from an Amazon URL."""
    m = ASIN_RE.search(url)
    return m.group(1) if m else None


def is_junk_product(name):
    """Check if a product name is junk/generic and should be filtered."""
    if JUNK_NAME_PATTERNS.search(name):
        return True
    if NON_FOOD_NAMES.search(name):
        return True
    if name.lower().strip() in GENERIC_SHORT_NAMES:
        return True
    # Brand-only names under 8 chars (e.g., "Shun", "OXO")
    if len(name.strip()) < 6 and not re.search(r'\d', name):
        return True
    return False


def slug_to_url(slug):
    """Convert a post slug to its permalink URL (approximate)."""
    # Try to find the post file to get the date
    post_file = os.path.join(POSTS_DIR, f"{slug}.md")
    if os.path.exists(post_file):
        with open(post_file, "r") as f:
            content = f.read(500)
            date_m = re.search(r'date:\s*(\d{4})-(\d{2})', content)
            if date_m:
                year, month = date_m.group(1), date_m.group(2)
                return f"/{year}/{month}/{slug}/"
    return f"/{slug}/"


def parse_amazon_links_md():
    """Parse amazon_links.md for curated products with herb-hugo-20 tag."""
    products = {}
    with open(AMAZON_LINKS_FILE, "r") as f:
        for line in f:
            if not line.startswith("| "):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 6:
                continue
            slug, anchor, product_name, url = parts[1], parts[2], parts[3], parts[4]
            if slug in ("Post", "------") or "skip" in url.lower() or not url.startswith("http"):
                continue
            asin = extract_asin(url)
            if not asin:
                continue
            if asin in ASIN_BLOCKLIST:
                continue
            # Normalize URL to clean dp format
            clean_url = f"https://www.amazon.com/dp/{asin}?tag=herb-hugo-20"
            post_url = slug_to_url(slug)
            if asin not in products:
                products[asin] = {
                    "name": product_name,
                    "url": clean_url,
                    "asin": asin,
                    "source": "amazon_links_md",
                    "featured_in": [],
                    "anchor_text": anchor,
                }
            if post_url not in products[asin]["featured_in"]:
                products[asin]["featured_in"].append(post_url)
    return products


GENERIC_ANCHORS = {
    "buy it", "on amazon", "like this", "basic", "this one", "here",
    "amazon", "check it out", "get it", "get one", "order", "order it",
    "these", "this", "that", "it", "one", "some", "them", "link",
    "amazingly delicious things", "a set like this that has covers",
}


def scan_posts_for_old_links():
    """Scan posts for old poeticlicen07-20 affiliate links."""
    products = {}
    pattern = re.compile(
        r'<a[^>]+href="[^"]*amazon\.com[^"]*tag=poeticlicen07-20[^"]*"[^>]*>(.*?)</a>',
        re.DOTALL
    )
    url_pattern = re.compile(r'href="([^"]*amazon\.com[^"]*tag=poeticlicen07-20[^"]*)"')

    for filepath in glob.glob(os.path.join(POSTS_DIR, "*.md")):
        with open(filepath, "r") as f:
            content = f.read()
        slug = os.path.splitext(os.path.basename(filepath))[0]
        post_url = slug_to_url(slug)

        for match in pattern.finditer(content):
            anchor_text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            url_match = url_pattern.search(match.group(0))
            if not url_match:
                continue
            url = url_match.group(1).replace("&amp;", "&")
            asin = extract_asin(url)
            if not asin:
                continue
            if asin in ASIN_BLOCKLIST:
                continue
            clean_url = f"https://www.amazon.com/dp/{asin}?tag=herb-hugo-20"
            # Skip products with generic/useless anchor text
            if not anchor_text or anchor_text.lower() in GENERIC_ANCHORS or len(anchor_text) < 4:
                continue
            if asin not in products:
                products[asin] = {
                    "name": anchor_text or f"Product {asin}",
                    "url": clean_url,
                    "asin": asin,
                    "source": "old_post_links",
                    "featured_in": [],
                    "anchor_text": anchor_text,
                }
            if post_url not in products[asin]["featured_in"]:
                products[asin]["featured_in"].append(post_url)
    return products


def scan_review_pages():
    """Scan standalone kitchen tool review pages for herbivoracious-shop-20 links."""
    products = {}
    pattern = re.compile(
        r'<a[^>]+href="([^"]*amazon\.com[^"]*tag=herbivoracious-shop-20[^"]*)"[^>]*>(.*?)</a>',
        re.DOTALL
    )

    for filepath in glob.glob(os.path.join(CONTENT_DIR, "*.md")):
        with open(filepath, "r") as f:
            content = f.read()
        slug = os.path.splitext(os.path.basename(filepath))[0]
        # Get the page title from frontmatter
        title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        page_title = title_match.group(1).strip('"\'') if title_match else slug
        page_url = f"/{slug}/"

        for match in pattern.finditer(content):
            url = match.group(1).replace("&amp;", "&")
            anchor_text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            asin = extract_asin(url)
            if not asin:
                continue
            if asin in ASIN_BLOCKLIST:
                continue
            clean_url = f"https://www.amazon.com/dp/{asin}?tag=herb-hugo-20"
            if asin not in products:
                products[asin] = {
                    "name": anchor_text or f"Product {asin}",
                    "url": clean_url,
                    "asin": asin,
                    "source": "review_page",
                    "featured_in": [],
                    "anchor_text": anchor_text,
                    "review_url": page_url,
                    "review_title": page_title,
                }
            else:
                # Add review info even if product exists from another source
                products[asin]["review_url"] = page_url
                products[asin]["review_title"] = page_title
            if page_url not in products[asin]["featured_in"]:
                products[asin]["featured_in"].append(page_url)

    # Also scan posts directory for the two kitchen tool review posts
    for filepath in glob.glob(os.path.join(POSTS_DIR, "*.md")):
        with open(filepath, "r") as f:
            content = f.read()
        if "herbivoracious-shop-20" not in content:
            continue
        slug = os.path.splitext(os.path.basename(filepath))[0]
        title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        page_title = title_match.group(1).strip('"\'') if title_match else slug
        page_url = slug_to_url(slug)

        for match in pattern.finditer(content):
            url = match.group(1).replace("&amp;", "&")
            anchor_text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            asin = extract_asin(url)
            if not asin:
                continue
            if asin in ASIN_BLOCKLIST:
                continue
            clean_url = f"https://www.amazon.com/dp/{asin}?tag=herb-hugo-20"
            if asin not in products:
                products[asin] = {
                    "name": anchor_text or f"Product {asin}",
                    "url": clean_url,
                    "asin": asin,
                    "source": "review_page",
                    "featured_in": [],
                    "anchor_text": anchor_text,
                    "review_url": page_url,
                    "review_title": page_title,
                }
            else:
                if "review_url" not in products[asin]:
                    products[asin]["review_url"] = page_url
                    products[asin]["review_title"] = page_title
            if page_url not in products[asin]["featured_in"]:
                products[asin]["featured_in"].append(page_url)
    return products


def merge_products(*product_dicts):
    """Merge multiple product dicts, deduplicating by ASIN. Prefer amazon_links_md names."""
    merged = {}
    for products in product_dicts:
        for asin, product in products.items():
            if asin not in merged:
                merged[asin] = dict(product)
            else:
                existing = merged[asin]
                # Prefer curated name from amazon_links.md
                if product.get("source") == "amazon_links_md" and existing.get("source") != "amazon_links_md":
                    existing["name"] = product["name"]
                # Merge featured_in lists
                for url in product.get("featured_in", []):
                    if url not in existing["featured_in"]:
                        existing["featured_in"].append(url)
                # Carry over review info
                if "review_url" in product and "review_url" not in existing:
                    existing["review_url"] = product["review_url"]
                    existing["review_title"] = product.get("review_title", "")
    return merged


def filter_junk(products):
    """Remove junk products after merge."""
    filtered = {}
    removed = []
    for asin, product in products.items():
        if is_junk_product(product["name"]):
            removed.append(product["name"])
        else:
            filtered[asin] = product
    if removed:
        print(f"  Removed {len(removed)} junk products:")
        for name in sorted(removed):
            print(f"    - {name}")
    return filtered


def build_flat_products(products):
    """Build a flat list of products (no categories) for products.json.
    Categorization is handled separately by categorize_products.py."""
    product_list = []
    for asin, product in products.items():
        entry = {
            "name": product["name"],
            "url": product["url"],
            "asin": asin,
        }
        if product.get("review_url"):
            entry["review_url"] = product["review_url"]
        # Only include first few featured_in links
        featured = [u for u in product.get("featured_in", []) if u != product.get("review_url")]
        if featured:
            entry["featured_in"] = featured[:3]
        product_list.append(entry)

    product_list.sort(key=lambda p: p["name"].lower())
    return product_list


def main():
    print("Extracting products from amazon_links.md...")
    md_products = parse_amazon_links_md()
    print(f"  Found {len(md_products)} products")

    print("Scanning posts for old poeticlicen07-20 links...")
    old_products = scan_posts_for_old_links()
    print(f"  Found {len(old_products)} products")

    print("Scanning review pages for herbivoracious-shop-20 links...")
    review_products = scan_review_pages()
    print(f"  Found {len(review_products)} products")

    print("Merging and deduplicating...")
    all_products = merge_products(md_products, old_products, review_products)
    print(f"  Total unique products (pre-filter): {len(all_products)}")

    print("Filtering junk products...")
    all_products = filter_junk(all_products)
    print(f"  Total clean products: {len(all_products)}")

    # Write flat product list — categorize_products.py will add categories
    product_list = build_flat_products(all_products)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    output = {"products": product_list}
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nWrote {len(product_list)} products to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
