#!/usr/bin/env python3
"""Use Claude API to recategorize products into expanded categories and generate Hugo content."""

import json
import os
import re
import anthropic

SITE_DIR = os.path.join(os.path.dirname(__file__), "site")
PRODUCTS_FILE = os.path.join(SITE_DIR, "data", "products.json")
SHOP_CONTENT_DIR = os.path.join(SITE_DIR, "content", "shop")

CATEGORIES = {
    "knives-sharpening": {
        "name": "Knives & Sharpening",
        "description": "Chef's knives, sharpening steels, and knife accessories",
        "image": "/images/shop/knives-sharpening.jpg",
    },
    "cookware-appliances": {
        "name": "Cookware & Appliances",
        "description": "Dutch ovens, skillets, blenders, and essential kitchen equipment",
        "image": "/images/shop/cookware-appliances.jpg",
    },
    "bakeware-tools": {
        "name": "Bakeware & Tools",
        "description": "Tart pans, baking mats, pastry tools, and cookie cutters",
        "image": "/images/shop/bakeware-tools.jpg",
    },
    "kitchen-gadgets": {
        "name": "Kitchen Gadgets",
        "description": "Thermometers, peelers, graters, scales, and everyday tools",
        "image": "/images/shop/kitchen-gadgets.jpg",
    },
    "spices-seasonings": {
        "name": "Spices & Seasonings",
        "description": "The global spice rack for adventurous cooks",
        "image": "/images/shop/spices-seasonings.jpg",
    },
    "asian-pantry": {
        "name": "Asian Pantry",
        "description": "Essential ingredients for Japanese, Korean, Thai, and Chinese cooking",
        "image": "/images/shop/asian-pantry.jpg",
    },
    "mexican-latin-pantry": {
        "name": "Mexican & Latin Pantry",
        "description": "Chiles, masa, achiote, and ingredients for Latin American cooking",
        "image": "/images/shop/mexican-latin-pantry.jpg",
    },
    "middle-eastern-indian-pantry": {
        "name": "Middle Eastern & Indian Pantry",
        "description": "Tamarind, asafoetida, pomegranate molasses, and more",
        "image": "/images/shop/middle-eastern-indian-pantry.jpg",
    },
    "cheese-dairy": {
        "name": "Cheese & Dairy",
        "description": "Artisan cheeses and specialty dairy for cooking",
        "image": "/images/shop/cheese-dairy.jpg",
    },
    "condiments-sauces": {
        "name": "Condiments & Sauces",
        "description": "Bold flavors to keep on hand",
        "image": "/images/shop/condiments-sauces.jpg",
    },
    "oils-vinegars": {
        "name": "Oils & Vinegars",
        "description": "Quality fats and acids that make dishes sing",
        "image": "/images/shop/oils-vinegars.jpg",
    },
    "grains-pasta-legumes": {
        "name": "Grains, Pasta & Legumes",
        "description": "Farro, polenta, lentils, specialty noodles, and flours",
        "image": "/images/shop/grains-pasta-legumes.jpg",
    },
    "sweeteners-chocolate": {
        "name": "Sweeteners & Chocolate",
        "description": "Maple syrup, jaggery, sorghum, and artisan chocolate",
        "image": "/images/shop/sweeteners-chocolate.jpg",
    },
    "pantry-staples": {
        "name": "Pantry Staples",
        "description": "Salt, canned tomatoes, panko, broth, and dried mushrooms",
        "image": "/images/shop/pantry-staples.jpg",
    },
    "books": {
        "name": "Books",
        "description": "Cookbooks and food writing worth reading",
        "image": "/images/shop/books.jpg",
    },
}

CATEGORY_ORDER = [
    "knives-sharpening",
    "cookware-appliances",
    "bakeware-tools",
    "kitchen-gadgets",
    "spices-seasonings",
    "asian-pantry",
    "mexican-latin-pantry",
    "middle-eastern-indian-pantry",
    "cheese-dairy",
    "condiments-sauces",
    "oils-vinegars",
    "grains-pasta-legumes",
    "sweeteners-chocolate",
    "pantry-staples",
    "books",
]


