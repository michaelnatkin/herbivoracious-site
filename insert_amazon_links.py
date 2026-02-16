#!/usr/bin/env python3
"""Insert Amazon affiliate links into Hugo blog posts based on amazon_links.md."""

import re
import os
import unicodedata


LINKS_FILE = "amazon_links.md"
POSTS_DIR = "site/content/posts"


def parse_links_table(filepath):
    """Parse the markdown table and return list of (slug, anchor_text, product, url)."""
    entries = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|") or line.startswith("| Post") or line.startswith("|--"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue
            slug = parts[1]
            anchor = parts[2]
            product = parts[3]
            url = parts[4]
            if url.startswith("https://www.amazon.com/"):
                entries.append((slug, anchor, product, url))
    return entries


def find_post_file(posts_dir, slug):
    """Find the post file matching the slug."""
    direct = os.path.join(posts_dir, slug + ".md")
    if os.path.exists(direct):
        return direct
    for fname in sorted(os.listdir(posts_dir)):
        if fname.startswith(slug) and fname.endswith(".md"):
            return os.path.join(posts_dir, fname)
    return None


def strip_accents(s):
    """Remove accents/diacritics from string."""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.category(c).startswith('M'))


def normalize(s):
    """Normalize for matching: strip accents, normalize quotes."""
    s = strip_accents(s)
    s = re.sub(r'[\u2018\u2019\u201c\u201d\u0060\u00b4\u2032]', "'", s)
    s = s.replace('\u2014', '-').replace('\u2013', '-')
    s = s.replace('\xa0', ' ')  # non-breaking space
    s = s.replace('&nbsp;', ' ')
    return s


def extract_anchor_text(anchor):
    """Extract plain text from anchor, handling markdown link format."""
    m = re.match(r'\[([^\]]+)\]\(.*\)', anchor)
    if m:
        return m.group(1)
    return anchor


def is_inside_tag(content, pos):
    """Check if position is inside an HTML tag."""
    i = pos - 1
    while i >= 0:
        if content[i] == '>':
            return False
        if content[i] == '<':
            return True
        i -= 1
    return False


def is_inside_link(content, pos):
    """Check if position is already inside an <a> tag."""
    before = content[:pos].lower()
    last_a_open = max(before.rfind("<a "), before.rfind("<a\n"), before.rfind("<a>"))
    last_a_close = before.rfind("</a>")
    if last_a_open == -1:
        return False
    return last_a_open > last_a_close


def is_in_front_matter(content, pos):
    """Check if position is in YAML front matter."""
    # Front matter is between first --- and second ---
    first = content.find('---')
    if first == -1:
        return False
    second = content.find('---', first + 3)
    if second == -1:
        return False
    return first <= pos <= second


def build_pos_map(content):
    """Build mapping from normalized positions back to original positions."""
    norm_chars = []
    orig_positions = []
    i = 0
    for ch in content:
        nfkd = unicodedata.normalize('NFKD', ch)
        for c in nfkd:
            if unicodedata.category(c).startswith('M'):
                continue  # skip combining marks
            # Apply same transforms as normalize()
            if c in '\u2018\u2019\u201c\u201d\u0060\u00b4\u2032':
                c = "'"
            elif c == '\u2014' or c == '\u2013':
                c = '-'
            elif c == '\xa0':
                c = ' '
            norm_chars.append(c)
            orig_positions.append(i)
        i += 1
    # Add sentinel for end position
    orig_positions.append(i)
    return ''.join(norm_chars), orig_positions


def try_match(content, norm_content, pos_map, search_text, amazon_url):
    """Try to find search_text and insert link. Returns (new_content, success, original_matched_text)."""
    norm_search = normalize(search_text)
    pattern = re.compile(re.escape(norm_search), re.IGNORECASE)

    for match in pattern.finditer(norm_content):
        ns, ne = match.start(), match.end()
        # Map back to original positions
        start = pos_map[ns]
        end = pos_map[ne] if ne < len(pos_map) else pos_map[-1]
        if is_in_front_matter(content, start):
            continue
        if is_inside_tag(content, start):
            continue
        if is_inside_link(content, start):
            return None, False, "already-linked"
        original_text = content[start:end]
        linked = f'<a href="{amazon_url}">{original_text}</a>'
        return content[:start] + linked + content[end:], True, original_text

    return None, False, None


