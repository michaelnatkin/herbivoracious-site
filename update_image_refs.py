#!/usr/bin/env python3
"""Update all image references from JPG/JPEG/PNG to WebP."""

import os
import re
from pathlib import Path

# Directories with content files
CONTENT_DIRS = ["site/content/posts", "site/content"]
TEMPLATE_FILES = [
    "site/themes/herbivoracious/layouts/_default/baseof.html",
    "site/themes/herbivoracious/layouts/partials/sidebar.html",
    "site/themes/herbivoracious/layouts/partials/cookbook-cta.html",
]

# Only replace references to local image paths
LOCAL_PREFIXES = ("/images/", "/wp-content/")


def replace_local_image_ext(text: str) -> str:
    """Replace .jpg/.jpeg/.png with .webp in local image references only."""

    def replacer(match):
        full = match.group(0)
        # Check if this is a local path
        # Look for src="...", href="...", or cover.image paths
        for prefix in LOCAL_PREFIXES:
            if prefix in full:
                return re.sub(r"\.(jpg|jpeg|png)", ".webp", full, flags=re.IGNORECASE)
        return full

    # Match src="..." and href="..." attributes containing image extensions
    text = re.sub(
        r'(src|href)\s*=\s*"[^"]*\.(jpg|jpeg|png)"',
        replacer,
        text,
        flags=re.IGNORECASE,
    )

    return text


def update_front_matter_cover(text: str) -> str:
    """Update cover.image in YAML front matter."""
    # Match cover image line in front matter
    def replacer(match):
        line = match.group(0)
        for prefix in LOCAL_PREFIXES:
            if prefix in line:
                return re.sub(r"\.(jpg|jpeg|png)", ".webp", line, flags=re.IGNORECASE)
        return line

    return re.sub(
        r"^(\s*image\s*:\s*[\"']?)/[^\s\"']*\.(jpg|jpeg|png)([\"']?)$",
        replacer,
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )


def update_file(filepath: Path) -> bool:
    """Update image references in a single file. Returns True if modified."""
    try:
        original = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return False

    modified = original

    # Update front matter cover images
    if filepath.suffix == ".md":
        modified = update_front_matter_cover(modified)

    # Update inline HTML image references
    modified = replace_local_image_ext(modified)

    if modified != original:
        filepath.write_text(modified, encoding="utf-8")
        return True
    return False


def main():
    total_updated = 0
    total_checked = 0

    # Update content files
    for dir_path in CONTENT_DIRS:
        root = Path(dir_path)
        if not root.exists():
            continue

        if dir_path == "site/content":
            # Only top-level .md files (not posts/ subdirectory again)
            files = sorted(root.glob("*.md"))
        else:
            files = sorted(root.rglob("*.md"))

        print(f"\n{dir_path}: checking {len(files)} files")
        for f in files:
            total_checked += 1
            if update_file(f):
                total_updated += 1

    # Update template files
    print(f"\nTemplates: checking {len(TEMPLATE_FILES)} files")
    for tpl in TEMPLATE_FILES:
        p = Path(tpl)
        total_checked += 1
        if p.exists() and update_file(p):
            total_updated += 1
            print(f"  Updated: {tpl}")
        elif not p.exists():
            print(f"  NOT FOUND: {tpl}")

    print(f"\n{'='*50}")
    print(f"Files checked: {total_checked}")
    print(f"Files updated: {total_updated}")


if __name__ == "__main__":
    main()
