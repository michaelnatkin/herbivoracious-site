#!/usr/bin/env python3
"""Fix remaining broken internal links found by audit.

Issues:
1. Truncated slugs with trailing dashes (TypePad era)
2. Triple dashes in slugs (should be single)
3. Mangled links with text in URL
4. Missing wp-content/uploads images for 2023 post
5. Social plugin image references
6. Links to skipped pages and category URLs
"""

import os
import re
import json
import glob
from pathlib import Path

CONTENT_DIR = '/Users/michael/code/herbvivoracious-migration/site/content'
POSTS_DIR = os.path.join(CONTENT_DIR, 'posts')
STATIC_DIR = '/Users/michael/code/herbvivoracious-migration/site/static'

# Load inventory to build slug map
with open('/Users/michael/code/herbvivoracious-migration/wp_inventory.json') as f:
    inventory = json.load(f)

# Build map: slug → date
slug_to_date = {}
for p in inventory['posts']:
    if p['status'] == 'publish' and p['slug'] and p['date']:
        slug_to_date[p['slug']] = p['date'][:10]

# === Fix 1: Add aliases for broken URL patterns ===
# Map: broken_path → (correct_slug, year_month)
BROKEN_TO_CORRECT = {
    # Trailing dash truncated slugs
    '/2007/07/the-vegetarian-': ('the-vegetarian', '2007/07'),
    '/2007/09/falafel-in-the-': ('falafel-in-the', '2007/09'),
    '/2007/10/phyllo-wrapped-': ('phyllo-wrapped', '2007/10'),
    '/2008/04/calabro---the-b': ('calabro-the-b', '2008/04'),
    '/2008/04/recipe-atayef-': ('recipe-atayef', '2008/04'),
    '/2008/04/recipe-sabich-': ('recipe-sabich', '2008/04'),
    '/2008/05/recipe-sesame-c': ('recipe-sesame-c-1', '2008/05'),
    '/2008/06/the-pink-door-': ('the-pink-door', '2008/06'),
    # Triple-dash slugs (links used ---, actual slugs use -)
    '/2008/10/whats-in-my-pantry-part-1---liquids-by-the-stove': ('whats-in-my-pantry-part-1-liquids-by-the-stove', '2008/10'),
    '/2010/01/the-value-of-acid---making-your-food-pop-part-2': ('the-value-of-acid-making-your-food-pop-part-2', '2010/01'),
    '/2010/02/things-that-go-crunch-in-the-night---making-your-food-pop-part-4': ('things-that-go-crunch-in-the-night-making-your-food-pop-part-4', '2010/02'),
}

def add_alias_to_post(slug, alias):
    """Add an alias to a post's front matter."""
    filepath = os.path.join(POSTS_DIR, f'{slug}.md')
    if not os.path.exists(filepath):
        print(f"  WARNING: Post file not found: {filepath}")
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    if alias in content:
        return False  # Already has this alias

    # Find aliases line or add one
    if 'aliases:' in content:
        # Add to existing aliases
        content = content.replace(
            'aliases: [',
            f'aliases: ["{alias}", ',
        )
    else:
        # Add aliases line before closing ---
        # Find the second ---
        parts = content.split('---', 2)
        if len(parts) >= 3:
            parts[1] = parts[1].rstrip('\n') + f'\naliases: ["{alias}"]\n'
            content = '---'.join(parts)

    with open(filepath, 'w') as f:
        f.write(content)
    return True


def fix_content_in_file(filepath, old_text, new_text):
    """Replace text in a content file."""
    with open(filepath, 'r') as f:
        content = f.read()

    if old_text not in content:
        return False

    content = content.replace(old_text, new_text)
    with open(filepath, 'w') as f:
        f.write(content)
    return True


