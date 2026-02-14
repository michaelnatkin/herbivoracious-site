#!/usr/bin/env python3
"""Convert WordPress XML export to Hugo Markdown files.

Handles:
- All published posts and pages
- Front matter with categories, tags, dates, slugs
- Internal link fixing (date-based .html → clean URLs)
- Image path normalization
- WordPress shortcode cleanup
- Hugo aliases for old URL patterns
"""

import xml.etree.ElementTree as ET
import re
import os
import html
import json
from datetime import datetime
from urllib.parse import urlparse, unquote
from pathlib import Path

XML_PATH = '/Users/michael/Downloads/WordPress.2026-02-14.xml'
HUGO_DIR = '/Users/michael/code/herbvivoracious-migration/site'
CONTENT_DIR = os.path.join(HUGO_DIR, 'content')
POSTS_DIR = os.path.join(CONTENT_DIR, 'posts')

NS = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'wp': 'http://wordpress.org/export/1.2/',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

# ---- Category name map (slug → nice name) ----
CATEGORY_NAMES = {}
TAG_NAMES = {}

# ---- Build URL maps for link fixing ----
# post_id → { slug, date, post_type }
POST_MAP = {}
# slug → canonical URL
SLUG_TO_URL = {}
# old URL patterns → new URL
REDIRECT_MAP = {}


def clean_text(text):
    """Clean text from CDATA."""
    if text is None:
        return ''
    return text.strip()


def escape_yaml(s):
    """Escape a string for YAML front matter."""
    if not s:
        return '""'
    # If it contains special chars, quote it
    if any(c in s for c in ':#[]{}|>&*!?,\'"\\'):
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return f'"{s}"'


def normalize_internal_link(href):
    """Convert an internal link to Hugo's canonical URL format."""
    # Strip domain
    path = href
    for prefix in [
        'https://www.herbivoracious.com',
        'http://www.herbivoracious.com',
        'https://herbivoracious.com',
        'http://herbivoracious.com',
    ]:
        if path.lower().startswith(prefix):
            path = path[len(prefix):]
            break

    if not path.startswith('/'):
        return href  # External link, leave alone

    # Don't touch image links
    if path.startswith('/images/'):
        return path

    # Don't touch anchor-only links
    if path.startswith('/#'):
        return path

    # Handle query strings - strip them for internal links
    if '?' in path:
        path = path.split('?')[0]

    # Strip .html / .htm extension
    path = re.sub(r'\.html?$', '', path)

    # Ensure trailing slash for clean URLs
    if path and not path.endswith('/') and '.' not in path.split('/')[-1]:
        path = path + '/'

    # Normalize double slashes
    path = re.sub(r'/+', '/', path)

    return path


def fix_image_src(src):
    """Normalize image source paths."""
    # Strip domain from herbivoracious URLs
    for prefix in [
        'https://www.herbivoracious.com',
        'http://www.herbivoracious.com',
        'https://herbivoracious.com',
        'http://herbivoracious.com',
    ]:
        if src.lower().startswith(prefix):
            src = src[len(prefix):]
            break

    # Fix wp-content/uploads references to /images/ if applicable
    if '/wp-content/uploads/' in src:
        # These are rare (only 3) - keep as-is, they might be different files
        pass

    return src


def clean_shortcodes(content):
    """Remove or convert WordPress shortcodes."""
    if not content:
        return ''

    # Remove [caption] shortcodes but keep the image and caption text
    # [caption id="..." align="..." width="..."]<img .../>Caption text[/caption]
    def replace_caption(m):
        inner = m.group(1)
        # Extract the img tag and caption text
        img_match = re.search(r'(<img[^>]+>)', inner)
        img = img_match.group(1) if img_match else ''
        # Caption text is whatever follows the img tag
        caption = re.sub(r'<img[^>]+>', '', inner).strip()
        if caption and img:
            return f'<figure>{img}<figcaption>{caption}</figcaption></figure>'
        return img or inner

    content = re.sub(r'\[caption[^\]]*\](.*?)\[/caption\]', replace_caption, content, flags=re.DOTALL)

    # Remove [gallery] shortcodes
    content = re.sub(r'\[gallery[^\]]*\]', '', content)

    # Remove ad insertion shortcodes
    content = re.sub(r'\[ad[^\]]*\]', '', content)
    content = re.sub(r'\[insertable_ad[^\]]*\]', '', content)

    # Remove social sharing shortcodes
    content = re.sub(r'\[share[^\]]*\]', '', content)
    content = re.sub(r'\[sociallocker[^\]]*\].*?\[/sociallocker\]', '', content, flags=re.DOTALL)

    # Remove any remaining unknown shortcodes
    content = re.sub(r'\[/?[a-zA-Z_]+[^\]]*\]', '', content)

    return content


