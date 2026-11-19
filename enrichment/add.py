import json,sys,os
day=int(sys.argv[1]); p='enrichment/batches/day-%02d.json'%day
cur=json.load(open(p)) if os.path.exists(p) else []
new=json.load(sys.stdin)
have={e['slug'] for e in cur}
for e in new:
    assert e['slug'] not in have, e['slug']
    assert os.path.exists('site/content/posts/%s.md'%e['slug']), e['slug']
    assert e['summary'] and e['glance']
    cur.append(e)
json.dump(cur,open(p,'w'),indent=1,ensure_ascii=False)
print(len(cur),'in day',day)
