# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WordPress-to-Hugo migration of herbivoracious.com, a vegetarian food blog with ~616 posts (2007-2013). The site uses a custom Hugo theme ("herbivoracious") with a two-column layout (main content + sidebar). Migration plan is tracked in `/Users/michael/.cursor/plans/herbivoracious_static_migration_030c9c71.plan.md`.

## Commands

```bash
# Run Hugo dev server (from site/ directory)
cd site && hugo server -D

# Build the site
cd site && hugo

# Run the link/image audit
python3 audit.py
```

**Never edit files in `site/public/` directly.** The Hugo dev server watches for changes and rebuilds automatically. Edit source files in `site/themes/herbivoracious/` or `site/content/` instead.

**Never `git push` without explicit permission.** You may commit freely, but always ask before pushing to remote.

## Architecture

```
├── convert.py          # WP XML → Hugo Markdown converter (already run)
├── parse_wp.py         # WordPress XML parser
├── fix_links.py        # Internal link fixer
├── audit.py            # Broken link/image auditor
├── wp_inventory.json   # Full WP content inventory
├── uploads/            # Raw WordPress media files
└── site/               # Hugo site root
    ├── hugo.toml       # Site config (theme, permalinks, taxonomies)
    ├── content/
    │   ├── posts/      # ~616 blog posts (Markdown with HTML content)
    │   └── *.md        # Standalone pages (about, cookbook, etc.)
    ├── static/
    │   ├── images/     # Migrated media (mirrors old WP upload paths)
    │   └── wp-content/ # Legacy path aliases for old image URLs
    └── themes/
        └── herbivoracious/
            ├── layouts/_default/
            │   ├── baseof.html   # Base template (head, header, footer)
            │   ├── list.html     # Homepage + category/tag listings
            │   ├── single.html   # Individual post layout
            │   ├── terms.html    # Taxonomy index (categories, tags)
            │   └── archives.html # Chronological archive
            ├── layouts/partials/
            │   └── sidebar.html  # Sidebar (popular posts, topics list)
            └── static/css/
                └── style.css     # All styles (single file)
```

## Key Design Decisions

- **Permalink structure:** `/:year/:month/:slug/` — matches old WordPress URLs so external links don't break
- **Aliases:** Each post has `aliases` in front matter for old URL patterns (`.html` suffix, alternate slugs)
- **Content format:** Posts are Markdown files but contain raw HTML from WordPress (not pure Markdown)
- **Cover images:** Set via `cover.image` in front matter; used on homepage cards and og:image
- **Fonts:** Google Fonts — Inter (sans-serif, for UI/headings) and Lora (serif, for body text)
- **Theme is custom, not PaperMod:** PaperMod exists in themes/ but is unused. The active theme is `herbivoracious` (set in `hugo.toml`)
- **No build toolchain:** Plain CSS, no preprocessors. Single `style.css` file for all styles.

## Migration Status

Phases completed: export, convert, media. In progress: link fixing, theme refinement. Pending: full audit, deployment.
