import re,json,unicodedata
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()
def parse(path='/tmp/cbk/ce.txt'):
    L=[l.rstrip('\n') for l in open(path,encoding='utf8',errors='ignore')]
    recs=[]; i=0
    diet=re.compile(r'^(Vegan|Vegetarian|Gluten|Not vegan|Vegetarian;)',re.I)
    serves=re.compile(r'^(Serves|Makes|Yields?)\b',re.I)
    while i<len(L)-3:
        t=L[i].strip()
        if t and len(t)<110 and not t.endswith('.') and (diet.match(L[i+1].strip()) or serves.match(L[i+1].strip()) or serves.match(L[i+2].strip())):
            # header block: title, [diet], serves, time
            j=i+1; meta=[]
            while j<len(L) and j<i+5 and L[j].strip() and len(L[j])<110 and not re.match(r'^\d',L[j].strip()) or (j<i+5 and re.match(r'^\d+ (minutes|hour)',L[j].strip())):
                meta.append(L[j].strip()); j+=1
                if len(meta)>=3: break
            # headnote paragraphs until blank line followed by ingredient list (first line starting with a digit/quantity) -- headnote = non-empty lines before first blank line after which a quantity line appears
            k=j; head=[]
            while k<len(L) and L[k].strip(): head.append(L[k].strip()); k+=1
            # skip blank, collect following block as headnote continuation? headnotes use consecutive lines; stop at first blank
            recs.append(dict(title=t,meta=meta,head=head,line=i)); i=k
        else: i+=1
    return recs
if __name__=='__main__':
    r=parse(); print(len(r)); 
    for x in r[:6]+r[-3:]: print(x['title'],'|',x['meta'],'|',len(x['head']),'paras')
