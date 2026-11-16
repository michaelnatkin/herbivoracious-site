#!/usr/bin/env python3
"""Turn hand-picked second-pass matches into review batches (same format as batch-NN.json).
Resolves URLs from .cache/candidates/v2.json, verifies Weee!/Sur La Table/Shopify pages (200 + schema.org InStock), writes batches/batch-<name>.json.
Usage: python3 propose_v2.py <picks.json> <batch-name>"""
import json,os,re,sys,subprocess,time,glob,html
ROOT=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.dirname(ROOT)
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
picks=json.load(open(sys.argv[1])); name=sys.argv[2]
cat=json.load(open(os.path.join(REPO,'site/data/products.json')))
cands=json.load(open(os.path.join(ROOT,'.cache/candidates/v2.json')))
tit={}
for f in ['amazon_titles.json','amazon_titles_browser.json']:
    p=os.path.join(ROOT,'.cache',f)
    if os.path.exists(p): tit.update(json.load(open(p)))
RATE={'Weee!':(None,10),'Sur La Table':(0.06,9),"Murray's Cheese":(0.06,6),'Barnes & Noble':(0.01,5.15),'ChefShop.com':(None,7),'Savory Spice Shop':(0.33,15),'The Spice House':(0.21,15),'Nuts.com':(0.38,20),'King Arthur Baking':(0.08,5),'iHerb.com':(0.13,15)}
usage={}
for f in glob.glob(os.path.join(REPO,'site/content/posts/*.md'))+glob.glob(os.path.join(REPO,'site/content/*.md')):
    t=open(f).read()
    for m in re.finditer(r'product id="([^"]+)"',t): usage.setdefault(m.group(1),set()).add(os.path.basename(f)[:-3])
last={}
def get(url,host):
    w=3.0-(time.time()-last.get(host,0))
    if w>0: time.sleep(w)
    last[host]=time.time()
    r=subprocess.run(['curl','-s','-L','--compressed','--max-time','25','-A',UA,'-w','\n%{http_code}',url],capture_output=True)
    b,_,c=r.stdout.decode('utf-8','replace').rpartition('\n'); return b,c.strip()
def verify(url,merchant):
    if merchant not in ('Weee!','Sur La Table','Savory Spice Shop','The Spice House','Nuts.com','ChefShop.com'): return None,None,'not checkable (site blocks scripts)'
    b,c=get(url,merchant)
    if c in ('403','429','000'):
        time.sleep(12); b,c=get(url,merchant)
    if c!='200': return False,None,f'HTTP {c}'
    av=re.search(r'"availability":\s*"(?:https?://schema.org/)?(\w+)"',b)
    pr=re.search(r'"price":\s*"?([0-9.]+)"?',b)
    price='$'+pr.group(1) if pr and merchant!='ChefShop.com' else None
    if av and av.group(1)!='InStock': return False,price,'schema.org says '+av.group(1)
    return True,price,'ok' if av else 'ok (no availability data)'
out=[]
for pid,pk in picks.items():
    p=cat[pid]; c=cands.get(pid,{}).get('cands',[])
    url=pk.get('url')
    if not url:
        m=[x for x in c if pk['sub'] in x['url']]
        if not m: print('NO CAND',pid,pk['sub']); continue
        url=m[0]['url']; pk.setdefault('product',m[0]['title'])
    merchant=pk['merchant']
    ok,price,why=verify(url,merchant)
    print(f"{pid[:36]:36} {merchant[:12]:12} {pk['conf']:6} verified={ok} {price or ''} {why}")
    if ok is False: print('   -> dropped'); continue
    epc,rate=RATE.get(merchant,(None,None))
    t=re.sub(r'^Amazon\.com\s*:?\s*','',tit.get(next((a for a in p.get('asins',[]) if a in tit),''),'') or p['name'])
    out.append(dict(id=pid,name=p['name'],status='match',kind=pk.get('kind','equivalent'),confidence=pk['conf'],
        amazon=dict(asins=p.get('asins',[]),title=t[:140],anchors=[],links=len(usage.get(pid,[])),posts=len(usage.get(pid,[])),example_post=sorted(usage.get(pid,['']))[0]),
        primary=dict(merchant=merchant,product=html.unescape(pk.get('product',''))[:120],url=url,epc=epc,rate=rate,price=pk.get('price') or price,verified=bool(ok)),
        alternatives=[],note=pk['note']))
json.dump(out,open(os.path.join(ROOT,'batches',f'batch-{name}.json'),'w'),indent=1)
print('wrote',len(out),'proposals to batch-'+name+'.json')
