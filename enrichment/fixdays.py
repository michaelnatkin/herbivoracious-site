import json,os,glob
q={x['slug']:x['day'] for x in json.load(open('enrichment/queue.json'))}
allr={}
for p in sorted(glob.glob('enrichment/batches/day-*.json')):
    for e in json.load(open(p)): allr[e['slug']]=e
by={}
for s,e in allr.items(): by.setdefault(q[s],[]).append(e)
order=[x['slug'] for x in json.load(open('enrichment/queue.json'))]
for p in glob.glob('enrichment/batches/day-*.json'): os.remove(p)
for d,es in by.items():
    es.sort(key=lambda e: order.index(e['slug']))
    json.dump(es,open('enrichment/batches/day-%02d.json'%d,'w'),indent=1,ensure_ascii=False)
print({d:len(v) for d,v in sorted(by.items())})
