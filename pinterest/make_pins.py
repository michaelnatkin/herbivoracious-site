#!/usr/bin/env python3
"""Pin factory: builds vertical (2:3) Pinterest pin images from recipe posts, plus a Pinterest bulk-upload CSV.

  python3 make_pins.py slug1 slug2 ...        # specific posts (file name without .md)
  python3 make_pins.py --pilot                # a small varied sample
  python3 make_pins.py --all [--limit N]      # every recipe post with a usable photo

Output: site/static/pins/<slug>.jpg  (served at https://herbivoracious.com/pins/<slug>.jpg)
        pinterest/pins.csv           (title, description, link, media URL, board, ...)
Photos >= 800px wide get a full-bleed layout; smaller photos get a framed-card layout so they stay crisp.
"""
import csv, glob, html, os, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(SITE, "static", "pins")
CSV_PATH = os.path.join(ROOT, "pinterest", "pins.csv")
BASE = "https://herbivoracious.com"
W, H = 1000, 1500
CREAM, INK, ACCENT, MUTE = (250, 247, 242), (42, 32, 23), (0, 166, 199), (122, 111, 98)
GEORGIA_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
GEORGIA_I = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"


def front_matter(path):
    t = open(path).read()
    fm = t.split("---")[1] if t.startswith("---") else ""
    body = t.split("---", 2)[2] if t.startswith("---") else t
    get = lambda k: (re.search(r'^%s:\s*"?(.*?)"?\s*$' % k, fm, re.M) or [None, ""])[1]
    cats = re.findall(r'"([^"]+)"', (re.search(r'^categories:\s*\[(.*?)\]', fm, re.M) or [None, ""])[1])
    cover = (re.search(r'cover:\s*\n\s*image:\s*"([^"]+)"', fm) or [None, ""])[1]
    return {"title": html.unescape(get("title")), "date": get("date"), "slug": get("slug"), "desc": html.unescape(get("description")),
            "cats": cats, "cover": cover, "recipe": "recipe:" in fm, "draft": get("draft") == "true", "body": body}


def clean_title(t):
    t = re.sub(r"\s+Recipes?\s*[-–—:].*$", "", t, flags=re.I)
    t = re.sub(r"\s*[-–—]\s*(A )?(Vegetarian |Vegan )?Recipes?\b.*$", "", t, flags=re.I)
    t = re.sub(r"^Recipe:\s*", "", t, flags=re.I)
    return t.replace("\xa0", " ").strip(" -–—")


def source_image(cover):
    """Largest available version of the cover photo: (path, width)."""
    best = (None, 0)
    for c in {cover, re.sub(r"-\d+x\d+(\.\w+)$", r"\1", cover)}:
        p = os.path.join(SITE, "static", c.lstrip("/"))
        if os.path.exists(p):
            try:
                w = Image.open(p).size[0]
                if w > best[1]:
                    best = (p, w)
            except Exception:
                pass
    stem = os.path.splitext(re.sub(r"-\d+x\d+(\.\w+)$", r"\1", os.path.basename(cover)))[0]
    for h in glob.glob(os.path.join(ROOT, "uploads", "**", stem + ".*"), recursive=True):
        try:
            w = Image.open(h).size[0]
            if w > best[1] + 150:
                best = (h, w)
        except Exception:
            pass
    return best


