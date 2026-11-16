import sys,re,subprocess,json,difflib
sys.path.insert(0,'seo-review')
from book_parse import parse,norm
recs=parse()
files=subprocess.run("git show --diff-filter=A --name-only --format= 904c10c5 | grep site/content/posts",shell=True,capture_output=True,text=True).stdout.split()
def match(cands):
    best=(0,None)
    for r in recs:
        k=norm(r['title'])
        for c in cands:
            s=difflib.SequenceMatcher(None,c,k).ratio()
            if s>best[0]: best=(s,r)
    return best
out=[]
for f in files:
    t=open(f).read(); fm=t.split('---')[1]; body=t.split('---',2)[2]
    name=(re.search(r'^  name:\s*"(.*)"',fm,re.M) or re.search(r'^title:\s*"(.*)"',fm,re.M)).group(1)
    title=re.sub(r'\s*-\s*Recipe$','',re.search(r'^title:\s*"(.*)"',fm,re.M).group(1))
    sc,r=match([norm(name),norm(title)])
    plain=norm(re.sub(r'<[^>]+>',' ',re.sub(r'\{\{[^}]*\}\}','',body)))
    first=norm(r['head'][0])[:55] if r and r['head'] else ''
    out.append(dict(file=f,name=name,book=r['title'] if r else None,score=round(sc,2),has=bool(first and first in plain),nhead=len(r['head']) if r else 0))
json.dump(out,open('/tmp/book_compare.json','w'),indent=1)
good=[o for o in out if o['score']>=0.8]
print('added posts',len(out),'| matched>=0.8',len(good),'| with intro',sum(o['has'] for o in good),'| MISSING',sum(not o['has'] for o in good))
print('low-score (need manual):'); [print('  ',o['score'],o['name'][:45],'<->',(o['book'] or '')[:40]) for o in out if o['score']<0.8]