def categorize_with_claude(products):
    """Send all product names to Claude for categorization."""
    client = anthropic.Anthropic()

    product_lines = []
    for i, p in enumerate(products):
        product_lines.append(f"{i}: {p['name']}")

    slug_list = "\n".join(f"- {slug}: {CATEGORIES[slug]['name']}" for slug in CATEGORY_ORDER)

    prompt = f"""Categorize each product into exactly one category. Products are from a vegetarian food blog's affiliate shop.

CATEGORIES (use the slug):
{slug_list}

PRODUCTS (index: name):
{chr(10).join(product_lines)}

Return a JSON object mapping product index (as string) to category slug. Example:
{{"0": "spices-seasonings", "1": "cookware-appliances", "2": "books"}}

Rules:
- Every product must be assigned exactly one category
- Knives, sharpening steels, knife holders → knives-sharpening
- Pans, pots, Dutch ovens, blenders, food processors, stand mixers, juicers, dehydrators, smokers → cookware-appliances
- Baking pans, tart pans, baking mats, pastry tools, cookie cutters, cake rings → bakeware-tools
- Thermometers, scales, peelers, graters, spatulas, tongs, mandolines, mortars, spinners, shears → kitchen-gadgets
- Gochujang, miso, soy sauce, kecap manis, tofu skin, kombu, nori, sesame paste, yuzu, dashi, rice → asian-pantry
- Achiote, masa, dried Mexican chiles (guajillo, pasilla, ancho, chipotle, morita), Mexican oregano → mexican-latin-pantry
- Tamarind, asafoetida, ras el hanout, za'atar, harissa, Aleppo pepper, sumac, pomegranate molasses, chana dal, fenugreek, amchoor → middle-eastern-indian-pantry
- Cheeses (ricotta, gouda, chevre, pecorino), buttermilk powder → cheese-dairy
- Hot sauce, mustard, jam, chutney, preserved lemons, pickles, sriracha → condiments-sauces
- Olive oil, sesame oil, vinegar, balsamic, rosewater → oils-vinegars
- Flour, pasta, noodles, lentils, polenta, farro, couscous, beans, panko, bread crumbs → grains-pasta-legumes
- Sugar, maple syrup, jaggery, sorghum, chocolate, honey, molasses, espresso powder → sweeteners-chocolate
- Salt, canned tomatoes, broth, dried mushrooms, agar agar, xanthan gum, tapioca maltodextrin, coconut cream, tea, freeze-dried fruit → pantry-staples
- Cookbooks, food writing, recipe books → books
- When in doubt about spices: if it's clearly associated with a specific cuisine (Asian, Mexican, Middle Eastern/Indian), put it there. Otherwise use spices-seasonings.

Return ONLY the JSON object, no other text."""

    print("  Calling Claude API for categorization...")
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # Extract JSON from response (handle markdown code blocks)
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    assignments = json.loads(text)
    return assignments


def generate_shop_content(categorized_products):
    """Generate Hugo content files for the shop section."""
    os.makedirs(SHOP_CONTENT_DIR, exist_ok=True)

    # Write _index.md
    index_content = """---
title: "Shop"
description: "Recommended kitchen tools, specialty ingredients, spices, and cookbooks from Herbivoracious."
layout: "list"
type: "shop"
---
"""
    with open(os.path.join(SHOP_CONTENT_DIR, "_index.md"), "w") as f:
        f.write(index_content)
    print(f"  Wrote {SHOP_CONTENT_DIR}/_index.md")

    # Write one .md per category
    for slug in CATEGORY_ORDER:
        cat = CATEGORIES[slug]
        products = categorized_products.get(slug, [])
        if not products:
            continue
        content = f"""---
title: "{cat['name']}"
layout: "single"
type: "shop"
params:
  category_slug: "{slug}"
  description: "{cat['description']}"
  image: "{cat['image']}"
  product_count: {len(products)}
---
"""
        filepath = os.path.join(SHOP_CONTENT_DIR, f"{slug}.md")
        with open(filepath, "w") as f:
            f.write(content)
        print(f"  Wrote {filepath} ({len(products)} products)")


def main():
    with open(PRODUCTS_FILE) as f:
        data = json.load(f)

    products = data["products"]
    print(f"Loaded {len(products)} products from {PRODUCTS_FILE}")

    # Categorize with Claude
    assignments = categorize_with_claude(products)

    # Build categorized product lists
    categorized = {}
    uncategorized = []
    for idx_str, slug in assignments.items():
        idx = int(idx_str)
        if idx >= len(products):
            continue
        product = products[idx]
        if slug not in CATEGORIES:
            print(f"  WARNING: Unknown category '{slug}' for '{product['name']}', using pantry-staples")
            slug = "pantry-staples"
        if slug not in categorized:
            categorized[slug] = []
        categorized[slug].append(product)

    # Check for unassigned products
    assigned_indices = {int(k) for k in assignments.keys()}
    for i, p in enumerate(products):
        if i not in assigned_indices:
            uncategorized.append(p)
            print(f"  WARNING: Unassigned product: {p['name']}")

    # Sort products within each category
    for slug in categorized:
        categorized[slug].sort(key=lambda p: p["name"].lower())

    # Print summary
    print("\nCategory breakdown:")
    total = 0
    for slug in CATEGORY_ORDER:
        count = len(categorized.get(slug, []))
        if count:
            print(f"  {CATEGORIES[slug]['name']}: {count}")
            total += count
    print(f"  Total categorized: {total}")
    if uncategorized:
        print(f"  Uncategorized: {len(uncategorized)}")

    # Write updated products.json with categories
    output_categories = []
    for slug in CATEGORY_ORDER:
        if slug not in categorized:
            continue
        cat = CATEGORIES[slug]
        cat_products = []
        for p in categorized[slug]:
            entry = {"name": p["name"], "url": p["url"]}
            if "review_url" in p:
                entry["review_url"] = p["review_url"]
            if "featured_in" in p:
                entry["featured_in"] = p["featured_in"]
            cat_products.append(entry)
        output_categories.append({
            "name": cat["name"],
            "slug": slug,
            "description": cat["description"],
            "image": cat["image"],
            "products": cat_products,
        })

    with open(PRODUCTS_FILE, "w") as f:
        json.dump({"categories": output_categories}, f, indent=2)
    print(f"\nWrote categorized products to {PRODUCTS_FILE}")

    # Generate Hugo content files
    print("\nGenerating shop content pages...")
    generate_shop_content(categorized)


if __name__ == "__main__":
    main()
