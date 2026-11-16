"""Update existing intro paragraphs of cookbook posts to the final copyedited manuscript text, preserving product links / inline markup.
Only replaces a paragraph when it clearly corresponds to a manuscript paragraph near that recipe (similarity >= 0.55) and every link can be re-applied.
Usage: python3 seo-review/book_update.py [--apply]"""
import sys,re,json,os,difflib,html
sys.path.insert(0,os.path.dirname(__file__))
from book_docx import load
from book_parse import norm
APPLY='--apply' in sys.argv
recs={r['title']:r for r in load()}
FL=[]  # (lineno, text)
for i,l in enumerate(open('/tmp/cbk/ce.txt',encoding='utf8',errors='ignore')):
    s=l.strip()
    if len(s)>40: FL.append((i,s))
def strip_markup(s): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',re.sub(r'\{\{[^}]*\}\}','',s))).strip())
def anchor_index(heads):
    for h in heads:
        k=norm(h)
        best=max(FL,key=lambda x:difflib.SequenceMatcher(None,k[:80],norm(x[1])[:80]).ratio())
        if difflib.SequenceMatcher(None,k[:80],norm(best[1])[:80]).ratio()>=0.85: return best[0]
    return None
def spans_of(old):
    sp=[]
    for m in re.finditer(r'\{\{% product [^%]*%\}\}',old):
        e=old.find('{{% /product %}}',m.end())
        if e>0: sp.append((m.start(),m.group(0),'{{% /product %}}',strip_markup(old[m.end():e])))
    for m in re.finditer(r'<(a|em|strong|b|i)\b[^>]*>',old):
        e=old.find('</'+m.group(1)+'>',m.end())
        if e>0: sp.append((m.start(),m.group(0),'</'+m.group(1)+'>',strip_markup(old[m.end():e])))
    return sorted(sp)
def rebuild(old,new):
    esc=html.escape(new,quote=False); sp=spans_of(old)
    groups={}
    for st,op,cl,txt in sp:
        if txt: groups.setdefault(html.escape(txt,quote=False),[]).append((st,op,cl))
    edits=[];lost=[]
    for txt,g in groups.items():
        i=esc.find(txt)
        if i<0:
            i=esc.lower().find(txt.lower())
        if i<0: lost.append(txt); continue
        g.sort(); edits.append((i,i+len(txt),''.join(o for _,o,_ in g),''.join(c for _,_,c in reversed(g))))
    edits.sort(key=lambda e:(e[0],-e[1]))
    out=esc; 
    for s,e,o,c in sorted(edits,key=lambda e:-e[0]):
        out=out[:s]+o+out[s:e]+c+out[e:]
    return out,lost
rows=json.load(open('/tmp/book_match.json')); stats=dict(same=0,replaced=0,left=0,flag=0); flagged=[]; samples=[]; changes=[]
for r in rows:
    if r['score']<0.7: continue
    b=recs[r['book']]
    if not b['head']: continue
    f=r['file']; t=open(f).read(); parts=t.split('---',2); body=parts[2]
    pre,sep,post=body.partition('<div class="recipe-card">')
    if not sep: continue
    a=anchor_index(b['head'])
    if a is None: stats['flag']+=1; flagged.append((r['name'],'no anchor')); continue
    cands=[x for x in FL if a-6<=x[0]<=a+70]
    def repl(m):
        old=m.group(1); pl=strip_markup(old)
        if len(pl)<40: stats['left']+=1; return m.group(0)
        best=max(cands,key=lambda x:difflib.SequenceMatcher(None,norm(pl),norm(x[1])).ratio())
        sim=difflib.SequenceMatcher(None,norm(pl),norm(best[1])).ratio()
        if sim>=0.995: stats['same']+=1; return m.group(0)
        if sim<0.55: stats['left']+=1; return m.group(0)
        best=(best[0],re.sub(r'\s*\((?:see |See )?(?:the box on )?page 000\)','',best[1]))
        if re.search(r'[\[\]]|page 000|<BOX|END BOX|\bTK\b',best[1]):
            stats['flag']+=1; flagged.append((r['name'],'manuscript paragraph has an editor query / placeholder - left as is: '+best[1][:60])); return m.group(0)
        new,lost=rebuild(old,best[1])
        if lost: stats['flag']+=1; flagged.append((r['name'],'link text not in final: '+'; '.join(lost)[:70])); return m.group(0)
        stats['replaced']+=1; samples.append((r['name'],round(sim,2),pl[:90],best[1][:90])); changes.append(r['name'])
        return '<p>'+new+'</p>'
    pre2=re.sub(r'<p>(.*?)</p>',repl,pre,flags=re.S)
    if pre2!=pre and APPLY: open(f,'w').write('---'+parts[1]+'---'+pre2+sep+post)
print('APPLY' if APPLY else 'DRY RUN',stats,'| posts touched',len(set(changes)))
print('flagged:'); [print('  ',x) for x in flagged[:25]]
import random; random.seed(3)
print('samples:'); [print(f'  [{s[1]}] {s[0][:30]}\n     OLD: {s[2]}\n     NEW: {s[3]}') for s in random.sample(samples,min(6,len(samples)))]
