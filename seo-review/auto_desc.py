import glob,re,html,json,sys
rows=json.load(open('../analytics/out/gsc_by_page.json'))['rows']
imp={r['keys'][0].rstrip('/').split('/')[-1]:r['impressions'] for r in rows}
def intro(body):
    body=re.sub(r'\{\{[%<].*?[%>]\}\}','',body,flags=re.S)
    paras=re.findall(r'<p[^>]*>(.*?)</p>',body,flags=re.S) or re.split(r'\n\s*\n',body)
    for p in paras:
        t=html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',p))).strip()
        t=re.sub(r'\s+([.,;:!?])',r'\1',t)
        if len(t)<70: continue
        if re.match(r'^[\d¼½¾⅓⅔]',t) or re.search(r'Serves|Yields|Makes \d|minutes /|\bcups?\b.*\bcups?\b',t[:120]): continue
        if re.match(r'^(Posted|Updated|Filed|Tags|Categories|Share|Related)',t): continue
        return t
    return ''
def trim(t,n=155):
    if len(t)<=n: return t
    cut=t[:n]; m=max(cut.rfind('. '),cut.rfind('! '),cut.rfind('? '))
    if m>=90: return cut[:m+1]
    return cut.rsplit(' ',1)[0].rstrip(',;:-–—')+'…'
out=[];skipped=[]
for f in glob.glob('content/posts/*.md')+glob.glob('content/*.md'):
    s=open(f).read()
    if not s.startswith('---\n'): continue
    head,rest=s.split('\n---\n',1)
    if re.search(r'^draft:\s*true',head,re.M): continue
    m=re.search(r'^description:\s*(.*)$',head,re.M)
    if m and len(m.group(1).strip('"\' '))>=20: continue
    d=trim(intro(rest))
    mt=re.search(r'^title:\s*(.*?)\s*$',head,re.M)
    if not mt: skipped.append(f.split('/')[-1][:-3]); continue
    tt=mt.group(1).strip('"\'')
    tt=html.unescape(tt)
    words={w for w in re.findall(r"[a-z]{4,}",tt.lower())}-{'recipe','recipes','with','from','review','and','your','vegetarian','style','guest','post'}
    ok=d and re.search(r'^[A-Z]',d) and any(w in d.lower() for w in words) and not re.match(r"^(I |I'|I’|My |So |Well|Here are|One of the many)",d) and not (d.count(' ')<8)
    isrec='recipe:' in head
    if not ok:
        ct=re.sub(r'\s*[-–—:]?\s*(A )?(Vegetarian |Vegan )?Recipes?\b.*$','',tt,flags=re.I).strip(' -–—:') or tt
        d=f"{ct}: a vegetarian recipe with ingredients and step-by-step instructions from Herbivoracious." if isrec else ''
        if not d: skipped.append(f.split('/')[-1][:-3]); continue
    sl=f.split('/')[-1][:-3]
    if not d: skipped.append(sl); continue
    q='"'+d.replace('\\','\\\\').replace('"','\\"')+'"'
    head=re.sub(r'^description:.*\n?','',head,flags=re.M)
    head=re.sub(r'^(title:.*)$',lambda mm:mm.group(1)+f'\ndescription: {q}',head,count=1,flags=re.M)
    out.append((imp.get(sl,0),sl,d))
    if '--apply' in sys.argv: open(f,'w').write(head+'\n---\n'+rest)
out.sort(reverse=True)
print(len(out),'with generated description;',len(skipped),'skipped (no usable intro)')
for i,sl,d in out[:25]: print(int(i),sl[:45],'|',d)
json.dump(skipped,open('../analytics/out/desc_skipped.json','w'))