def generate_search_variants(anchor_text):
    """Generate search variants from anchor text, from most specific to least."""
    variants = [anchor_text]

    # Strip parenthetical content: "asafoetida (hing) powder" -> "asafoetida powder", "asafoetida"
    no_parens = re.sub(r'\s*\([^)]+\)\s*', ' ', anchor_text).strip()
    if no_parens != anchor_text:
        variants.append(no_parens)

    # Try without leading adjectives like "dried", "canned", "fresh", "organic", "pure"
    stripped = re.sub(r'^(dried|canned|fresh|organic|pure|ground|whole|thick|red)\s+', '', anchor_text, flags=re.IGNORECASE)
    if stripped != anchor_text:
        variants.append(stripped)
        # Also strip parens from this
        stripped_no_parens = re.sub(r'\s*\([^)]+\)\s*', ' ', stripped).strip()
        if stripped_no_parens != stripped:
            variants.append(stripped_no_parens)

    # Try just the key product word(s) - last 1-2 words of the anchor
    words = anchor_text.split()
    if len(words) > 2:
        variants.append(' '.join(words[-2:]))
    if len(words) > 1:
        variants.append(words[-1])

    # Try first significant word (skip articles/adjectives)
    skip = {'a', 'an', 'the', 'dried', 'canned', 'fresh', 'organic', 'pure', 'ground', 'whole'}
    for w in words:
        if w.lower() not in skip and len(w) > 3:
            variants.append(w)
            break

    return variants


def insert_link(content, anchor_text, amazon_url):
    """Find anchor_text in content and wrap it in an Amazon link."""
    norm_content, pos_map = build_pos_map(content)
    variants = generate_search_variants(anchor_text)

    seen = set()
    for variant in variants:
        if variant.lower() in seen:
            continue
        seen.add(variant.lower())
        result, ok, matched = try_match(content, norm_content, pos_map, variant, amazon_url)
        if ok:
            return result, True, matched
        if matched == "already-linked":
            return content, False, "already-linked"

    return content, False, "not-found"


def main():
    entries = parse_links_table(LINKS_FILE)
    print(f"Found {len(entries)} posts with Amazon links to insert")

    success = 0
    already_linked = []
    not_found = []
    matched_details = []

    for slug, raw_anchor, product, url in entries:
        anchor = extract_anchor_text(raw_anchor)
        post_file = find_post_file(POSTS_DIR, slug)
        if not post_file:
            not_found.append((slug, f"file not found"))
            continue

        with open(post_file, "r") as f:
            content = f.read()

        new_content, ok, note = insert_link(content, anchor, url)
        if ok:
            with open(post_file, "w") as f:
                f.write(new_content)
            success += 1
            if note != anchor and note.lower() != anchor.lower():
                matched_details.append((slug, anchor, note))
        elif note == "already-linked":
            already_linked.append(slug)
        else:
            not_found.append((slug, f"anchor '{anchor}'"))

    print(f"\nResults: {success} links inserted")
    print(f"  Already linked (skipped): {len(already_linked)}")
    print(f"  Not found: {len(not_found)}")

    if matched_details:
        print(f"\nPartial matches ({len(matched_details)}):")
        for slug, anchor, matched in matched_details:
            print(f"  {slug}: '{anchor}' → matched '{matched}'")

    if already_linked:
        print(f"\nAlready linked ({len(already_linked)}):")
        for slug in already_linked:
            print(f"  {slug}")

    if not_found:
        print(f"\nNot found ({len(not_found)}):")
        for slug, reason in not_found:
            print(f"  {slug}: {reason}")


if __name__ == "__main__":
    main()
