#!/usr/bin/env python3
"""Restore ZLRecipe data to migrated Hugo posts.

Parses the wp_amd_zlrecipe_recipes table from the MySQL dump,
maps recipes to Hugo post files via the WordPress XML export,
and appends formatted recipe cards to each post.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

SQL_PATH = '/Users/michael/Downloads/localhost.sql'
XML_PATH = '/Users/michael/Downloads/WordPress.2026-02-14.xml'
POSTS_DIR = Path('/Users/michael/code/herbvivoracious-migration/site/content/posts')

NS = {
    'wp': 'http://wordpress.org/export/1.2/',
}


def parse_sql_recipes(sql_path):
    """Parse ZLRecipe INSERT statement from SQL dump."""
    with open(sql_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the INSERT statement for zlrecipe
    # Can't use simple .*?; because semicolons appear inside string values
    start_match = re.search(
        r"INSERT INTO `wp_amd_zlrecipe_recipes`.*?VALUES\s*\n",
        content,
        re.DOTALL
    )
    if not start_match:
        print("ERROR: Could not find zlrecipe INSERT in SQL dump")
        return []

    values_start = start_match.end()
    # The INSERT ends with ');\n' — find it by searching for ');' followed by newline
    end_pos = content.find(');\n', values_start)
    if end_pos == -1:
        end_pos = content.find(');', values_start)
    if end_pos == -1:
        print("ERROR: Could not find end of zlrecipe INSERT")
        return []

    values_str = content[values_start:end_pos + 1]  # include the closing ')'

    # Parse each row tuple. The format is: (id, post_id, 'title', 'image', 'summary', 'rating', 'prep', 'cook', 'total', 'yield', 'serving', 'cal', 'fat', 'ingredients', 'instructions', 'notes', 'created')
    # We need to carefully parse SQL string values that may contain escaped quotes
    recipes = []
    # Split on row boundaries: "),\n(" or just the rows
    # Use a state machine to parse SQL values properly
    i = 0
    while i < len(values_str):
        # Find start of a row
        paren_start = values_str.find('(', i)
        if paren_start == -1:
            break

        # Parse fields within the parentheses
        fields = []
        j = paren_start + 1
        while True:
            # Skip whitespace
            while j < len(values_str) and values_str[j] in ' \t\n\r':
                j += 1

            if j >= len(values_str):
                break

            if values_str[j] == ')':
                j += 1
                break
            elif values_str[j] == ',':
                j += 1
                continue
            elif values_str[j] == "'":
                # Parse quoted string
                j += 1
                val = []
                while j < len(values_str):
                    if values_str[j] == '\\' and j + 1 < len(values_str):
                        next_char = values_str[j + 1]
                        if next_char == "'":
                            val.append("'")
                            j += 2
                        elif next_char == '\\':
                            val.append('\\')
                            j += 2
                        elif next_char == 'r':
                            val.append('\r')
                            j += 2
                        elif next_char == 'n':
                            val.append('\n')
                            j += 2
                        elif next_char == 't':
                            val.append('\t')
                            j += 2
                        else:
                            val.append(next_char)
                            j += 2
                    elif values_str[j] == "'" and j + 1 < len(values_str) and values_str[j + 1] == "'":
                        val.append("'")
                        j += 2
                    elif values_str[j] == "'":
                        j += 1
                        break
                    else:
                        val.append(values_str[j])
                        j += 1
                fields.append(''.join(val))
            else:
                # Parse unquoted value (number or NULL)
                end = j
                while end < len(values_str) and values_str[end] not in ',)':
                    end += 1
                fields.append(values_str[j:end].strip())
                j = end

        if len(fields) >= 17:
            recipes.append({
                'recipe_id': int(fields[0]),
                'post_id': int(fields[1]),
                'recipe_title': fields[2],
                'recipe_image': fields[3],
                'summary': fields[4],
                'prep_time': fields[6],
                'cook_time': fields[7],
                'total_time': fields[8],
                'yield': fields[9],
                'ingredients': fields[13],
                'instructions': fields[14],
                'notes': fields[15],
            })

        i = j

    return recipes


def build_postid_to_slug(xml_path):
    """Map WordPress post_id to slug from the XML export."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    channel = root.find('channel')

    mapping = {}
    for item in channel.findall('item'):
        post_id_el = item.find('wp:post_id', NS)
        slug_el = item.find('wp:post_name', NS)
        status_el = item.find('wp:status', NS)

        if post_id_el is None or slug_el is None:
            continue

        post_id = post_id_el.text.strip() if post_id_el.text else ''
        slug = slug_el.text.strip() if slug_el.text else ''
        status = status_el.text.strip() if status_el is not None and status_el.text else ''

        if post_id and slug and status == 'publish':
            mapping[int(post_id)] = slug

    return mapping


def parse_duration(iso_dur):
    """Convert ISO 8601 duration (e.g. PT1H30M) to human-readable string."""
    if not iso_dur:
        return ''

    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_dur)
    if not match:
        return iso_dur

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)

    parts = []
    if hours == 1:
        parts.append('1 hr')
    elif hours > 1:
        parts.append(f'{hours} hrs')

    if minutes:
        parts.append(f'{minutes} min')

    return ' '.join(parts) if parts else ''


