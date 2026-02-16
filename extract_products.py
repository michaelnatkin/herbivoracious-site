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

# Category assignments by keyword matching on product name/anchor text
CATEGORY_RULES = [
    # Kitchen Tools - equipment, appliances, cookware
    ("Kitchen Tools", re.compile(
        r'(?i)knife|knives|skillet|dutch oven|pan\b|blender|grater|ricer|'
        r'peeler|thermometer|sharpener|sharpening|spatula|mat\b|stone\b|'
        r'tart pan|cookie cutter|crepe pan|baking mat|whip|dispenser|'
        r'paella pan|mandoline|scale|parchment|pastry blender|grapefruit spoon|'
        r'cheese making|spherification'
    )),
    # Books
    ("Books", re.compile(
        r'(?i)\bbook\b|cookbook|herbivoracious.*natkin|mastering the art|'
        r'flavor revolution|best food writing|ideas in food|curious cook|'
        r'aromas of aleppo|alice waters|simple food'
    )),
    # Spices & Seasonings
    ("Spices & Seasonings", re.compile(
        r'(?i)spice|seasoning|paprika|pimenton|cumin|chili powder|chile powder|'
        r'ras el hanout|za.atar|berbere|chaat masala|garam masala|curry powder|'
        r'sumac|asafoetida|hing\b|fennel pollen|nutmeg|saffron|amchoor|'
        r'black salt|kala namak|long pepper|sichuan pepper|szechwan pepper|'
        r'mustard seed|oregano.*mexican|harissa.*seasoning|five.spice'
    )),
    # Condiments & Sauces
    ("Condiments & Sauces", re.compile(
        r'(?i)gochujang|kochujang|ssamjang|miso\b|harissa|hot sauce|tapatio|'
        r'soy sauce|kecap manis|nama shoyu|tamarind|sriracha|chili oil|'
        r'mustard\b|chutney|relish|jam\b|pickle|amba|preserved lemon|'
        r'cornichon|achiote paste|pectin|transglutaminase|activa'
    )),
    # Oils & Vinegars
    ("Oils & Vinegars", re.compile(
        r'(?i)vinegar|oil\b|balsamic|balsamico|sherry vinegar|champagne vinegar|'
        r'sesame oil|olive oil|rosewater|rose water'
    )),
    # Grains & Legumes
    ("Grains & Legumes", re.compile(
        r'(?i)flour\b|rice\b(?!.*vinegar)|lentil|chickpea|chana dal|bean|'
        r'farro\b|polenta|cornmeal|masa\b|buckwheat|teff\b|noodle|pasta|'
        r'soba\b|orecchiette|stringozzi|fregola|couscous|vermicelli|'
        r'dangmyeon|poha\b|flatbread|bread crumb|panko|xanthan'
    )),
    # Sweeteners
    ("Sweeteners", re.compile(
        r'(?i)maple syrup|sugar|jaggery|sorghum syrup|honey\b|molasses|'
        r'malt powder|malted milk|isomalt|chocolate\b|espresso.*instant|'
        r'buttermilk.*powder|demerara'
    )),
    # Dried Vegetables
    ("Dried Vegetables", re.compile(
        r'(?i)dried.*mushroom|morel|shiitake.*dried|kombu|seaweed|nori|'
        r'dried.*pepper|dried.*chile|dried.*chili|guajillo|pasilla|ancho.*dried|'
        r'chipotle.*dried|morita|new mexico.*chile|'
        r'dried.*kaffir|dried.*fenugreek|dried.*mint|preserved vegetable|'
        r'zha cai|jackfruit|yuba|tofu skin|beancurd'
    )),
    # Specialty Ingredients (catch-all for everything else)
    ("Specialty Ingredients", re.compile(r'.*')),
]


def extract_asin(url):
    """Extract ASIN from an Amazon URL."""
    m = ASIN_RE.search(url)
    return m.group(1) if m else None


def categorize_product(name):
    """Assign a category based on product name."""
    for cat_name, pattern in CATEGORY_RULES:
        if pattern.search(name):
            return cat_name
    return "Specialty Ingredients"


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


def build_categories(products):
    """Organize products into categories."""
    cat_products = defaultdict(list)
    for asin, product in products.items():
        category = categorize_product(product["name"])
        entry = {
            "name": product["name"],
            "url": product["url"],
        }
        if product.get("review_url"):
            entry["review_url"] = product["review_url"]
        # Only include first few featured_in links
        featured = [u for u in product.get("featured_in", []) if u != product.get("review_url")]
        if featured:
            entry["featured_in"] = featured[:3]
        cat_products[category].append(entry)

    # Sort products within each category alphabetically
    for cat in cat_products:
        cat_products[cat].sort(key=lambda p: p["name"].lower())

    category_meta = {
        "Kitchen Tools": {
            "description": "Essential equipment for the serious home cook",
            "image": "/images/shop/kitchen-tools.jpg",
        },
        "Specialty Ingredients": {
            "description": "Unique ingredients that elevate everyday cooking",
            "image": "/images/shop/specialty-ingredients.jpg",
        },
        "Spices & Seasonings": {
            "description": "The global spice rack for adventurous cooks",
            "image": "/images/shop/spices-seasonings.jpg",
        },
        "Grains & Legumes": {
            "description": "Wholesome staples from around the world",
            "image": "/images/shop/grains-legumes.jpg",
        },
        "Condiments & Sauces": {
            "description": "Bold flavors to keep on hand",
            "image": "/images/shop/condiments-sauces.jpg",
        },
        "Oils & Vinegars": {
            "description": "Quality fats and acids that make dishes sing",
            "image": "/images/shop/oils-vinegars.jpg",
        },
        "Sweeteners": {
            "description": "Beyond white sugar — natural and specialty sweeteners",
            "image": "/images/shop/sweeteners.jpg",
        },
        "Dried Vegetables": {
            "description": "Mushrooms, chiles, seaweed, and other pantry powerhouses",
            "image": "/images/shop/dried-vegetables.jpg",
        },
        "Books": {
            "description": "Cookbooks and food writing worth reading",
            "image": "/images/shop/books.jpg",
        },
    }

    # Ordered category list
    category_order = [
        "Kitchen Tools", "Specialty Ingredients", "Spices & Seasonings",
        "Grains & Legumes", "Condiments & Sauces", "Oils & Vinegars",
        "Sweeteners", "Dried Vegetables", "Books",
    ]

    categories = []
    for name in category_order:
        if name not in cat_products:
            continue
        slug = name.lower().replace(" & ", "-").replace(" ", "-")
        meta = category_meta.get(name, {})
        categories.append({
            "name": name,
            "slug": slug,
            "description": meta.get("description", ""),
            "image": meta.get("image", ""),
            "products": cat_products[name],
        })

    return categories


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
    print(f"  Total unique products: {len(all_products)}")

    print("Categorizing products...")
    categories = build_categories(all_products)
    for cat in categories:
        print(f"  {cat['name']}: {len(cat['products'])} products")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    output = {"categories": categories}
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nWrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
