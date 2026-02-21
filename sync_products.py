#!/usr/bin/env python3
"""Sync Amazon affiliate products from blog posts into products.json.

Scans all posts for Amazon links, de-duplicates by ASIN, categorizes new
products via LLM (with a persistent cache), and writes an updated products.json.
Designed to run both locally and in CI.
"""

import json
import os
import re
import glob
import sys

SITE_DIR = os.path.join(os.path.dirname(__file__), "site")
CONTENT_DIR = os.path.join(SITE_DIR, "content")
POSTS_DIR = os.path.join(CONTENT_DIR, "posts")
PRODUCTS_FILE = os.path.join(SITE_DIR, "data", "products.json")
CATEGORY_CACHE_FILE = os.path.join(SITE_DIR, "data", "product-categories.json")
SHOP_CONTENT_DIR = os.path.join(SITE_DIR, "content", "shop")

# ASIN regex: 10-char alphanumeric Amazon product ID
ASIN_RE = re.compile(r'/(?:dp|gp/product)/([A-Z0-9]{10})')

# Match <a> tags with herb-hugo-20 affiliate links
HERB_LINK_RE = re.compile(
    r'<a[^>]+href="([^"]*amazon\.com[^"]*tag=herb-hugo-20[^"]*)"[^>]*>(.*?)</a>',
    re.DOTALL
)

# Match <a> tags with herbivoracious-shop-20 affiliate links (review pages)
SHOP_LINK_RE = re.compile(
    r'<a[^>]+href="([^"]*amazon\.com[^"]*tag=herbivoracious-shop-20[^"]*)"[^>]*>(.*?)</a>',
    re.DOTALL
)

# Match <a> tags with old poeticlicen07-20 affiliate links
OLD_LINK_RE = re.compile(
    r'<a[^>]+href="([^"]*amazon\.com[^"]*tag=poeticlicen07-20[^"]*)"[^>]*>(.*?)</a>',
    re.DOTALL
)

# --- Junk filters (from extract_products.py) ---

JUNK_NAME_PATTERNS = re.compile(
    r'(?i)'
    r'^Product [A-Z0-9]+$|'
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

NON_FOOD_NAMES = re.compile(
    r'(?i)'
    r'Nikon D7000|'
    r'Terex AL-5L LED Light Tower|'
    r'True Blood|'
    r'I Like You.*Hospitality|'
    r'Roasting in Hell.s Kitchen|'
    r'Top Chef'
)

GENERIC_SHORT_NAMES = {
    "shun", "plenty", "silpat", "bourdain", "ina garten",
    "jaques pepin", "daniel boulud", "bill buford",
    "edward espe brown", "food & wine", "food &amp; wine",
    "frantoia", "corningware",
}

GENERIC_ANCHORS = {
    "buy it", "on amazon", "like this", "basic", "this one", "here",
    "amazon", "check it out", "get it", "get one", "order", "order it",
    "these", "this", "that", "it", "one", "some", "them", "link",
    "amazingly delicious things", "a set like this that has covers",
}

# --- Categories ---

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

CATEGORY_DESCRIPTIONS = {
    "knives-sharpening": "Chef's knives, sharpening steels, and knife accessories",
    "cookware-appliances": "Dutch ovens, skillets, blenders, and essential kitchen equipment",
    "bakeware-tools": "Tart pans, baking mats, pastry tools, and cookie cutters",
    "kitchen-gadgets": "Thermometers, peelers, graters, scales, and everyday tools",
    "spices-seasonings": "The global spice rack for adventurous cooks",
    "asian-pantry": "Essential ingredients for Japanese, Korean, Thai, and Chinese cooking",
    "mexican-latin-pantry": "Chiles, masa, achiote, and ingredients for Latin American cooking",
    "middle-eastern-indian-pantry": "Tamarind, asafoetida, pomegranate molasses, and more",
    "cheese-dairy": "Artisan cheeses and specialty dairy for cooking",
    "condiments-sauces": "Bold flavors to keep on hand",
    "oils-vinegars": "Quality fats and acids that make dishes sing",
    "grains-pasta-legumes": "Farro, polenta, lentils, specialty noodles, and flours",
    "sweeteners-chocolate": "Maple syrup, jaggery, sorghum, and artisan chocolate",
    "pantry-staples": "Salt, canned tomatoes, panko, broth, and dried mushrooms",
    "books": "Cookbooks and food writing worth reading",
}


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
    if len(name.strip()) < 6 and not re.search(r'\d', name):
        return True
    return False


def get_post_url(filepath, content):
    """Get the permalink URL for a post from its frontmatter."""
    slug = os.path.splitext(os.path.basename(filepath))[0]
    date_m = re.search(r'date:\s*(\d{4})-(\d{2})', content[:500])
    if date_m:
        year, month = date_m.group(1), date_m.group(2)
        return f"/{year}/{month}/{slug}/"
    return f"/{slug}/"


def strip_html_tags(text):
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text).strip()


