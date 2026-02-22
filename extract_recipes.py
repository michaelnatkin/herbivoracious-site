#!/usr/bin/env python3
"""Extract recipe data from recipe-card HTML in posts and add to front matter."""

import glob
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

POSTS_DIR = Path("site/content/posts")


def strip_html(text):
    """Remove HTML tags and clean up whitespace."""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text().strip()


def clean_text(text):
    """Normalize whitespace in text."""
    return re.sub(r"\s+", " ", text).strip()


def extract_recipe_from_card(card_html):
    """Parse a recipe-card div and extract structured data."""
    soup = BeautifulSoup(card_html, "html.parser")
    card = soup.find("div", class_="recipe-card")
    if not card:
        return None

    recipe = {}

    # Extract recipe name from <strong>, <h2>, or first bold text
    name_el = card.find("h2") or card.find("strong")
    if name_el:
        recipe["name"] = clean_text(name_el.get_text())

    # Extract metadata from <em> tags before the first <ul>
    # Look for yield, time, diet info
    meta_texts = []
    first_ul = card.find("ul")
    if first_ul:
        # Collect text before first ul
        for el in card.children:
            if el == first_ul:
                break
            if hasattr(el, "get_text"):
                meta_texts.append(clean_text(el.get_text()))
            elif isinstance(el, NavigableString):
                t = clean_text(str(el))
                if t:
                    meta_texts.append(t)

    meta_text = " ".join(meta_texts)

    # Parse yield (serves/yields/makes)
    yield_match = re.search(
        r"(?:serves?|yields?|makes?)\s+(.+?)(?:\s*[/|]|\s*$)",
        meta_text,
        re.IGNORECASE,
    )
    if yield_match:
        recipe["yield"] = clean_text(yield_match.group(1).rstrip("."))

    # Parse time
    time_match = re.search(
        r"(\d+\s*(?:minutes?|mins?|hours?|hrs?)(?:\s*(?:active|total|prep|cook))?(?:\s*\([^)]+\))?)",
        meta_text,
        re.IGNORECASE,
    )
    if time_match:
        recipe["time"] = clean_text(time_match.group(1))

    # Parse diet info
    diet_keywords = []
    if re.search(r"\bvegan\b", meta_text, re.IGNORECASE):
        diet_keywords.append("Vegan")
    if re.search(r"\bvegetarian\b", meta_text, re.IGNORECASE):
        diet_keywords.append("Vegetarian")
    if re.search(r"\bgluten[- ]?free\b", meta_text, re.IGNORECASE):
        diet_keywords.append("Gluten-Free")
    if diet_keywords:
        recipe["diet"] = ", ".join(diet_keywords)

    # Extract ingredients from all <ul><li> items
    ingredients = []
    for ul in card.find_all("ul"):
        for li in ul.find_all("li", recursive=False):
            text = clean_text(strip_html(str(li)))
            if text:
                ingredients.append(text)
    recipe["ingredients"] = ingredients

    # Extract instructions from all <ol><li> items
    instructions = []
    for ol in card.find_all("ol"):
        for li in ol.find_all("li", recursive=False):
            text = clean_text(strip_html(str(li)))
            if text:
                instructions.append(text)
    recipe["instructions"] = instructions

    if not ingredients and not instructions:
        return None

    return recipe


def yaml_escape(s):
    """Escape a string for YAML double-quoted scalar."""
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    return s


def recipe_to_yaml(recipe):
    """Convert recipe dict to YAML string for front matter."""
    lines = ["recipe:"]
    if "name" in recipe:
        lines.append(f'  name: "{yaml_escape(recipe["name"])}"')
    if "yield" in recipe:
        lines.append(f'  yield: "{yaml_escape(recipe["yield"])}"')
    if recipe.get("ingredients"):
        lines.append("  ingredients:")
        for ing in recipe["ingredients"]:
            lines.append(f'    - "{yaml_escape(ing)}"')
    if recipe.get("instructions"):
        lines.append("  instructions:")
        for inst in recipe["instructions"]:
            lines.append(f'    - "{yaml_escape(inst)}"')
    return "\n".join(lines)


def process_post(filepath):
    """Process a single post file. Returns True if modified."""
    text = filepath.read_text(encoding="utf-8")

    # Skip if already has recipe data
    if re.search(r"^recipe:", text, re.MULTILINE):
        return False

    # Check for recipe-card div
    if '<div class="recipe-card">' not in text:
        return False

    # Split front matter and content
    match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not match:
        return False

    front_matter = match.group(1)
    content = match.group(2)

    # Extract the first recipe-card using BeautifulSoup (handles nested divs)
    soup = BeautifulSoup(content, "html.parser")
    card_el = soup.find("div", class_="recipe-card")
    if not card_el:
        return False

    card_html = str(card_el)

    recipe = extract_recipe_from_card(card_html)
    if not recipe:
        return False

    # Add recipe data to front matter
    yaml_block = recipe_to_yaml(recipe)
    new_text = f"---\n{front_matter}\n{yaml_block}\n---\n{content}"
    filepath.write_text(new_text, encoding="utf-8")
    return True


def main():
    posts = sorted(POSTS_DIR.glob("*.md"))
    modified = 0
    skipped = 0
    errors = 0

    for post in posts:
        try:
            if process_post(post):
                modified += 1
                print(f"  + {post.name}")
            else:
                skipped += 1
        except Exception as e:
            errors += 1
            print(f"  ! {post.name}: {e}", file=sys.stderr)

    print(f"\nDone: {modified} modified, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    main()
