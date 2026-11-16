"""Add the cookbook's total times to recipe front matter (recipe.total_time, ISO 8601) for posts whose recipe is in the book.
Only unambiguous totals ("45 minutes", "1 hour and 30 minutes (30 minutes active)"); skips "plus chilling time", "about", conditional times.
Usage: python3 seo-review/book_times.py [--apply]"""
import sys,re,glob,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
from book_docx import load
from book_parse import norm
APPLY='--apply' in sys.argv
recs=load()
PAT=re.compile(r'^\s*(?:(\d+)\s*(?:hours?|hrs?)(?:\s*(?:and)?\s*(\d+)\s*minutes?)?|(\d+)\s*minutes?)(?:\s+total)?\s*(?:\(\s*(\d+)\s*(?:minutes?|min)\.?\s*active\s*\))?\s*$',re.I)
def total_minutes(meta):
    for m in reversed(meta):
        g=PAT.match(m)
        if g:
            h,mm,only,act=g.groups()
            return (int(h)*60+int(mm or 0)) if h else int(only)
    return None
def iso(mins):
    h,m=divmod(mins,60)
    return 'PT'+(f'{h}H' if h else '')+(f'{m}M' if m else '')
OV={'bunuelos sephardic doughnuts':'sephardic doughnuts bunuelos','dhal puri roti caribbean lentil stuffed flatbread':'caribbean lentil stuffed flatbread dhal puri roti','pozole rojo de frijol':'red pozole with beans pozole rojo de frijol','spaghetti aglio e olio':'spaghetti with garlic and oil aglio e olio','tofu dengaku':'broiled tofu with miso jam tofu dengaku','apio lemony celery root':'lemony celery root apio','aromatic tofu en papillote':'aromatic tofu packets','chana mushroom masala':'chana mushroom masala with mushrooms'}
byt={}
for r in recs:
    mins=total_minutes(r['meta'])
    byt[norm(r['title'])]=(r,mins)
n_add=n_skip=n_nomatch=0; ex=[]
for f in sorted(glob.glob('site/content/posts/*.md')):
    t=open(f).read(); fm=t.split('---')[1]
    if not re.search(r'^recipe:',fm,re.M) or re.search(r'^  total_time:',fm,re.M): continue
    name=(re.search(r'^  name:\s*"(.*)"',fm,re.M) or re.search(r'^title:\s*"(.*)"',fm,re.M)).group(1)
    title=re.sub(r'\s*-\s*Recipe$','',re.search(r'^title:\s*"(.*)"',fm,re.M).group(1))
    cands=[norm(OV.get(norm(name),name)),norm(OV.get(norm(title),title))]
    best=None;bs=0
    for k,(r,mins) in byt.items():
        s=max(difflib.SequenceMatcher(None,c,k).ratio() for c in cands)
        if s>bs: best,bs=(r,mins),s
    if bs<0.86: n_nomatch+=1; continue
    r,mins=best
    if not mins: n_skip+=1; continue
    n_add+=1; ex.append((name[:34],'<->',r['title'][:34],r['meta'][-1][:40],iso(mins)))
    if APPLY:
        fm2=re.sub(r'(^recipe:\n(?:  name:.*\n)(?:  yield:.*\n)?)',lambda m:m.group(1)+f'  total_time: "{iso(mins)}"\n',fm,count=1,flags=re.M)
        if fm2!=fm: open(f,'w').write('---'+fm2+'---'+t.split('---',2)[2])
print('APPLY' if APPLY else 'DRY','| add',n_add,'| skipped (no clean total)',n_skip,'| not in book',n_nomatch)
for e in ex: print('  ',e)
print('sample skipped meta:',[ (r['title'][:25],r['meta'][-1][:40]) for r in recs if r['meta'] and not total_minutes(r['meta'])][:8])
