#!/usr/bin/env python3
"""Apply the next un-applied enrichment batch (enrichment/batches/day-NN.json).

Each entry: slug, summary, glance [{label,value}], faq [{q,a}] (optional),
yield (optional fix), total_time (optional ISO, only if the post states a time).
Sets lastmod to today's real date. Never touches the post's prose.
Usage: apply.py            -> next pending day (no-op if its batch file is missing)
       apply.py --day 3    -> force a specific day
"""
import json, re, sys, html, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
POSTS = ROOT.parent / "site" / "content" / "posts"
state_path = ROOT / "state.json"
state = json.loads(state_path.read_text()) if state_path.exists() else {"applied": []}

if "--day" in sys.argv:
    day = int(sys.argv[sys.argv.index("--day") + 1])
else:
    day = max(state["applied"], default=0) + 1
batch_path = ROOT / "batches" / f"day-{day:02d}.json"
if not batch_path.exists():
    print(f"no batch file for day {day}; nothing to do")
    sys.exit(0)

today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
esc = lambda s: html.escape(s, quote=False)

def yq(s):
    return json.dumps(s, ensure_ascii=False)

out = []
for e in json.loads(batch_path.read_text()):
    f = POSTS / f"{e['slug']}.md"
    t = f.read_text()
    head, sep, body = t.partition("\n---\n")
    if not sep or not t.startswith("---\n"):
        sys.exit(f"{f.name}: unexpected front matter")
    assert e["summary"].strip() and e["glance"], e["slug"]
    if re.search(r"^summary:", head, re.M):
        print(f"skip {e['slug']} (already has summary)")
        continue
    lines = head.split("\n")
    if lines[1].startswith("lastmod:"):
        lines[1] = f"lastmod: {today}"
    else:
        lines.insert(1, f"lastmod: {today}")
    head = "\n".join(lines)
    def setfield(head, key, val):
        if re.search(rf"^  {key}:", head, re.M):
            return re.sub(rf"^(  {key}: ).*$", lambda m: m.group(1) + yq(val), head, count=1, flags=re.M)
        anchor = r"^  yield: .*$" if key == "total_time" and re.search(r"^  yield:", head, re.M) else r"^  name: .*$"
        head, n = re.subn(anchor, lambda m: m.group(0) + f"\n  {key}: {yq(val)}", head, count=1, flags=re.M)
        if not n:
            sys.exit(f"{e['slug']}: nowhere to put {key}")
        return head
    if "yield" in e:
        head = setfield(head, "yield", e["yield"])
    if "total_time" in e and not re.search(r"^  total_time:", head, re.M):
        head = setfield(head, "total_time", e["total_time"])
    fm = f"\nsummary: {yq(e['summary'])}\nglance:\n"
    for g in e["glance"]:
        fm += f"  - label: {yq(g[0])}\n    value: {yq(g[1])}\n"
    head += fm.rstrip("\n")
    if e.get("faq") and "Frequently asked questions" not in body:
        faq = '\n\n<div class="faq"><h2>Frequently asked questions</h2>\n'
        for q, a in e["faq"]:
            faq += f"\n<h3>{esc(q)}</h3>\n<p>{esc(a)}</p>\n"
        faq += "\n</div>\n"
        body = body.rstrip("\n") + faq
    out.append((f, head + sep + body))
    print("will enrich", e["slug"])

for f, text in out:
    f.write_text(text)
state["applied"].append(day)
state_path.write_text(json.dumps(state))
