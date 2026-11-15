"""Builds matches.json for the review page from amazon_inventory.csv plus hand-researched matches."""
import csv, json
inv = {r["asin"]: r for r in csv.DictReader(open("../amazon_inventory.csv"))}

def item(id, asins, title, kind, conf, primary, alts=(), note=""):
    rows = [inv[a] for a in asins]
    return {
        "id": id, "asins": asins, "amazon_title": title,
        "anchors": sorted({x.strip() for r in rows for x in r["all_anchors"].split(";") if x.strip()})[:4],
        "links": sum(int(r["links"]) for r in rows), "posts": sum(int(r["posts"]) for r in rows),
        "example_post": rows[0]["example_post"].replace("site/content/posts/", "").replace(".md", ""),
        "kind": kind, "confidence": conf, "primary": primary, "alternatives": list(alts), "note": note,
    }

def m(merchant, product, url, epc, rate, price=None, verified=True):
    return {"merchant": merchant, "product": product, "url": url, "epc": epc, "rate": rate, "price": price, "verified": verified}

SAV, SPH, SLT = ("Savory Spice Shop", 0.33, 15), ("The Spice House", 0.21, 15), ("Sur La Table", 0.06, 9)
items = [
 item(1, ["B000NO943C"], "Chiquilín Smoked Paprika, Spanish Pimentón Ahumado, Oak-Smoked, 2.64 oz Tin", "equivalent", "high",
      m(SAV[0], "Smoked Spanish Sweet Paprika", "https://www.savoryspiceshop.com/products/smoked-spanish-sweet-paprika", SAV[1], SAV[2], "$10.95"),
      [m(SPH[0], "Smoked Spanish Paprika, Sweet (Pimentón de la Vera)", "https://www.thespicehouse.com/smoked-spanish-paprika-sweet", SPH[1], SPH[2])],
      "Different brand, same style (Spanish oak-smoked pimentón de la Vera). The recipes just call for smoked paprika."),
 item(2, ["B00017028M", "B0006FS4TI", "B0019ZHXQE"], "Maldon Sea Salt Flakes (three Amazon listings, different sizes)", "same", "high",
      m(SAV[0], "Maldon Sea Salt", "https://www.savoryspiceshop.com/products/maldon-sea-salt", SAV[1], SAV[2]),
      [m(SPH[0], "Maldon English Sea Salt", "https://thespicehouse.com/products/maldon-english-sea-salt", SPH[1], SPH[2])],
      "Same product. Merges 3 Amazon listings (2 of them no longer load on Amazon, matched by anchor text)."),
 item(3, ["1558327452"], "Herbivoracious: A Flavor Revolution with 150 Vegetarian Recipes (your cookbook)", "book", "high",
      m("Bookshop", "Herbivoracious (ISBN 9781558327450)", "https://bookshop.org/book/9781558327450", 0.01, 10, None, False),
      [m("Barnes & Noble", "Herbivoracious (ISBN 9781558327450)", "https://www.barnesandnoble.com/w/?ean=9781558327450", 0.01, 5.15, None, False)],
      "Link built from the ISBN. Bookshop blocks my automated check (403), so please click it to confirm."),
 item(4, ["B00006JSUB"], "Lodge Pre-Seasoned Cast Iron Skillet, 12 Inches", "same", "high",
      m("Lodge Cast Iron", "Classic Cast Iron Skillet, 12\" (L10SK3)", "https://www.lodgecastiron.com/products/round-cast-iron-classic-skillet", 0.02, 3, "$29.90"),
      [], "Same product on Lodge's own site; the page lists several sizes, and 12\" is one of the options."),
 item(5, ["B00008T960"], "Silpat Premium Non-Stick Silicone Baking Mat, Half Sheet Size", "same", "high",
      m(SLT[0], "Silpat Half Sheet Baking Mat", "https://www.surlatable.com/silpat-half-sheet-baking-mat/PRO-5521158.html", SLT[1], SLT[2], "$27.95"),
      [], "Same product. Sur La Table is the only in-network seller I found."),
 item(6, ["B013HB0CC4"], "Gochujang, Premium Korean Red Chili Paste, 1.1 lb", "equivalent", "medium",
      m("Weee! (SayWeee)", "Premium Gochujang Red Chili Paste, 500g", "https://www.sayweee.com/en/product/Premium-Gochujang-Red-Chili-Paste-500g-/2072369", None, None, "$18.68/lb"),
      [], "Different brand and size (500 g vs 1.1 lb). The Weee! merchant has no EPC data yet. Your posts spell it 'kochujang'."),
 item(7, ["B0058DO1SG"], "Columela Classic Sherry Vinegar, 12.7 fl oz", "equivalent", "medium",
      m("ChefShop.com", "Sanchez Romate Sherry Vinegar, 750 ml", "https://chefshop.com/products/sanchez-romate-sherry-vinegar-750ml", None, 7, None),
      [], "Different brand (a well-regarded Spanish one). ChefShop shows no EPC data. Nothing in the higher-EPC shops carries sherry vinegar."),
 item(8, ["B000YDO2LG"], "OXO Good Grips Handheld Mandoline Slicer", "same", "high",
      m("OXO", "Good Grips Hand-Held Mandoline Slicer", "https://www.oxo.com/oxo-good-grips-hand-held-mandoline-slicer.html", 0.04, 15, "~$22", False),
      [], "Same product, direct from the maker. The URL came from search results and oxo.com blocks my check (403), so please click it to confirm."),
 item(9, ["0061373265"], "Authentic Mexican, 20th Anniversary Edition (Rick Bayless)", "book", "high",
      m("Bookshop", "Authentic Mexican (ISBN 9780061373268)", "https://bookshop.org/book/9780061373268", 0.01, 10, None, False),
      [m("Barnes & Noble", "Authentic Mexican (ISBN 9780061373268)", "https://www.barnesandnoble.com/w/?ean=9780061373268", 0.01, 5.15, None, False)],
      "Link built from the ISBN (unverified; Bookshop blocks my check)."),
 item(10, ["B0000645YM"], "Cuisinart Mini Food Processor, 3-Cup, Reversible Blade", "equivalent", "high",
      m(SLT[0], "Cuisinart 3-Cup Mini-Prep Plus Food Processor", "https://www.surlatable.com/cuisinart-3-cup-mini-prep-plus-food-processor/PRO-961938.html", SLT[1], SLT[2], "$49.95"),
      [], "Same line, current model name (Mini-Prep Plus)."),
]
json.dump(items, open("matches.json", "w"), indent=1)
print(len(items), "items;", sum(i["links"] for i in items), "links covered")