def convert_links(text):
    """Convert [text|url] link syntax to HTML <a> tags."""
    return re.sub(
        r'\[([^|\]]+)\|([^\]]+)\]',
        r'<a href="\2">\1</a>',
        text
    )


def parse_recipe_list(text, ordered=False):
    """Parse ingredient/instruction text into HTML list with section headers.

    Lines starting with ! are section headers.
    Regular lines are list items.
    """
    if not text:
        return ''

    # Normalize line endings and split
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')

    html_parts = []
    in_list = False
    tag = 'ol' if ordered else 'ul'

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for italic notes like _Note: ..._
        if line.startswith('_') and line.endswith('_'):
            if in_list:
                html_parts.append(f'</{tag}>')
                in_list = False
            html_parts.append(f'<p><em>{convert_links(line[1:-1])}</em></p>')
            continue

        # Section header
        if line.startswith('!'):
            if in_list:
                html_parts.append(f'</{tag}>')
                in_list = False
            header = line[1:].strip()
            html_parts.append(f'<h4>{convert_links(header)}</h4>')
            continue

        # Regular list item
        if not in_list:
            html_parts.append(f'<{tag}>')
            in_list = True
        html_parts.append(f'  <li>{convert_links(line)}</li>')

    if in_list:
        html_parts.append(f'</{tag}>')

    return '\n'.join(html_parts)


def build_recipe_html(recipe):
    """Generate the recipe card HTML for a single recipe."""
    parts = []
    parts.append('<div class="recipe-card">')

    # Title
    parts.append(f'  <h2 class="recipe-card-title">{recipe["recipe_title"]}</h2>')

    # Meta (times + yield)
    meta_items = []
    prep = parse_duration(recipe['prep_time'])
    cook = parse_duration(recipe['cook_time'])
    total = parse_duration(recipe['total_time'])

    if prep:
        meta_items.append(f'<span>Prep: {prep}</span>')
    if cook:
        meta_items.append(f'<span>Cook: {cook}</span>')
    if total:
        meta_items.append(f'<span>Total: {total}</span>')

    if meta_items or recipe['yield']:
        parts.append('  <div class="recipe-card-meta">')
        if meta_items:
            parts.append(f'    {" | ".join(meta_items)}')
        if recipe['yield']:
            if meta_items:
                parts.append(f'    <br>Yield: {recipe["yield"]}')
            else:
                parts.append(f'    Yield: {recipe["yield"]}')
        parts.append('  </div>')

    # Summary
    if recipe['summary']:
        parts.append(f'  <div class="recipe-card-summary"><p>{convert_links(recipe["summary"])}</p></div>')

    # Ingredients
    ingredients_html = parse_recipe_list(recipe['ingredients'], ordered=False)
    if ingredients_html:
        parts.append('  <h3>Ingredients</h3>')
        parts.append(f'  {ingredients_html}')

    # Instructions
    instructions_html = parse_recipe_list(recipe['instructions'], ordered=True)
    if instructions_html:
        parts.append('  <h3>Instructions</h3>')
        parts.append(f'  {instructions_html}')

    # Notes
    if recipe['notes']:
        notes = recipe['notes'].replace('\r\n', '\n').replace('\r', '\n').strip()
        if notes:
            parts.append(f'  <div class="recipe-card-notes"><h3>Notes</h3><p>{convert_links(notes)}</p></div>')

    parts.append('</div>')
    return '\n'.join(parts)


def deduplicate_recipes(recipes):
    """When multiple recipes exist for same post_id, keep the last one (most complete)."""
    by_post = {}
    for r in recipes:
        pid = r['post_id']
        if pid not in by_post or r['recipe_id'] > by_post[pid]['recipe_id']:
            by_post[pid] = r
    return list(by_post.values())


def main():
    print("Parsing SQL dump for ZLRecipe data...")
    recipes = parse_sql_recipes(SQL_PATH)
    print(f"  Found {len(recipes)} recipe rows")

    recipes = deduplicate_recipes(recipes)
    print(f"  After deduplication: {len(recipes)} recipes for unique posts")

    print("Building post_id → slug mapping from WordPress XML...")
    postid_to_slug = build_postid_to_slug(XML_PATH)
    print(f"  Mapped {len(postid_to_slug)} published posts")

    patched = 0
    skipped = 0

    for recipe in recipes:
        post_id = recipe['post_id']
        slug = postid_to_slug.get(post_id)

        if not slug:
            print(f"  SKIP: post_id {post_id} not found in XML (recipe: {recipe['recipe_title']})")
            skipped += 1
            continue

        md_file = POSTS_DIR / f'{slug}.md'
        if not md_file.exists():
            print(f"  SKIP: no markdown file for slug '{slug}' (recipe: {recipe['recipe_title']})")
            skipped += 1
            continue

        # Check if recipe card already exists in this file
        existing = md_file.read_text(encoding='utf-8')
        if '<div class="recipe-card">' in existing:
            print(f"  SKIP: recipe card already present in {slug}.md")
            skipped += 1
            continue

        recipe_html = build_recipe_html(recipe)

        # Append recipe card to end of post
        with open(md_file, 'a', encoding='utf-8') as f:
            f.write('\n\n')
            f.write(recipe_html)
            f.write('\n')

        print(f"  PATCHED: {slug}.md ← {recipe['recipe_title']}")
        patched += 1

    print(f"\nDone: {patched} posts patched, {skipped} skipped")


if __name__ == '__main__':
    main()