def scan_all_posts():
    """Scan all posts for Amazon affiliate links (all tag variants)."""
    products = {}

    for filepath in glob.glob(os.path.join(POSTS_DIR, "*.md")):
        with open(filepath, "r") as f:
            content = f.read()
        post_url = get_post_url(filepath, content)

        # Scan for herb-hugo-20 links (current affiliate tag)
        for match in HERB_LINK_RE.finditer(content):
            url = match.group(1).replace("&amp;", "&")
            anchor = strip_html_tags(match.group(2))
            _add_product(products, url, anchor, post_url)

        # Scan for old poeticlicen07-20 links
        for match in OLD_LINK_RE.finditer(content):
            url = match.group(1).replace("&amp;", "&")
            anchor = strip_html_tags(match.group(2))
            _add_product(products, url, anchor, post_url)

        # Scan for herbivoracious-shop-20 links (review posts)
        for match in SHOP_LINK_RE.finditer(content):
            url = match.group(1).replace("&amp;", "&")
            anchor = strip_html_tags(match.group(2))
            _add_product(products, url, anchor, post_url, is_review=True)

    return products


def scan_content_pages():
    """Scan top-level content pages for review links."""
    products = {}

    for filepath in glob.glob(os.path.join(CONTENT_DIR, "*.md")):
        with open(filepath, "r") as f:
            content = f.read()
        slug = os.path.splitext(os.path.basename(filepath))[0]
        page_url = f"/{slug}/"

        title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        page_title = title_match.group(1).strip('"\'') if title_match else slug

        for pattern in [HERB_LINK_RE, SHOP_LINK_RE, OLD_LINK_RE]:
            for match in pattern.finditer(content):
                url = match.group(1).replace("&amp;", "&")
                anchor = strip_html_tags(match.group(2))
                asin = extract_asin(url)
                if not asin:
                    continue
                clean_url = f"https://www.amazon.com/dp/{asin}?tag=herb-hugo-20"

                if not anchor or anchor.lower() in GENERIC_ANCHORS or len(anchor) < 4:
                    continue

                if asin not in products:
                    products[asin] = {
                        "name": anchor,
                        "url": clean_url,
                        "asin": asin,
                        "featured_in": [],
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


def _add_product(products, url, anchor, post_url, is_review=False):
    """Add a product to the products dict from a scanned link."""
    asin = extract_asin(url)
    if not asin:
        return
    clean_url = f"https://www.amazon.com/dp/{asin}?tag=herb-hugo-20"

    if not anchor or anchor.lower() in GENERIC_ANCHORS or len(anchor) < 4:
        return

    if asin not in products:
        products[asin] = {
            "name": anchor,
            "url": clean_url,
            "asin": asin,
            "featured_in": [],
        }
    else:
        # Prefer longer/more descriptive name
        if len(anchor) > len(products[asin]["name"]):
            products[asin]["name"] = anchor

    if post_url not in products[asin]["featured_in"]:
        products[asin]["featured_in"].append(post_url)


def merge_scanned(post_products, page_products):
    """Merge post and page scan results."""
    merged = dict(post_products)
    for asin, product in page_products.items():
        if asin not in merged:
            merged[asin] = dict(product)
        else:
            existing = merged[asin]
            for url in product.get("featured_in", []):
                if url not in existing["featured_in"]:
                    existing["featured_in"].append(url)
            if "review_url" in product and "review_url" not in existing:
                existing["review_url"] = product["review_url"]
                existing["review_title"] = product.get("review_title", "")
    return merged


def filter_junk(products):
    """Remove junk products."""
    filtered = {}
    removed = []
    for asin, product in products.items():
        if is_junk_product(product["name"]):
            removed.append(product["name"])
        else:
            filtered[asin] = product
    if removed:
        print(f"  Filtered {len(removed)} junk products")
    return filtered


def load_existing_products():
    """Load the current products.json, returning {asin: product} and {asin: category_slug}."""
    if not os.path.exists(PRODUCTS_FILE):
        return {}, {}

    with open(PRODUCTS_FILE) as f:
        data = json.load(f)

    products_by_asin = {}
    categories_by_asin = {}

    for category in data.get("categories", []):
        slug = category["slug"]
        for product in category.get("products", []):
            asin = extract_asin(product["url"])
            if asin:
                products_by_asin[asin] = product
                categories_by_asin[asin] = slug

    return products_by_asin, categories_by_asin


def load_category_cache():
    """Load the ASIN -> category cache."""
    if os.path.exists(CATEGORY_CACHE_FILE):
        with open(CATEGORY_CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_category_cache(cache):
    """Save the ASIN -> category cache."""
    # Sort by ASIN for stable diffs
    sorted_cache = dict(sorted(cache.items()))
    with open(CATEGORY_CACHE_FILE, "w") as f:
        json.dump(sorted_cache, f, indent=2)
        f.write("\n")


def categorize_with_llm(uncategorized_products):
    """Call Anthropic API to categorize products. Returns {asin: category_slug}."""
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
    asin_list = list(uncategorized_products.keys())
    product_lines = []
    for i, asin in enumerate(asin_list):
        product_lines.append(f"{i}: {uncategorized_products[asin]['name']}")

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

    print(f"  Calling Claude API to categorize {len(asin_list)} products...")
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
        if idx < len(asin_list):
            asin = asin_list[idx]
            if slug in CATEGORIES:
                result[asin] = slug
            else:
                print(f"  WARNING: Unknown category '{slug}' for '{uncategorized_products[asin]['name']}', using pantry-staples")
                result[asin] = "pantry-staples"
    return result


def update_product_counts():
    """Update product_count in each shop/*.md front matter."""
    # Load current products.json to get counts
    with open(PRODUCTS_FILE) as f:
        data = json.load(f)

    counts = {}
    for category in data.get("categories", []):
        counts[category["slug"]] = len(category.get("products", []))

    for slug, count in counts.items():
        filepath = os.path.join(SHOP_CONTENT_DIR, f"{slug}.md")
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r") as f:
            content = f.read()

        updated = re.sub(
            r'(product_count:\s*)\d+',
            f'\\g<1>{count}',
            content,
        )
        if updated != content:
            with open(filepath, "w") as f:
                f.write(updated)
            print(f"  Updated {slug}.md product_count: {count}")


def build_products_json(all_products, category_cache, existing_products):
    """Build the categorized products.json structure."""
    # Group products by category
    by_category = {slug: [] for slug in CATEGORY_ORDER}

    for asin, product in all_products.items():
        cat = category_cache.get(asin, "pantry-staples")
        if cat not in by_category:
            cat = "pantry-staples"

        # Prefer existing curated name/data
        existing = existing_products.get(asin, {})
        entry = {
            "name": existing.get("name", product["name"]),
            "url": f"https://www.amazon.com/dp/{asin}?tag=herb-hugo-20",
        }

        # Preserve review_url from existing or scanned
        review_url = existing.get("review_url") or product.get("review_url")
        if review_url:
            entry["review_url"] = review_url

        # Merge featured_in from both sources
        featured = set()
        for url in existing.get("featured_in", []):
            featured.add(url)
        for url in product.get("featured_in", []):
            featured.add(url)
        # Remove review_url from featured_in
        featured.discard(review_url)
        if featured:
            entry["featured_in"] = sorted(featured)[:5]

        by_category[cat].append(entry)

    # Build output structure
    output_categories = []
    for slug in CATEGORY_ORDER:
        products = by_category[slug]
        if not products:
            continue
        products.sort(key=lambda p: p["name"].lower())
        output_categories.append({
            "name": CATEGORIES[slug],
            "slug": slug,
            "description": CATEGORY_DESCRIPTIONS[slug],
            "image": f"/images/shop/{slug}.jpg",
            "products": products,
        })

    return {"categories": output_categories}


def main():
    print("=== sync_products.py ===\n")

    # Step 1: Scan all posts
    print("Scanning posts for Amazon links...")
    post_products = scan_all_posts()
    print(f"  Found {len(post_products)} unique products in posts")

    print("Scanning content pages for review links...")
    page_products = scan_content_pages()
    print(f"  Found {len(page_products)} unique products in content pages")

    # Step 2: Merge
    all_scanned = merge_scanned(post_products, page_products)
    print(f"  Total unique products from scan: {len(all_scanned)}")

    # Step 3: Filter junk
    all_scanned = filter_junk(all_scanned)
    print(f"  After filtering: {len(all_scanned)}")

    # Step 4: Load existing data
    print("\nLoading existing products.json...")
    existing_products, existing_categories = load_existing_products()
    print(f"  Existing products: {len(existing_products)}")

    # Step 5: Load category cache
    category_cache = load_category_cache()
    print(f"  Category cache: {len(category_cache)} entries")

    # Seed cache from existing products.json categories
    cache_updated = False
    for asin, cat_slug in existing_categories.items():
        if asin not in category_cache:
            category_cache[asin] = cat_slug
            cache_updated = True

    if cache_updated:
        print(f"  Seeded cache from existing products.json (now {len(category_cache)} entries)")

    # Step 6: Find uncategorized products
    uncategorized = {}
    for asin, product in all_scanned.items():
        if asin not in category_cache:
            uncategorized[asin] = product

    print(f"\n  New products to categorize: {len(uncategorized)}")

    # Step 7: Categorize via LLM if needed
    if uncategorized:
        new_categories = categorize_with_llm(uncategorized)
        if new_categories:
            category_cache.update(new_categories)
            print(f"  Categorized {len(new_categories)} products via LLM")
        else:
            # Fallback: put uncategorized in pantry-staples
            print("  WARNING: Using pantry-staples fallback for uncategorized products")
            for asin in uncategorized:
                if asin not in category_cache:
                    category_cache[asin] = "pantry-staples"
    else:
        print("  No new products to categorize (0 LLM calls needed)")

    # Step 8: Save category cache
    save_category_cache(category_cache)
    print(f"  Saved category cache ({len(category_cache)} entries)")

    # Step 9: Build and write products.json
    print("\nBuilding products.json...")
    output = build_products_json(all_scanned, category_cache, existing_products)
    total = sum(len(c["products"]) for c in output["categories"])

    with open(PRODUCTS_FILE, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")
    print(f"  Wrote {total} products across {len(output['categories'])} categories")

    # Step 10: Update product_count in shop .md files
    print("\nUpdating shop page product counts...")
    update_product_counts()

    print(f"\nDone! {total} total products in {PRODUCTS_FILE}")


if __name__ == "__main__":
    main()
