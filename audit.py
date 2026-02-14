#!/usr/bin/env python3
"""Audit the built Hugo site for broken internal links and missing images."""

import os
import re
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse, unquote

PUBLIC_DIR = '/Users/michael/code/herbvivoracious-migration/site/public'
STATIC_DIR = '/Users/michael/code/herbvivoracious-migration/site/static'

def find_all_html_files():
    """Find all HTML files in public directory."""
    files = []
    for root, dirs, filenames in os.walk(PUBLIC_DIR):
        for f in filenames:
            if f.endswith('.html'):
                files.append(os.path.join(root, f))
    return files

def extract_links(html_content):
    """Extract all href and src links from HTML."""
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_content)
    srcs = re.findall(r'src=["\']([^"\']+)["\']', html_content)
    return hrefs, srcs

def resolve_path(base_path, link):
    """Resolve a relative or absolute link to a filesystem path."""
    parsed = urlparse(link)

    # Skip external links, mailto, javascript, anchors
    if parsed.scheme in ('http', 'https', 'mailto', 'javascript', ''):
        if parsed.netloc and parsed.netloc not in ('herbivoracious.com', 'www.herbivoracious.com'):
            return None  # External

    if link.startswith('mailto:') or link.startswith('javascript:') or link.startswith('#'):
        return None

    if link.startswith('//'):
        return None  # Protocol-relative external

    path = parsed.path
    if not path or path == '/':
        return None

    # Remove query string and fragment
    path = unquote(path)

    # Make absolute
    if not path.startswith('/'):
        base_dir = os.path.dirname(base_path)
        rel_from_public = os.path.relpath(base_dir, PUBLIC_DIR)
        path = '/' + os.path.join(rel_from_public, path)

    return path

def check_path_exists(path):
    """Check if a path resolves to a file in the public directory."""
    # Try exact path
    full_path = os.path.join(PUBLIC_DIR, path.lstrip('/'))

    if os.path.exists(full_path):
        return True

    # Try with index.html
    index_path = os.path.join(full_path, 'index.html')
    if os.path.exists(index_path):
        return True

    # Try without trailing slash + index.html
    if full_path.endswith('/'):
        if os.path.exists(full_path.rstrip('/') + '/index.html'):
            return True
    else:
        if os.path.exists(full_path + '/index.html'):
            return True

    return False

def main():
    print("Auditing built site...")
    html_files = find_all_html_files()
    print(f"Found {len(html_files)} HTML files")

    broken_links = defaultdict(list)  # path → [(source_file, link)]
    broken_images = defaultdict(list)
    total_internal_links = 0
    total_images = 0

    for html_file in html_files:
        rel_file = os.path.relpath(html_file, PUBLIC_DIR)

        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        hrefs, srcs = extract_links(content)

        for href in hrefs:
            path = resolve_path(html_file, href)
            if path is None:
                continue
            total_internal_links += 1
            if not check_path_exists(path):
                broken_links[path].append(rel_file)

        for src in srcs:
            path = resolve_path(html_file, src)
            if path is None:
                continue
            total_images += 1
            if not check_path_exists(path):
                broken_images[path].append(rel_file)

    print(f"\nChecked {total_internal_links} internal links, {total_images} image references")

    # Report broken links
    print(f"\n=== BROKEN INTERNAL LINKS: {len(broken_links)} unique paths ===")
    # Group by pattern
    by_pattern = defaultdict(list)
    for path, sources in sorted(broken_links.items()):
        if '/images/' in path:
            by_pattern['images'].append((path, sources))
        elif re.match(r'/\d{4}/\d{2}/', path):
            by_pattern['date-based'].append((path, sources))
        else:
            by_pattern['other'].append((path, sources))

    for pattern in ['date-based', 'other', 'images']:
        items = by_pattern.get(pattern, [])
        if items:
            print(f"\n--- {pattern} ({len(items)}) ---")
            for path, sources in items[:30]:
                print(f"  {path}")
                for s in sources[:3]:
                    print(f"    ← {s}")
                if len(sources) > 3:
                    print(f"    ← ...and {len(sources)-3} more")

    # Report broken images
    print(f"\n=== BROKEN IMAGE REFERENCES: {len(broken_images)} unique paths ===")
    for path, sources in sorted(broken_images.items())[:50]:
        print(f"  {path}")
        for s in sources[:2]:
            print(f"    ← {s}")
        if len(sources) > 2:
            print(f"    ← ...and {len(sources)-2} more")

    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total HTML files: {len(html_files)}")
    print(f"Internal links checked: {total_internal_links}")
    print(f"Image refs checked: {total_images}")
    print(f"Broken internal links: {len(broken_links)} unique paths")
    print(f"Broken images: {len(broken_images)} unique paths")

if __name__ == '__main__':
    main()
