#!/usr/bin/env python3
"""Second-chance matcher. Searches Weee!, Sur La Table and the four Shopify food merchants using the REAL Amazon listing title
(the first pass searched with anchor text like 'from a can'). Polite: one request per host every few seconds, 429 backoff.
Output: .cache/candidates/v2.json  [{id,name,title,terms,cands:[{merchant,title,url,score,source}]}]   (resumable)"""
import json,os,re,subprocess,sys,time,threading,urllib.parse,html
import concurrent.futures as cf
ROOT=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(ROOT,'.cache','candidates','v2.json')
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
items=json.load(open('/tmp/remaining_titles.json'))
res=json.load(open(OUT)) if os.path.exists(OUT) else {}
STOP=set('the a an and of for with by in to from on pack count oz ounce ounces lb lbs pound pounds inch inches ml g kg fl set piece pieces each new best premium organic natural brand free non gmo gluten amazon com grocery gourmet food kitchen'.split())
GAP={'weee':4.0,'slt':4.0,'nuts.com':9.0,'savoryspiceshop.com':9.0,'thespicehouse.com':9.0,'chefshop.com':9.0}
last={};lock={h:threading.Lock() for h in GAP};cool={}
def get(host,url):
    with lock[host]:
        if time.time()<cool.get(host,0): return '', 'cooling'
        w=GAP[host]-(time.time()-last.get(host,0))
        if w>0: time.sleep(w)
        last[host]=time.time()
        r=subprocess.run(['curl','-s','-L','--compressed','--max-time','25','-A',UA,'-w','\n%{http_code}',url],capture_output=True)
        b,_,c=r.stdout.decode('utf-8','replace').rpartition('\n')
        if c.strip()=='429': cool[host]=time.time()+300; print('429',host,flush=True)
        return b,c.strip()
def clean_title(t):
    t=re.sub(r'^Amazon\.com\s*:?\s*','',t or ''); t=t.split(' : ')[0]
    t=re.sub(r'\(.*?\)|\[.*?\]','',t); t=re.sub(r'[,;|].*$','',t) if len(t)>60 else t
    return re.sub(r'\s+',' ',t).strip()
def toks(s):
    s=html.unescape(s).lower().replace("'",'')
    return [w for w in re.findall(r'[a-z0-9]+',s) if w not in STOP and len(w)>1]
def terms(o):
    ts=[]
    t=clean_title(o['title'] or '')
    w=toks(t)
    if w: ts.append(' '.join(w[:5]))
    n=toks(o['name'])
    if n and ' '.join(n[:3]) not in ts and not re.match(r'amazon item|from a can|this |try this|or you|simple|smaller|storebought|order them|written a|the book|just soft',o['name'].lower()): ts.append(' '.join(n[:3]))
    if len(w)>=3: ts.append(' '.join(w[:3]))
    seen=[];[seen.append(x) for x in ts if x and x not in seen]
    return seen[:3]
def score(q,c):
    qs=set(toks(q)); cs=set(toks(c))
    return round(len(qs&cs)/max(1,len(qs)),2) if qs else 0
GROCERY={'pantry-staples','asian-pantry','grains-pasta-legumes','condiments-sauces','sweeteners-chocolate','spices-seasonings','mexican-latin-pantry','oils-vinegars','cheese-dairy','middle-eastern-indian-pantry',None}
GEAR={'cookware-appliances','bakeware-tools','kitchen-gadgets','knives-sharpening'}
def weee(q):
    b,c=get('weee','https://www.weee.com/en/grocery-near-me/lang-en/explore/'+urllib.parse.quote('-'.join(q.split())))
    out=[];seen=set()
    for m in re.finditer(r'/en/product/([A-Za-z0-9%_\-\.]+)/(\d+)',b):
        if m.group(2) in seen: continue
        seen.add(m.group(2)); out.append(('Weee!','https://www.weee.com'+m.group(0),urllib.parse.unquote(m.group(1)).replace('-',' ')))
    return out
def slt(q):
    b,c=get('slt','https://www.surlatable.com/search?q='+urllib.parse.quote_plus(q))
    out=[];seen=set()
    for m in re.finditer(r'href="(/product/([a-z0-9\-]+)/(\d+))"',b):
        if m.group(3) in seen: continue
        seen.add(m.group(3)); out.append(('Sur La Table','https://www.surlatable.com'+m.group(1),m.group(2).replace('-',' ')))
    return out
def shopify(host,q):
    b,c=get(host,'https://www.%s/search/suggest.json?%s'%(host,urllib.parse.urlencode({'q':q,'resources[type]':'product','resources[limit]':'5'})))
    try: ps=json.loads(b)['resources']['results']['products']
    except Exception: return []
    name={'nuts.com':'Nuts.com','savoryspiceshop.com':'Savory Spice Shop','thespicehouse.com':'The Spice House','chefshop.com':'ChefShop.com'}[host]
    return [(name,'https://www.%s%s'%(host,p['url'].split('?')[0]),p['title']) for p in ps]
def run_source(name,fn,todo):
    for o in todo:
        qs=terms(o); r=res.setdefault(o['id'],dict(id=o['id'],name=o['name'],title=o['title'],cat=o['cat'],terms=qs,cands=[]))
        if name in r.get('done',[]): continue
        found=[]
        for q in qs[:2]:
            try: found+=fn(q) if not isinstance(fn,tuple) else fn[0](fn[1],q)
            except Exception as e: print('err',name,o['id'],e,flush=True)
            if len(found)>=8: break
        base=' '.join(qs)
        for m,u,t in found:
            if not any(x['url']==u for x in r['cands']): r['cands'].append(dict(merchant=m,url=u,title=t,score=score(base,t),source=name))
        r.setdefault('done',[]).append(name)
        json.dump(res,open(OUT,'w'),indent=1)
if __name__=='__main__':
    groc=[o for o in items if o['cat'] in GROCERY]; gear=[o for o in items if o['cat'] in GEAR]
    jobs=[('weee',weee,[o for o in items if o['cat']!='books']),('slt',slt,gear+[o for o in items if o['cat'] is None])]
    for h in ['nuts.com','savoryspiceshop.com','thespicehouse.com','chefshop.com']: jobs.append((h,(shopify,h),groc))
    with cf.ThreadPoolExecutor(len(jobs)) as ex:
        fs=[ex.submit(run_source,*j) for j in jobs]
        for f in fs: f.result()
    print('DONE',len(res))
