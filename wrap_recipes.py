#!/usr/bin/env python3
"""
wrap_recipes.py - Wrap recipe sections in .recipe-card divs for Herbivoracious posts.

Finds posts in the "Recipes" category that don't already have a .recipe-card wrapper,
detects the recipe section (typically at the end of the post), and wraps it in
<div class="recipe-card">...</div>.

Usage:
    python3 wrap_recipes.py             # Apply changes
    python3 wrap_recipes.py --dry-run   # Preview without writing
"""

import os
import re
import sys
import glob

POSTS_DIR = "site/content/posts"


def get_front_matter_end(content):
    """Return the index just past the closing --- of front matter."""
    if not content.startswith('---'):
        return 0
    end = content.find('\n---\n', 3)
    if end != -1:
        return end + 5  # past \n---\n
    end = content.find('\n---', 3)
    if end != -1:
        return end + 4  # past \n--- (EOF case)
    return 0


def has_recipes_category(content):
    """Check if front matter includes 'Recipes' in categories."""
    fm_end = content.find('\n---\n', 3)
    if fm_end == -1:
        fm_end = content.find('\n---', 3)
    if fm_end == -1:
        return False
    fm = content[:fm_end]
    return '"Recipes"' in fm or "'Recipes'" in fm


def find_recipe_start(body):
    """
    Find the character position where the recipe section begins.

    Detection: look for a block-starting <strong> tag followed within 500 chars
    by <ul>/<ol> (primary) or <em> (fallback). Returns the last (closest to end)
    valid candidate position, or -1 if none found.
    """
    strong_re = re.compile(r'<strong\b[^>]*>(.*?)</strong>', re.DOTALL | re.IGNORECASE)

    primary = []    # followed by <ul> or <ol>
    secondary = []  # followed by <em> only

    for m in strong_re.finditer(body):
        pos = m.start()

        # --- Block-start check ---
        # The <strong> must begin a block, not be inline within a sentence.
        # Strip back through any opening container tags (<p>, <div>, <span>)
        # to find the true block boundary.
        before = body[max(0, pos - 150):pos]
        while True:
            tag_m = re.search(r'<(?:p|div|span)\b[^>]*>\s*$', before, re.IGNORECASE)
            if tag_m:
                before = before[:tag_m.start()]
            else:
                break

        is_block = False
        if not before.strip() or pos == 0:
            is_block = True
        elif re.search(r'(?:</[a-z][a-z0-9]*[^>]*>|<br\b[^>]*/?>)\s*$', before, re.IGNORECASE):
            is_block = True
        elif re.search(r'\n\s*$', before):
            is_block = True

        if not is_block:
            continue

        # --- Context exclusion ---
        # Skip if inside an unclosed <li> or <a> tag.
        preceding = body[max(0, pos - 300):pos]
        if re.search(r'<li\b[^>]*>(?:(?!</li>).)*$', preceding, re.DOTALL):
            continue
        if re.search(r'<a\b[^>]*>(?:(?!</a>).)*$', preceding, re.DOTALL):
            continue

        # --- Forward check ---
        after = body[m.end():m.end() + 500]
        has_list = bool(re.search(r'<(?:ul|ol)\b', after, re.IGNORECASE))
        has_em = bool(re.search(r'<em\b', after, re.IGNORECASE))

        if has_list:
            primary.append(pos)
        elif has_em:
            secondary.append(pos)

    if primary:
        return primary[-1]
    if secondary:
        return secondary[-1]
    return -1


def adjust_for_container_tags(body, pos):
    """Move start back past any opening container tags wrapping the <strong>."""
    while True:
        before = body[max(0, pos - 100):pos]
        tag_m = re.search(r'<(?:p|div|span)\b[^>]*>\s*$', before, re.IGNORECASE)
        if tag_m:
            pos -= len(before) - tag_m.start()
        else:
            break
    return pos


def process_post(filepath, dry_run=False):
    """
    Process a single post file.

    Returns one of: 'wrapped', 'skipped', 'already_wrapped', 'not_recipe'
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if not has_recipes_category(content):
        return 'not_recipe'

    fm_end = get_front_matter_end(content)
    body = content[fm_end:]

    if 'recipe-card' in body:
        return 'already_wrapped'

    recipe_pos = find_recipe_start(body)
    if recipe_pos == -1:
        return 'skipped'

    # Adjust start position to include wrapping container tags (<p>, <div>, <span>)
    recipe_pos = adjust_for_container_tags(body, recipe_pos)

    # Build the wrapped body
    new_body = (
        body[:recipe_pos]
        + '<div class="recipe-card">\n'
        + body[recipe_pos:].rstrip()
        + '\n</div>\n'
    )

    if not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content[:fm_end] + new_body)

    return 'wrapped'


def main():
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("=== DRY RUN (no files will be modified) ===\n")

    posts = sorted(glob.glob(os.path.join(POSTS_DIR, '*.md')))

    wrapped, skipped, already, not_recipe = [], [], [], []

    for filepath in posts:
        basename = os.path.basename(filepath)
        result = process_post(filepath, dry_run=dry_run)
        if result == 'wrapped':
            wrapped.append(basename)
        elif result == 'skipped':
            skipped.append(basename)
        elif result == 'already_wrapped':
            already.append(basename)
        elif result == 'not_recipe':
            not_recipe.append(basename)

    print(f"Results:")
    print(f"  Wrapped:         {len(wrapped)}")
    print(f"  Already wrapped: {len(already)}")
    print(f"  Skipped:         {len(skipped)}")
    print(f"  Not in Recipes:  {len(not_recipe)}")

    if skipped:
        print(f"\nSkipped posts ({len(skipped)} — no recipe pattern detected):")
        for s in sorted(skipped):
            print(f"  - {s}")

    if wrapped and len(wrapped) <= 20:
        print(f"\nWrapped posts:")
        for w in wrapped:
            print(f"  + {w}")
    elif wrapped:
        print(f"\nFirst 20 wrapped posts:")
        for w in wrapped[:20]:
            print(f"  + {w}")
        print(f"  ... and {len(wrapped) - 20} more")


if __name__ == '__main__':
    main()
