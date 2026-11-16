"""Restore text that the cookbook import dropped: headnote (intro) paragraphs, the card's 'diet / serves / time' line, and recipe yield.
Source: the author's chapter .docx files; wording is swapped for the copyedited final book text where a near-identical line exists.
Usage: python3 seo-review/book_fix.py [--apply]"""
import sys,re,json,os,html,difflib
sys.path.insert(0,os.path.dirname(__file__))
from book_docx import load
from book_parse import norm
APPLY='--apply' in sys.argv
recs={r['title']:r for r in load()}
final=[l.strip() for l in open('/tmp/cbk/ce.txt',encoding='utf8',errors='ignore') if len(l.strip())>60]
fidx={}
for l in final: fidx.setdefault(norm(l)[:30],[]).append(l)
def finalize(par):
    key=norm(par)[:30]
    pool=fidx.get(key) or []
    if not pool:   # try close first-30 match
        ks=difflib.get_close_matches(key,list(fidx),n=1,cutoff=0.8)
        pool=fidx[ks[0]] if ks else []
    best=None;bs=0
    for l in pool:
        s=difflib.SequenceMatcher(None,norm(par),norm(l)).ratio()
        if s>bs: best,bs=l,s
    return (best,bs) if best and bs>=0.7 else (par,0)
rows=json.load(open('/tmp/book_match.json'))
stats=dict(intro=0,meta=0,yield_=0,skipped=[]);log=[]
for r in rows:
    if r['score']<0.7: stats['skipped'].append((r['name'],'low match')); continue
    f=r['file']; t=open(f).read(); parts=t.split('---',2); fm,body=parts[1],parts[2]
    b=recs[r['book']]; changed=[]
    pre=re.sub(r'<div class="recipe-card">.*','',body,flags=re.S)
    pre=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',re.sub(r'\{\{[^}]*\}\}','',pre))).strip()
    # 1. intro
    if len(pre)<120 and b['head']:
        ps=[]
        for h in b['head']:
            txt,sc=finalize(h); ps.append('<p>'+html.escape(txt,quote=False)+'</p>')
        block='\n'.join(ps)+'\n\n'
        body=body.replace('<div class="recipe-card">',block+'<div class="recipe-card">',1); changed.append(f'intro({len(ps)} paras)'); stats['intro']+=1
    elif len(pre)<120: stats['skipped'].append((r['name'],'no headnote in book'))
    # 2. meta line in card
    if b['meta'] and re.search(r'<div class="recipe-card">\s*<p><strong>[^<]*</strong>\s*</p>',body):
        line=' / '.join(b['meta'])
        body=re.sub(r'(<div class="recipe-card">\s*<p><strong>[^<]*</strong>)(\s*)</p>',lambda m:m.group(1)+'\n<br /><em>'+html.escape(line,quote=False)+'</em>\n</p>',body,count=1); changed.append('meta'); stats['meta']+=1
    # 3. yield front matter
    if not re.search(r'^  yield:',fm,re.M):
        sv=next((m for m in b['meta'] if re.match(r'^(Serves|Makes|Yields?)\b',m,re.I)),None) or next((m for m in b['meta'] if re.match(r'^\d.*servings?',m,re.I)),None)
        if sv:
            y=re.sub(r'^(Serves|Makes|Yields?)\s+','',sv,flags=re.I).strip().replace('"',"'")
            fm=re.sub(r'(^recipe:\n  name:.*\n)',lambda m:m.group(1)+f'  yield: "{y}"\n',fm,count=1,flags=re.M); changed.append('yield'); stats['yield_']+=1
    if changed:
        log.append((r['name'],changed))
        if APPLY: open(f,'w').write('---'+fm+'---'+body)
print('APPLY' if APPLY else 'DRY RUN','| intro',stats['intro'],'meta',stats['meta'],'yield',stats['yield_'])
print('skipped:',stats['skipped'])
for n,c in log[:8]: print('  ',n[:45],c)
