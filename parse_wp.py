#!/usr/bin/env python3
"""Parse WordPress XML export and build content inventory."""

import xml.etree.ElementTree as ET
import re
import json
from collections import defaultdict
from urllib.parse import urlparse, unquote

XML_PATH = '/Users/michael/Downloads/WordPress.2026-02-14.xml'

# WordPress namespaces
NS = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'wp': 'http://wordpress.org/export/1.2/',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

def parse_cdata(text):
    """Extract text from CDATA or plain text."""
    if text is None:
        return ''
    return text.strip()

def extract_links(content):
    """Extract all links from HTML content."""
    if not content:
        return [], []

    # Find all href links
    href_pattern = r'href=["\']([^"\']+)["\']'
    hrefs = re.findall(href_pattern, content)

    # Find all image src
    src_pattern = r'src=["\']([^"\']+)["\']'
    srcs = re.findall(src_pattern, content)

    return hrefs, srcs

def main():
    print("Parsing WordPress XML export...")
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    channel = root.find('channel')

    # Get categories
    categories = {}
    for cat in channel.findall('wp:category', NS):
        term_id = cat.find('wp:term_id', NS).text
        slug = parse_cdata(cat.find('wp:category_nicename', NS).text)
        name = parse_cdata(cat.find('wp:cat_name', NS).text)
        parent = parse_cdata(cat.find('wp:category_parent', NS).text)
        categories[slug] = {'id': term_id, 'name': name, 'parent': parent}

    # Get tags
    tags = {}
    for tag in channel.findall('wp:tag', NS):
        term_id = tag.find('wp:term_id', NS).text
        slug = parse_cdata(tag.find('wp:tag_slug', NS).text)
        name = parse_cdata(tag.find('wp:tag_name', NS).text)
        tags[slug] = {'id': term_id, 'name': name}

    # Parse all items
    posts = []
    pages = []
    attachments = []
    other = []

    all_internal_links = []
    all_image_refs = []

    for item in channel.findall('item'):
        title = parse_cdata(item.find('title').text)
        link = parse_cdata(item.find('link').text)
        pub_date = parse_cdata(item.find('pubDate').text)

        post_id = item.find('wp:post_id', NS)
        post_id = post_id.text if post_id is not None else None

        post_date = item.find('wp:post_date', NS)
        post_date = parse_cdata(post_date.text) if post_date is not None else ''

        post_name = item.find('wp:post_name', NS)
        post_name = parse_cdata(post_name.text) if post_name is not None else ''

        post_type = item.find('wp:post_type', NS)
        post_type = parse_cdata(post_type.text) if post_type is not None else ''

        post_status = item.find('wp:status', NS)
        post_status = parse_cdata(post_status.text) if post_status is not None else ''

        content_elem = item.find('content:encoded', NS)
        content = parse_cdata(content_elem.text) if content_elem is not None else ''

        excerpt_elem = item.find('excerpt:encoded', NS)
        excerpt = parse_cdata(excerpt_elem.text) if excerpt_elem is not None else ''

        # Get categories and tags for this item
        item_cats = []
        item_tags = []
        for cat in item.findall('category'):
            domain = cat.get('domain', '')
            nicename = cat.get('nicename', '')
            if domain == 'category':
                item_cats.append(nicename)
            elif domain == 'post_tag':
                item_tags.append(nicename)

        # Get post meta
        meta = {}
        for pm in item.findall('wp:postmeta', NS):
            key = pm.find('wp:meta_key', NS)
            val = pm.find('wp:meta_value', NS)
            if key is not None and val is not None:
                meta[key.text] = val.text

        # Extract links and images from content
        hrefs, srcs = extract_links(content)

        # Filter for internal links
        for href in hrefs:
            if 'herbivoracious' in href or href.startswith('/'):
                all_internal_links.append({'from_id': post_id, 'from_slug': post_name, 'href': href})

        for src in srcs:
            all_image_refs.append({'from_id': post_id, 'from_slug': post_name, 'src': src})

        record = {
            'id': post_id,
            'title': title,
            'link': link,
            'slug': post_name,
            'date': post_date,
            'status': post_status,
            'categories': item_cats,
            'tags': item_tags,
            'content_length': len(content),
            'has_content': len(content) > 0,
            'meta': meta,
        }

        if post_type == 'post':
            posts.append(record)
        elif post_type == 'page':
            pages.append(record)
        elif post_type == 'attachment':
            record['attachment_url'] = meta.get('_wp_attached_file', '')
            attachments.append(record)
        else:
            record['post_type'] = post_type
            other.append(record)

    # Print summary
    print(f"\n=== CONTENT SUMMARY ===")
    print(f"Posts: {len(posts)}")
    print(f"Pages: {len(pages)}")
    print(f"Attachments: {len(attachments)}")
    print(f"Other: {len(other)}")

    # Posts by status
    print(f"\n=== POSTS BY STATUS ===")
    by_status = defaultdict(int)
    for p in posts:
        by_status[p['status']] += 1
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")

    # Published posts
    published = [p for p in posts if p['status'] == 'publish']
    print(f"\n=== PUBLISHED POSTS: {len(published)} ===")

    # Posts by year
    print(f"\n=== PUBLISHED POSTS BY YEAR ===")
    by_year = defaultdict(int)
    for p in published:
        if p['date']:
            year = p['date'][:4]
            by_year[year] += 1
    for year, count in sorted(by_year.items()):
        print(f"  {year}: {count}")

    # Categories
    print(f"\n=== CATEGORIES ({len(categories)}) ===")
    for slug, info in sorted(categories.items()):
        parent_str = f" (parent: {info['parent']})" if info['parent'] else ""
        print(f"  {info['name']} [{slug}]{parent_str}")

    # Tags
    print(f"\n=== TAGS ({len(tags)}) ===")
    tag_list = sorted(tags.keys())
    print(f"  {', '.join(tag_list[:30])}...")

    # Internal links analysis
    print(f"\n=== INTERNAL LINKS: {len(all_internal_links)} ===")
    link_patterns = defaultdict(int)
    for link in all_internal_links:
        href = link['href']
        # Categorize link patterns
        if '/wp-content/' in href:
            link_patterns['wp-content'] += 1
        elif re.match(r'.*/\d{4}/\d{2}/.*', href):
            link_patterns['date-based (YYYY/MM)'] += 1
        elif '.htm' in href:
            link_patterns['.htm extension'] += 1
        elif '?' in href:
            link_patterns['query string'] += 1
        else:
            link_patterns['other'] += 1

    for pattern, count in sorted(link_patterns.items(), key=lambda x: -x[1]):
        print(f"  {pattern}: {count}")

    # Image refs analysis
    print(f"\n=== IMAGE REFERENCES: {len(all_image_refs)} ===")
    img_patterns = defaultdict(int)
    for ref in all_image_refs:
        src = ref['src']
        if '/wp-content/uploads/' in src:
            img_patterns['wp-content/uploads'] += 1
        elif 'herbivoracious' in src:
            img_patterns['herbivoracious domain'] += 1
        elif src.startswith('http'):
            img_patterns['external'] += 1
        else:
            img_patterns['other/relative'] += 1

    for pattern, count in sorted(img_patterns.items(), key=lambda x: -x[1]):
        print(f"  {pattern}: {count}")

    # Sample some links to understand patterns
    print(f"\n=== SAMPLE INTERNAL LINKS ===")
    seen = set()
    for link in all_internal_links[:100]:
        href = link['href']
        # Normalize
        parsed = urlparse(href)
        path = parsed.path
        if path not in seen and 'wp-content' not in path:
            seen.add(path)
            print(f"  {path}")
        if len(seen) >= 20:
            break

    # Sample image paths
    print(f"\n=== SAMPLE IMAGE PATHS ===")
    seen = set()
    for ref in all_image_refs[:100]:
        src = ref['src']
        if src not in seen:
            seen.add(src)
            print(f"  {src}")
        if len(seen) >= 15:
            break

    # Pages
    print(f"\n=== PAGES ===")
    published_pages = [p for p in pages if p['status'] == 'publish']
    for p in published_pages:
        print(f"  {p['title']} [{p['slug']}]")

    # Save full data for conversion script
    data = {
        'categories': categories,
        'tags': tags,
        'posts': posts,
        'pages': pages,
        'attachments': attachments,
        'internal_links': all_internal_links,
        'image_refs': all_image_refs,
    }

    with open('wp_inventory.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nFull inventory saved to wp_inventory.json")

if __name__ == '__main__':
    main()
