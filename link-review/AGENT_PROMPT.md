You are matching products from a vegetarian food blog (herbivoracious.com) to replacement merchants. The blog's Amazon affiliate account was banned, so Amazon links earn nothing. We replace each Amazon link with the same product, or a close equivalent, at a merchant **in the Skimlinks affiliate network** (we earn commission only there).

Repo: /Users/michael/code/herbvivoracious-migration  (do not edit anything except your own output file)

## Your input and output
- Input: `link-review/batches/input-NN.json` — about 20 products. Each has `id`, `name`, `amazon_titles` (the exact Amazon listing title(s); may be empty), `anchors` (the link text used in posts), `is_book`, `links`/`posts` (how much it's used), `example_post`.
- Output: write `link-review/batches/batch-NN.json` (same NN), a JSON array with one object per input product (see format below). Validate it parses before finishing.

## How to match each product
1. Work out exactly what the Amazon link was (titles + anchors). Decide: the same product, or an equivalent/similar one (same kind and quality: a different brand of Spanish smoked paprika, a comparable 8" chef's knife). The owner reviews every match and vetoes bad ones, so showing a reasonable equivalent is better than giving up, but do not force bad matches (use confidence "low" or no_match).
2. Find in-network merchants that carry it. Check network membership and EPC (average earnings per click, US) with:
   - `python3 link-review/merchants.py search "<name or domain fragment>"`
   - `python3 link-review/merchants.py domain <domain.com>`
   - `python3 link-review/merchants.py top "<vertical>" 30`  (e.g. "Food", "Kitchenware")
   The network is broad: it includes many brand-direct shops (HexClad, Misen, Made In, ThermoWorks, OXO, Vitamix, All-Clad, Le Creuset, Lodge, Breville, Ooni, simplehuman…) and specialty food shops (Nuts.com, Savory Spice Shop, The Spice House, iHerb, Thrive Market, Weee!/SayWeee, ChefShop.com, King Arthur Baking, Sur La Table, Restaurant Supply, Barnes & Noble…). It does NOT include Amazon, Walmart, Target, Williams Sonoma, Crate & Barrel, Etsy, eBay. Only use merchants confirmed present by merchants.py.
3. **Pick the merchant with the highest EPC among those that carry the product** (EPC null = no data; use only if nothing better). Provide up to 2 alternatives, best EPC first.
4. Find the real product page URL. **Prefer the merchant's own catalog search** — `python3 link-review/shop_search.py <domain> "<terms>"` — which returns real product URLs for Shopify-style stores (Savory Spice Shop, The Spice House, ChefShop, Nuts.com, Masienda, Lodge, Burlap & Barrel, many brand shops). Use it for the highest-EPC merchants first (it fixes the common problem of guessing URLs). Fall back to WebSearch (standard mode) or WebFetch only when a store isn't searchable that way. Use the plain merchant product URL, never an affiliate redirect or tracking link. A URL returned by shop_search.py counts as `verified: true` (it comes from the merchant's live catalog). For any other URL, one plain check is enough: `curl -s -o /dev/null -L -w "%{http_code}" -A "Mozilla/5.0" "<url>"` — 200 = `verified: true`; 403/429/blocked = `verified: false` (a separate slow checker re-tests these later, so do NOT retry or loop on 403/429); 404 = discard it. Only plain GETs: never add to cart, sign up, or buy. Go easy on each merchant: no more than one request every couple of seconds per host.
5. **Books** (`is_book`): use the Barnes & Noble product page (`https://www.barnesandnoble.com/w/<slug>/<id>`), found by WebSearch. Never a search-style `/w/?ean=` URL. Not Bookshop.org. Match the same edition if you can tell (ISBN is the `asins` entry); otherwise note the edition.
6. If no in-network merchant sells it or anything reasonably equivalent, output `status: "no_match"` with a short `reason`. That's fine and expected for some items (discontinued, obscure, or only sold by Amazon).

## Output format (array of objects)
```json
{
  "id": "<input id>", "name": "<input name>", "status": "match",
  "kind": "same" | "equivalent" | "book",
  "confidence": "high" | "medium" | "low",
  "amazon": {"asins": [...], "title": "<Amazon title or best guess>", "anchors": [...], "links": N, "posts": N, "example_post": "<input example_post>"},
  "primary": {"merchant": "Savory Spice Shop", "product": "Smoked Spanish Sweet Paprika", "url": "https://...", "epc": 0.33, "rate": 15, "price": "$10.95", "verified": true},
  "alternatives": [ {same shape as primary} ],
  "note": "One plain sentence for the blog owner: how this differs from the Amazon item (brand, size), or why it is the same."
}
```
For no_match: `{"id", "name", "status": "no_match", "reason": "...", "amazon": {...as above...}}`. `epc` and `rate` are numbers from merchants.py (or null); `price` may be null.

## Working rules
- Be economical: roughly 5-8 tool calls per product at most; batch your shop_search/curl checks in one Bash call with a short `sleep 2` between calls to the same host.
- Don't change any other file. Don't commit.
- Finish with a short summary: how many match / no_match, and anything systematic the owner should know (e.g. a merchant that blocks verification).