def fit_text(draw, text, font_path, max_w, max_lines, start=84, floor=44, max_h=350):
    for size in range(start, floor - 1, -2):
        f = ImageFont.truetype(font_path, size)
        words, lines, cur = text.split(), [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if draw.textlength(trial, font=f) <= max_w:
                cur = trial
            else:
                lines.append(cur); cur = w
        lines.append(cur)
        if len(lines) <= max_lines and len(lines) * int(size * 1.22) <= max_h and all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f, lines
    return f, lines[:max_lines]


def make_image(src, title, out, tag="VEGETARIAN RECIPE"):
    photo = Image.open(src).convert("RGB")
    pw = photo.size[0]
    canvas = Image.new("RGB", (W, H), CREAM)
    if pw >= 800:                                   # full-bleed photo on top
        ph = ImageOps.fit(photo, (W, 960), Image.LANCZOS, centering=(0.5, 0.5))
        canvas.paste(ph, (0, 0))
        text_top = 960
    else:                                           # small photo: framed card over a blurred, tinted copy
        bg = ImageOps.fit(photo, (W, 960), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
        bg = Image.blend(bg, Image.new("RGB", bg.size, CREAM), 0.35)
        canvas.paste(bg, (0, 0))
        fw = 760; fh = int(photo.size[1] * fw / pw)
        fh = min(fh, 820); card = ImageOps.fit(photo, (fw, fh), Image.LANCZOS)
        pad = 14; frame = Image.new("RGB", (fw + 2 * pad, fh + 2 * pad), (255, 255, 255))
        frame.paste(card, (pad, pad))
        canvas.paste(frame, ((W - frame.size[0]) // 2, (960 - frame.size[1]) // 2))
        text_top = 960
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, text_top, W, H], fill=CREAM)
    d.rectangle([0, text_top, W, text_top + 8], fill=ACCENT)
    tf = ImageFont.truetype(GEORGIA_B, 27)
    tw = sum(d.textlength(ch, font=tf) + 4 for ch in tag) - 4
    x = (W - tw) / 2
    for ch in tag:                                   # letter-spaced tag line
        d.text((x, text_top + 34), ch, font=tf, fill=ACCENT); x += d.textlength(ch, font=tf) + 4
    f, lines = fit_text(d, title, GEORGIA_B, W - 140, 4)
    lh = int(f.size * 1.22); block = lh * len(lines)
    y = text_top + 84 + max(0, (400 - 84 - 80 - block) // 2)
    for l in lines:
        d.text(((W - d.textlength(l, font=f)) / 2, y), l, font=f, fill=INK); y += lh
    sig = ImageFont.truetype(GEORGIA_I, 40); s = "herbivoracious.com"
    d.text(((W - d.textlength(s, font=sig)) / 2, H - 76), s, font=sig, fill=MUTE)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.save(out, "JPEG", quality=86, optimize=True)


BOARDS = [("Desserts", "Vegetarian Desserts"), ("Salads", "Vegetarian Salads"), ("Appetizers", "Vegetarian Appetizers & Snacks"),
          ("Side Dishes", "Vegetarian Side Dishes"), ("Baking", "Vegetarian Baking")]


def board_for(fm):
    t = fm["title"].lower()
    if re.search(r"\b(soup|stew|chowder|broth|chili|dal)\b", t): return "Vegetarian Soups & Stews"
    for cat, name in BOARDS:
        if cat in fm["cats"]: return name
    if "Vegan or Modifiable" in fm["cats"]: return "Vegan & Vegan-Friendly Recipes"
    if "Main Courses" in fm["cats"]: return "Vegetarian Dinner Recipes"
    return "Vegetarian Recipes"


def description_for(fm, title):
    d = fm["desc"]
    if not d:
        para = re.search(r"<p[^>]*>(.+?)</p>|^([A-Za-z].{80,}?)$", re.sub(r"\{\{[^}]*\}\}", "", fm["body"]), re.S | re.M)
        d = re.sub(r"<[^>]+>", " ", (para.group(1) or para.group(2)) if para else "")
        d = html.unescape(re.sub(r"\s+", " ", d)).strip()
    if len(d) > 250: d = d[:247].rsplit(" ", 1)[0] + "…"
    tag = " Vegan or easily modified." if "Vegan or Modifiable" in fm["cats"] else ""
    return f"{d}{tag} Get the full vegetarian recipe at herbivoracious.com."[:500]


def permalink(fm):
    y, m = fm["date"][:4], fm["date"][5:7]
    return f"{BASE}/{y}/{m}/{fm['slug']}/"


def main(args):
    files = {os.path.splitext(os.path.basename(f))[0]: f for f in glob.glob(os.path.join(SITE, "content", "posts", "*.md"))}
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
    if "--pilot" in args:
        want = ["rigatoni-with-roasted-cauliflower-and-spicy-tomato-sauce-recipe", "black-bean-soup-recipe", "kimchi-fried-rice-kimchi-bokkeumbap-recipe",
                "savory-bread-pudding-with-morels-and-beet-greens-recipe", "chickpea-cakes-recipe", "butternut-squash-soup-with-maple-pumpkin-seeds-recipe",
                "irish-soda-bread-recipe", "lemon-cream-pasta-with-cauliflower"]
    elif "--all" in args:
        want = sorted(files)
        if "--best" in args:      # rank recipes by photo size so the sharpest pins come first
            def width(slug):
                fm = front_matter(files[slug])
                return source_image(fm["cover"])[1] if fm["recipe"] and not fm["draft"] and fm["cover"] else 0
            want = sorted(want, key=lambda sl: -width(sl))
    else:
        want = [a for a in args if not a.startswith("--")]
    rows = []
    for slug in want:
        f = files.get(slug)
        if not f: print("missing", slug); continue
        fm = front_matter(f)
        if not fm["recipe"] or fm["draft"] or not fm["cover"]: continue
        src, w = source_image(fm["cover"])
        if not src: continue
        title = clean_title(fm["title"])
        tag = "VEGAN-FRIENDLY RECIPE" if "Vegan or Modifiable" in fm["cats"] else "VEGETARIAN RECIPE"
        make_image(src, title, os.path.join(OUT, f"{slug}.jpg"), tag)
        rows.append({"Title": title[:100], "Description": description_for(fm, title), "Link": permalink(fm) + "?utm_source=pinterest&utm_medium=social&utm_campaign=pins",
                     "Media URL": f"{BASE}/pins/{slug}.jpg", "Pinterest board": board_for(fm), "_src_px": w, "_slug": slug})
        print(f"{slug[:52]:52} photo {w:4}px -> {'full-bleed' if w >= 800 else 'framed'}")
        if limit and len(rows) >= limit: break
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["Title", "Description", "Link", "Media URL", "Pinterest board"], extrasaction="ignore")
        wr.writeheader(); wr.writerows(rows)
    print(len(rows), "pins ->", OUT, "and", CSV_PATH)


if __name__ == "__main__":
    main(sys.argv[1:])