def main():
    print("Fixing remaining broken links...\n")

    # Fix 1: Add aliases for truncated/mangled slug URLs
    print("=== Adding aliases for broken URL patterns ===")
    for broken_path, (correct_slug, ym) in BROKEN_TO_CORRECT.items():
        # Add various alias patterns
        aliases_added = []
        for suffix in ['', '/', '.html']:
            alias = broken_path + suffix if not broken_path.endswith('/') else broken_path.rstrip('/') + suffix
            if add_alias_to_post(correct_slug, alias):
                aliases_added.append(alias)
        if aliases_added:
            print(f"  {correct_slug}: added {len(aliases_added)} aliases")

    # Fix 2: Fix links that have garbage text appended
    print("\n=== Fixing mangled links in content ===")
    # /2012/06/.../bit.ly/herbivor → remove the bit.ly part
    for md_file in glob.glob(os.path.join(POSTS_DIR, '*.md')):
        with open(md_file, 'r') as f:
            content = f.read()

        changed = False
        # Fix bit.ly garbage in href
        new_content = re.sub(
            r'(href="[^"]+)/bit\.ly/[^"]*"',
            r'\1"',
            content
        )
        if new_content != content:
            changed = True
            content = new_content

        # Fix links with spaces/text in URL (Onion Pakora issue)
        new_content = re.sub(
            r'href="(/[^"]*?)(?:\s+[A-Z][^"]*)"',
            r'href="\1"',
            content
        )
        if new_content != content:
            changed = True
            content = new_content

        # Fix links with "Caribbean Lentil..." text in href
        new_content = re.sub(
            r'href="(/[^"]*?)(?:Caribbean[^"]*|Hey Nikki[^"]*)"',
            r'href="\1"',
            content
        )
        if new_content != content:
            changed = True
            content = new_content

        # Remove social sharing plugin images
        new_content = re.sub(
            r'<img[^>]*social-sharing-toolkit[^>]*/?>',
            '',
            content,
            flags=re.IGNORECASE
        )
        if new_content != content:
            changed = True
            content = new_content

        # Remove wp-admin links
        new_content = re.sub(
            r'<a[^>]*wp-admin[^>]*>.*?</a>',
            '',
            content,
            flags=re.IGNORECASE | re.DOTALL
        )
        if new_content != content:
            changed = True
            content = new_content

        if changed:
            with open(md_file, 'w') as f:
                f.write(content)
            print(f"  Fixed: {os.path.basename(md_file)}")

    # Fix 3: Handle wp-content/uploads images for the 2023 post
    print("\n=== Fixing wp-content/uploads image paths ===")
    uploads_src = '/Users/michael/code/herbvivoracious-migration/uploads/uploads'
    wp_content_dest = os.path.join(STATIC_DIR, 'wp-content', 'uploads')

    # Copy 2023 uploads
    src_2023 = os.path.join(uploads_src, '2023')
    if os.path.exists(src_2023):
        dest_2023 = os.path.join(wp_content_dest, '2023')
        os.makedirs(dest_2023, exist_ok=True)
        import shutil
        shutil.copytree(src_2023, dest_2023, dirs_exist_ok=True)
        print(f"  Copied 2023 uploads to {dest_2023}")

    # Fix 4: Add redirect pages for category/section URLs that are now different
    print("\n=== Creating redirect pages for old WordPress category URLs ===")

    # /cooking-internship/ → /categories/cooking-internship/
    # /recipes/ → /categories/recipes/
    # /recipes/favorites/ → /categories/favorites/
    # /restaurants/ → /categories/restaurants/
    # /videos/ → /categories/cooking-videos/
    # /vegan/ → /categories/vegan-or-modifiable/
    # /blog/ → /posts/

    redirects = {
        'cooking-internship': '/categories/cooking-internship/',
        'cookbook-project': '/categories/cookbook-project/',
        'recipes': '/categories/recipes/',
        'restaurants': '/categories/restaurants/',
        'videos': '/categories/cooking-videos/',
        'vegan': '/categories/vegan-or-modifiable/',
    }

    for slug, target in redirects.items():
        filepath = os.path.join(CONTENT_DIR, f'{slug}.md')
        # Only create if it doesn't already exist as a page
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write(f'---\ntitle: "{slug}"\naliases: ["/{slug}/"]\nredirectTo: "{target}"\nurl: "{target}"\n---\n')
            print(f"  Created redirect: /{slug}/ → {target}")

    # Create /blog/ redirect
    blog_path = os.path.join(CONTENT_DIR, 'blog.md')
    if not os.path.exists(blog_path):
        with open(blog_path, 'w') as f:
            f.write('---\ntitle: "Blog"\naliases: ["/blog/"]\nurl: "/posts/"\n---\n')
        print("  Created redirect: /blog/ → /posts/")

    # Create /feed/ redirect
    feed_path = os.path.join(CONTENT_DIR, 'feed.md')
    if not os.path.exists(feed_path):
        with open(feed_path, 'w') as f:
            f.write('---\ntitle: "RSS Feed"\naliases: ["/feed/", "/feed"]\nurl: "/index.xml"\n---\n')
        print("  Created redirect: /feed/ → /index.xml")

    # Fix 5: Some posts link to pages that have .html suffix in date pattern
    # /2011/06/chickpea-and-potato-stew-with-baharat-recipe.html
    # /2011/07/vegetarian-frijoles-charros-mexican-cowboy-beans-with-smoked-onion-recipe.html
    # These should already have aliases from the conversion, let me check
    print("\n=== Checking .html alias coverage ===")
    for slug, date in slug_to_date.items():
        year, month = date[:4], date[5:7]
        html_alias = f'/{year}/{month}/{slug}.html'
        filepath = os.path.join(POSTS_DIR, f'{slug}.md')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            if html_alias not in content:
                # Missing .html alias
                if add_alias_to_post(slug, html_alias):
                    pass  # Silently add missing aliases

    # Fix some that link to page slugs that are actually posts
    # /mexican-torta-... is a post, not a page
    # /saffron-chickpea-stew-... is a post, not a page
    print("\n=== Adding page-style aliases for posts ===")
    for p in inventory['posts']:
        if p['status'] == 'publish' and p['slug'] and p['date']:
            slug = p['slug']
            # Add bare slug alias (without date) for posts that are linked that way
            page_alias = f'/{slug}/'
            filepath = os.path.join(POSTS_DIR, f'{slug}.md')
            if os.path.exists(filepath):
                add_alias_to_post(slug, page_alias)

    print("\nDone fixing links!")


if __name__ == '__main__':
    main()
