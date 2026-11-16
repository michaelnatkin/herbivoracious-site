import sys,re,subprocess,json,difflib,os
sys.path.insert(0,os.path.dirname(__file__))
from book_parse import norm
from book_docx import load
recs=load()
files=subprocess.run("git show --diff-filter=A --name-only --format= 904c10c5 | grep site/content/posts",shell=True,capture_output=True,text=True).stdout.split()
rows=[]
for f in files:
    t=open(f).read(); fm=t.split('---')[1]; body=t.split('---',2)[2]
    name=(re.search(r'^  name:\s*"(.*)"',fm,re.M) or re.search(r'^title:\s*"(.*)"',fm,re.M)).group(1)
    title=re.sub(r'\s*-\s*Recipe$','',re.search(r'^title:\s*"(.*)"',fm,re.M).group(1))
    cands=[norm(name),norm(title)]
    def sc(r):
        k=norm(r['title']); return max(difflib.SequenceMatcher(None,c,k).ratio() for c in cands)
    OV={'Bunuelos (Sephardic Doughnuts)':'Sephardic Doughnuts (Bunuelos)','Dhal Puri Roti (Caribbean Lentil-stuffed Flatbread)':'Caribbean Lentil-stuffed Flatbread (Dhal Puri Roti)','Pozole Rojo de Frijol':'Red Pozole with Beans (Pozole Rojo de Frijol)','Spaghetti Aglio e Olio':'Spaghetti with Garlic and Oil (Aglio e Olio)','Tofu Dengaku':'Broiled Tofu with Miso Jam (Tofu Dengaku)'}
    if name in OV: best=next(r for r in recs if r['title'].startswith(OV[name][:25])); s=1.0
    else: best=max(recs,key=sc); s=sc(best)
    plain=norm(re.sub(r'<[^>]+>',' ',re.sub(r'\{\{[^}]*\}\}','',body)))
    first=norm(best['head'][0])[:55] if best['head'] else ''
    rows.append(dict(file=f,name=name,book=best['title'],score=round(s,2),has=bool(first and first in plain),nhead=len(best['head'])))
json.dump(rows,open('/tmp/book_match.json','w'),indent=1)
ok=[r for r in rows if r['score']>=0.8]
print('posts',len(rows),'| matched>=0.8',len(ok),'| intro present',sum(r['has'] for r in ok),'| intro MISSING',sum(not r['has'] for r in ok))
for r in rows:
    if r['score']<0.8: print('  LOW',r['score'],r['name'][:42],'<->',r['book'][:42])
