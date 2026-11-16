import sys,re,json,os,difflib,html
sys.path.insert(0,os.path.dirname(__file__))
from book_docx import load
from book_parse import norm
exec(open(os.path.join(os.path.dirname(__file__),'book_fix.py')).read().split("rows=json.load")[0].split("APPLY=")[0]) if False else None
recs={r['title']:r for r in load()}
final=[l.strip() for l in open('/tmp/cbk/ce.txt',encoding='utf8',errors='ignore') if len(l.strip())>40]
fidx={}
for l in final: fidx.setdefault(norm(l)[:30],[]).append(l)
def finalize(par):
    key=norm(par)[:30]; pool=fidx.get(key) or []
    if not pool:
        ks=difflib.get_close_matches(key,list(fidx),n=1,cutoff=0.75); pool=fidx[ks[0]] if ks else []
    best=None;bs=0
    for l in pool:
        s=difflib.SequenceMatcher(None,norm(par),norm(l)).ratio()
        if s>bs: best,bs=l,s
    return (best,bs) if best and bs>=0.6 else (par,0.0)
rows=json.load(open('/tmp/book_match.json'))
plan=[]
for r in rows:
    if r['score']<0.7: continue
    b=recs[r['book']]; t=open(r['file']).read(); body=t.split('---',2)[2]
    pre=body.split('<div class="recipe-card">')[0]
    olds=re.findall(r'<p>(.*?)</p>',pre,re.S)
    if not b['head']: continue
    news=[finalize(h) for h in b['head']]
    def plain(s): return norm(re.sub(r'<[^>]+>',' ',re.sub(r'\{\{[^}]*\}\}','',s)))
    pairs=[]
    for i,o in enumerate(olds):
        best=max(range(len(news)),key=lambda j:difflib.SequenceMatcher(None,plain(o),norm(news[j][0])).ratio()) if news else None
        pairs.append((i,best,round(difflib.SequenceMatcher(None,plain(o),norm(news[best][0])).ratio(),2)))
    same=sum(1 for p in pairs if p[2]>=0.99)
    status='equal' if len(olds)==len(news) and same==len(olds) else ('replace' if olds else 'none')
    plan.append(dict(file=r['file'],name=r['name'],nold=len(olds),nnew=len(news),pairs=pairs,status=status,finals=[round(n[1],2) for n in news]))
json.dump(plan,open('/tmp/book_update_plan.json','w'),indent=1)
import collections
print(collections.Counter(p['status'] for p in plan))
for p in plan:
    if p['status']=='replace': print(p['name'][:38].ljust(38),'old',p['nold'],'new',p['nnew'],'best-sim',[x[2] for x in p['pairs']],'final-match',p['finals'])
