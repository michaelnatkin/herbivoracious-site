import zipfile,re,glob,os,sys
sys.path.insert(0,os.path.dirname(__file__))
from book_parse import norm
DIR="/Users/michael/Library/Mobile Documents/com~apple~CloudDocs/Documents/Book Edits"
def paras(f):
    x=zipfile.ZipFile(f).read('word/document.xml').decode('utf8')
    out=[]
    for p in re.findall(r'<w:p[ >].*?</w:p>',x,re.S):
        st=re.search(r'<w:pStyle w:val="([^"]+)"',p)
        t=re.sub(r'<[^>]+>','',p)
        t=t.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&quot;','"').replace('&apos;',"'")
        out.append(((st.group(1) if st else ''),t.strip()))
    return out
def load():
    chap={}
    for f in sorted(glob.glob(DIR+'/Herbivoracious.*.docx')):
        base=re.sub(r'\.(RF|RF\.MN)(\.MN)?(\.2)?\.docx$','',os.path.basename(f))
        chap.setdefault(base,[]).append(f)
    recs=[]
    for base,fs in chap.items():
        f=sorted(fs,key=lambda p:(('.2.' in p),os.path.getmtime(p)))[-1]   # latest
        P=paras(f); i=0
        while i<len(P):
            st,t=P[i]
            if st=='Heading2' and t:
                j=i+1; txt=[]
                while j<len(P) and P[j][0] not in ('RecipeIngredients','RecipeSteps','Heading2','Heading1') :
                    if P[j][1]: txt.append(P[j][1])
                    j+=1
                meta=[];head=[]
                for s in txt:
                    if not head and len(meta)<3 and len(s)<75 and not s.endswith('.'):
                        meta.append(s)
                    else: head.append(s)
                recs.append(dict(chapter=base.replace('Herbivoracious.',''),title=t,meta=meta,head=head,src=os.path.basename(f)))
                i=j
            else: i+=1
    return recs
if __name__=='__main__':
    r=load(); print(len(r)); 
    import collections; print(collections.Counter(x['chapter'] for x in r))
    for x in r[:3]: print(x['title'],x['meta'],len(x['head']))
