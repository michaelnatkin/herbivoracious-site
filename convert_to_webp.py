#!/usr/bin/env python3
"""Convert all JPG/JPEG/PNG images to WebP format."""

import os
import sys
from pathlib import Path
from PIL import Image

DIRS = [
    "site/static/images",
    "site/static/wp-content",
]
EXTENSIONS = {".jpg", ".jpeg", ".png"}
WEBP_QUALITY = 88


def convert_image(src: Path) -> tuple[bool, int, int]:
    """Convert a single image to WebP. Returns (success, original_size, webp_size)."""
    webp_path = src.with_suffix(".webp")
    if webp_path.exists():
        return False, 0, 0

    original_size = src.stat().st_size
    try:
        with Image.open(src) as img:
            # Preserve transparency for PNGs
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            img.save(webp_path, "WEBP", quality=WEBP_QUALITY, method=4)
        webp_size = webp_path.stat().st_size
        return True, original_size, webp_size
    except Exception as e:
        print(f"  ERROR: {src}: {e}", file=sys.stderr)
        if webp_path.exists():
            webp_path.unlink()
        return False, 0, 0


def main():
    total_converted = 0
    total_skipped = 0
    total_errors = 0
    total_original = 0
    total_webp = 0

    for dir_path in DIRS:
        root = Path(dir_path)
        if not root.exists():
            print(f"Skipping {dir_path} (not found)")
            continue

        files = sorted(
            f for f in root.rglob("*") if f.suffix.lower() in EXTENSIONS
        )
        print(f"\n{dir_path}: {len(files)} images to process")

        for i, src in enumerate(files, 1):
            converted, orig_sz, webp_sz = convert_image(src)
            if converted:
                total_converted += 1
                total_original += orig_sz
                total_webp += webp_sz
                savings = (1 - webp_sz / orig_sz) * 100 if orig_sz else 0
                if i % 500 == 0 or i == len(files):
                    print(f"  [{i}/{len(files)}] converted so far...")
            elif orig_sz == 0:
                # Check if it was skipped (already exists) vs error
                if src.with_suffix(".webp").exists():
                    total_skipped += 1
                else:
                    total_errors += 1

    print(f"\n{'='*50}")
    print(f"Converted: {total_converted}")
    print(f"Skipped (already exist): {total_skipped}")
    print(f"Errors: {total_errors}")
    if total_original > 0:
        savings_mb = (total_original - total_webp) / 1024 / 1024
        savings_pct = (1 - total_webp / total_original) * 100
        print(f"Original total: {total_original / 1024 / 1024:.1f} MB")
        print(f"WebP total: {total_webp / 1024 / 1024:.1f} MB")
        print(f"Saved: {savings_mb:.1f} MB ({savings_pct:.1f}%)")


if __name__ == "__main__":
    main()
