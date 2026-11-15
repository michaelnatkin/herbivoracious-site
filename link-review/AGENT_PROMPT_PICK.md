You are choosing replacement products for a vegetarian food blog (herbivoracious.com). The blog's Amazon affiliate account was banned, so each Amazon link is being replaced with the same product, or a close equivalent, at a merchant **in the Skimlinks affiliate network** (we earn commission only there). A script has already searched the merchants' own catalogs; your job is to **pick the best candidate for each product from those saved results. Do not use WebSearch, WebFetch or curl, and do not hit any website** (rate limits and a shared search budget would be harmed). Work only from the files.

Repo: /Users/michael/code/herbvivoracious-migration  (edit nothing except your own output file)

## Files
- Input: `link-review/batches/input-HNN.json` — ~20 products: `id`, `name`, `amazon_titles` (exact Amazon listing title; may be empty), `anchors` (link text in posts), `is_book`, `links`, `posts`, `example_post`, sometimes `owner_note`.
- Candidates: `link-review/.cache/candidates/input-HNN.json` — per product `id`, `terms` (what was searched), and `candidates`: merchants (best EPC first) each with `results` (`title`, `price`, `url`). EPC = average earnings per click; ties go to the higher EPC. `epc: null` means no data (use only if nothing better).
- Output: `link-review/batches/batch-HNN.json` (same HNN) — JSON array, one object per input product. Validate that it parses.

## How to choose
1. Work out exactly what the Amazon link was (titles + anchors). Candidates are raw search hits and often irrelevant (a search for "dried chanterelle" returns dried cranberries). Accept a candidate only if it really is the same product or a sensible equivalent: same ingredient in the same form (whole vs ground, dried vs fresh), comparable tool/brand class. Never pick something that would surprise the reader (a different ingredient, different form, wrong size class).
2. Among acceptable candidates, **prefer the highest EPC**; keep up to 2 other acceptable ones as `alternatives`.
3. Confidence: `"high"` only when it is the same product, or clearly the same ingredient in the same form/size class from a reputable seller. `"medium"` for a reasonable equivalent (different brand, similar item). `"low"` for a stretch. Be honest and conservative: the owner auto-approves "high", so a wrong "high" goes live without review.
4. Books (`is_book`) and anything with no acceptable candidate: output `status: "no_match"` with a short `reason`, and `"needs_web": true` if a non-searchable in-network merchant plausibly sells it (Barnes & Noble for books; Sur La Table, OXO, King Arthur, iHerb, Thrive Market, Weee, Williams-Sonoma-type gear). Use `"needs_web": false` if it is a genuine gap.
5. Candidate URLs come from the merchants' live catalogs, so set `"verified": true`. Use the plain URL given; never add tracking parameters.

## Output format
```json
{
  "id": "<input id>", "name": "<input name>", "status": "match",
  "kind": "same" | "equivalent",
  "confidence": "high" | "medium" | "low",
  "amazon": {"asins": [...], "title": "<amazon title or best guess>", "anchors": [...], "links": N, "posts": N, "example_post": "<input example_post>"},
  "primary": {"merchant": "<merchant name from candidates>", "product": "<candidate title>", "url": "<candidate url>", "epc": <number or null>, "rate": null, "price": "$X or null", "verified": true},
  "alternatives": [ {same shape} ],
  "note": "One plain sentence for the blog owner: how it differs from the Amazon item (brand, size, form), or why it is the same."
}
```
For no_match: `{"id", "name", "status": "no_match", "reason": "...", "needs_web": true|false, "amazon": {...}}`. Honor any `owner_note` in the input.

Finish with a short summary: counts of match / no_match (and how many needs_web), how many "high".