def fix_content_links(content):
    """Fix all internal links and image references in HTML content."""
    if not content:
        return ''

    # Fix href links
    def fix_href(m):
        prefix = m.group(1)  # href=" or href='
        url = m.group(2)
        suffix = m.group(3)  # closing quote

        new_url = normalize_internal_link(url)
        return f'{prefix}{new_url}{suffix}'

    content = re.sub(
        r'''(href=["'])([^"']+)(["'])''',
        fix_href,
        content
    )

    # Fix image src
    def fix_src(m):
        prefix = m.group(1)
        url = m.group(2)
        suffix = m.group(3)
        new_url = fix_image_src(url)
        return f'{prefix}{new_url}{suffix}'

    content = re.sub(
        r'''(src=["'])([^"']+)(["'])''',
        fix_src,
        content
    )

    return content


def wp_html_to_clean_html(content):
    """Clean up WordPress HTML quirks."""
    if not content:
        return ''

    # WordPress uses double newlines as paragraph breaks in some cases
    # But most content is already wrapped in <p> tags

    # Remove empty paragraphs
    content = re.sub(r'<p[^>]*>\s*</p>', '', content)
    content = re.sub(r'<p[^>]*>&nbsp;</p>', '', content)

    # Clean up excessive whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Remove Word-specific style cruft
    content = re.sub(r' style="margin: 0in 0in 0pt;"', '', content)
    content = re.sub(r' class="Recipe\w+"', '', content)
    content = re.sub(r' class="MsoNormal"', '', content)
    content = re.sub(r' face="Times New Roman"', '', content)

    # Clean up span tags that only had removed attributes
    content = re.sub(r'<span>([^<]*)</span>', r'\1', content)

    # Remove PayPal buttons and forms
    content = re.sub(r'<form[^>]*paypal[^>]*>.*?</form>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Remove tracking pixels
    content = re.sub(r'<img[^>]*pixel[^>]*/?>',  '', content, flags=re.IGNORECASE)
    content = re.sub(r'<img[^>]*1x1[^>]*/?>',  '', content, flags=re.IGNORECASE)
    content = re.sub(r'<img[^>]*width="1"[^>]*height="1"[^>]*/?>',  '', content, flags=re.IGNORECASE)

    # Remove Amazon associate tracking images (invisible pixel imgs)
    content = re.sub(r'<img[^>]*assoc-amazon[^>]*/?>',  '', content, flags=re.IGNORECASE)
    content = re.sub(r'<img[^>]*ir\?t=[^>]*/?>',  '', content, flags=re.IGNORECASE)

    return content.strip()


def compute_aliases(slug, date_str):
    """Compute Hugo aliases for old URL patterns so external links still work."""
    aliases = []
    if not date_str:
        return aliases

    try:
        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
    except (ValueError, IndexError):
        return aliases

    year = dt.strftime('%Y')
    month = dt.strftime('%m')

    # Old pattern: /YYYY/MM/slug.html
    aliases.append(f'/{year}/{month}/{slug}.html')

    # Some had just the slug with no date
    # Only add if the slug is unique enough (we'll handle collisions)

    return aliases


def build_index():
    """First pass: build complete index of all content for link resolution."""
    print("Building content index...")
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    channel = root.find('channel')

    # Get category names
    for cat in channel.findall('wp:category', NS):
        slug = clean_text(cat.find('wp:category_nicename', NS).text)
        name = clean_text(cat.find('wp:cat_name', NS).text)
        CATEGORY_NAMES[slug] = name

    # Get tag names
    for tag in channel.findall('wp:tag', NS):
        slug = clean_text(tag.find('wp:tag_slug', NS).text)
        name = clean_text(tag.find('wp:tag_name', NS).text)
        TAG_NAMES[slug] = name

    for item in channel.findall('item'):
        post_id = item.find('wp:post_id', NS)
        post_id = clean_text(post_id.text) if post_id is not None else None

        slug = item.find('wp:post_name', NS)
        slug = clean_text(slug.text) if slug is not None else ''

        post_type = item.find('wp:post_type', NS)
        post_type = clean_text(post_type.text) if post_type is not None else ''

        status = item.find('wp:status', NS)
        status = clean_text(status.text) if status is not None else ''

        post_date = item.find('wp:post_date', NS)
        post_date = clean_text(post_date.text) if post_date is not None else ''

        if status != 'publish' or not slug:
            continue

        POST_MAP[post_id] = {
            'slug': slug,
            'date': post_date,
            'post_type': post_type,
        }

        if post_type == 'post' and post_date:
            try:
                dt = datetime.strptime(post_date[:10], '%Y-%m-%d')
                canonical = f'/{dt.year}/{dt.month:02d}/{slug}/'
                SLUG_TO_URL[slug] = canonical

                # Map old URL patterns to canonical
                REDIRECT_MAP[f'/{dt.year}/{dt.month:02d}/{slug}.html'] = canonical
                REDIRECT_MAP[f'/{dt.year}/{dt.month:02d}/{slug}'] = canonical
                REDIRECT_MAP[f'/{slug}'] = canonical
                REDIRECT_MAP[f'/{slug}/'] = canonical
            except ValueError:
                pass
        elif post_type == 'page':
            canonical = f'/{slug}/'
            SLUG_TO_URL[slug] = canonical

    print(f"  Indexed {len(POST_MAP)} published items")
    print(f"  {len(SLUG_TO_URL)} slug→URL mappings")
    print(f"  {len(REDIRECT_MAP)} redirect mappings")


def convert_posts():
    """Convert all WordPress posts to Hugo Markdown."""
    print("\nConverting posts...")
    os.makedirs(POSTS_DIR, exist_ok=True)

    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    channel = root.find('channel')

    count = 0
    skipped = 0

    for item in channel.findall('item'):
        post_type = item.find('wp:post_type', NS)
        if post_type is None or clean_text(post_type.text) != 'post':
            continue

        status = item.find('wp:status', NS)
        if status is None or clean_text(status.text) != 'publish':
            skipped += 1
            continue

        title = clean_text(item.find('title').text)
        slug = clean_text(item.find('wp:post_name', NS).text)
        post_date = clean_text(item.find('wp:post_date', NS).text)

        content_elem = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
        content = clean_text(content_elem.text) if content_elem is not None else ''

        excerpt_elem = item.find('{http://wordpress.org/export/1.2/excerpt/}encoded')
        excerpt = clean_text(excerpt_elem.text) if excerpt_elem is not None else ''

        if not slug or not post_date:
            skipped += 1
            continue

        # Get categories and tags
        cats = []
        post_tags = []
        for cat in item.findall('category'):
            domain = cat.get('domain', '')
            nicename = cat.get('nicename', '')
            display_name = clean_text(cat.text)
            if domain == 'category' and nicename != 'uncategorized':
                cats.append(display_name)
            elif domain == 'post_tag':
                post_tags.append(display_name)

        # Get featured image from post meta
        meta = {}
        for pm in item.findall('wp:postmeta', NS):
            key = pm.find('wp:meta_key', NS)
            val = pm.find('wp:meta_value', NS)
            if key is not None and val is not None:
                meta[key.text] = val.text

        # Process content
        content = clean_shortcodes(content)
        content = fix_content_links(content)
        content = wp_html_to_clean_html(content)

        # Compute aliases
        aliases = compute_aliases(slug, post_date)

        # Build front matter
        try:
            dt = datetime.strptime(post_date, '%Y-%m-%d %H:%M:%S')
            date_iso = dt.strftime('%Y-%m-%dT%H:%M:%S')
        except ValueError:
            date_iso = post_date

        fm_lines = [
            '---',
            f'title: {escape_yaml(title)}',
            f'date: {date_iso}',
            f'slug: {escape_yaml(slug)}',
        ]

        if excerpt:
            fm_lines.append(f'description: {escape_yaml(excerpt)}')

        if cats:
            cat_yaml = ', '.join(escape_yaml(c) for c in cats)
            fm_lines.append(f'categories: [{cat_yaml}]')

        if post_tags:
            tag_yaml = ', '.join(escape_yaml(t) for t in post_tags)
            fm_lines.append(f'tags: [{tag_yaml}]')

        if aliases:
            alias_yaml = ', '.join(f'"{a}"' for a in aliases)
            fm_lines.append(f'aliases: [{alias_yaml}]')

        # Try to find a cover image in the content
        first_img = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
        if first_img:
            cover_src = first_img.group(1)
            if cover_src.startswith('/images/'):
                fm_lines.append(f'cover:')
                fm_lines.append(f'  image: "{cover_src}"')
                fm_lines.append(f'  hidden: true')

        fm_lines.append('---')

        front_matter = '\n'.join(fm_lines)

        # Write the file
        filename = f'{slug}.md'
        filepath = os.path.join(POSTS_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(front_matter)
            f.write('\n\n')
            f.write(content)
            f.write('\n')

        count += 1

    print(f"  Converted {count} posts (skipped {skipped})")
    return count


def convert_pages():
    """Convert WordPress pages to Hugo content."""
    print("\nConverting pages...")

    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    channel = root.find('channel')

    # Pages to skip (commercial, test, duplicate)
    SKIP_SLUGS = {
        'cart', 'checkout', 'my-account', 'store', 'shop',
        'insertable-ad', 'mjntest', 'testfo', 'font-test', 'blah',
        'test-category',
        # Duplicate cookbook pages
        'get-the-herbivoracious-cookbook-2',
        'get-the-herbivoracious-cookbook-3',
        'get-the-herbivoracious-cookbook-4',
        'get-the-herbivoracious-cookbook-5',
        'get-the-herbivoracious-cookbook-6',
        'get-the-herbivoracious-cookbook-ctn',
        'get-the-herbivoracious-cookbook-and-support-city-fruit',
        'get-the-herbivoracious-cookbook-and-support-growfood-and-viva-farms',
        'advertising-on-herbivoracious',
        'sign-up-for-email-updates',
        'thank-you-for-subscribing',
        'hire-me',
    }

    count = 0
    skipped = 0

    for item in channel.findall('item'):
        post_type = item.find('wp:post_type', NS)
        if post_type is None or clean_text(post_type.text) != 'page':
            continue

        status = item.find('wp:status', NS)
        if status is None or clean_text(status.text) != 'publish':
            skipped += 1
            continue

        title = clean_text(item.find('title').text)
        slug = clean_text(item.find('wp:post_name', NS).text)
        post_date = clean_text(item.find('wp:post_date', NS).text)

        if not slug:
            skipped += 1
            continue

        if slug in SKIP_SLUGS:
            skipped += 1
            continue

        content_elem = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
        content = clean_text(content_elem.text) if content_elem is not None else ''

        # Skip pages with no real content
        if len(content) < 50:
            skipped += 1
            continue

        # Process content
        content = clean_shortcodes(content)
        content = fix_content_links(content)
        content = wp_html_to_clean_html(content)

        # Build front matter
        try:
            dt = datetime.strptime(post_date, '%Y-%m-%d %H:%M:%S')
            date_iso = dt.strftime('%Y-%m-%dT%H:%M:%S')
        except ValueError:
            date_iso = post_date

        # Special handling for known pages
        layout = ''
        if slug == 'about':
            layout = 'page'
        elif slug == 'homepage':
            continue  # Homepage is handled by Hugo config

        fm_lines = [
            '---',
            f'title: {escape_yaml(title)}',
            f'date: {date_iso}',
            f'slug: {escape_yaml(slug)}',
        ]

        if layout:
            fm_lines.append(f'layout: "{layout}"')

        fm_lines.append('---')

        front_matter = '\n'.join(fm_lines)

        # Write page file - pages go directly in content/
        filepath = os.path.join(CONTENT_DIR, f'{slug}.md')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(front_matter)
            f.write('\n\n')
            f.write(content)
            f.write('\n')

        count += 1

    print(f"  Converted {count} pages (skipped {skipped})")
    return count


def create_section_index():
    """Create _index.md for the posts section."""
    filepath = os.path.join(POSTS_DIR, '_index.md')
    with open(filepath, 'w') as f:
        f.write('---\n')
        f.write('title: "All Posts"\n')
        f.write('---\n')
    print("Created posts section index")


def main():
    print("=" * 60)
    print("WordPress → Hugo Conversion")
    print("=" * 60)

    # Phase 1: Build complete index
    build_index()

    # Phase 2: Convert content
    post_count = convert_posts()
    page_count = convert_pages()

    # Phase 3: Create section indexes
    create_section_index()

    print(f"\n{'=' * 60}")
    print(f"DONE: {post_count} posts, {page_count} pages")
    print(f"Output: {CONTENT_DIR}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
