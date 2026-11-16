"""Clean manuscript artifacts in restored headnotes: '(page 000)' cross-references -> links to the matching post (or removed), stray editor notes."""
import re,glob,subprocess,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from book_parse import norm
# map recipe names -> permalink for every post
names={}
for f in glob.glob('site/content/posts/*.md'):
    fm=open(f).read().split('---')[1]
    g=lambda k:(re.search(r'^%s:\s*"?(.*?)"?\s*$'%k,fm,re.M) or [0,''])[1]
    d=g('date'); url=f"/{d[:4]}/{d[5:7]}/{g('slug')}/"
    for n in {g('title'),(re.search(r'^  name:\s*"(.*)"',fm,re.M) or [0,''])[1]}:
        n=re.sub(r'\s*-\s*Recipe$','',n); n=re.sub(r'^Recipe:\s*','',n)
        if n: names[norm(n)]=(url,n)
ALIASES={'brussels sprout gratin':None}
added=set()
diff=subprocess.run(['git','diff','-U0','--','site/content/posts'],capture_output=True,text=True).stdout
for l in diff.split('\n'):
    if l.startswith('+<p>') : added.add(l[1:])
n_link=n_drop=0; unresolved=[]
for f in sorted(glob.glob('site/content/posts/*.md')):
    t=open(f).read(); out=[]; ch=False
    for line in t.split('\n'):
        if line in added and ('page 000' in line or 'WITH WHAT' in line):
            new=line.replace('served WITH WHAT.','').replace('.served WITH WHAT','.')
            def sub(m):
                global n_link,n_drop
                before=new[:m.start()]
                title_txt=re.sub(r'<[^>]+>','',before)
                words=title_txt.split()
                for k in range(min(10,len(words)),0,-1):
                    cand=' '.join(words[-k:]).strip(' ,.;:()')
                    if norm(cand) in names and k>=2 and not before.rstrip().endswith('</a>'):
                        url,nm=names[norm(cand)]
                        n_link+=1
                        return ('\x00LINK',cand,url)
                n_drop+=1; unresolved.append((os.path.basename(f)[:40],title_txt[-50:])); return ''
            # process each occurrence left-to-right
            res=new; pos=0
            while True:
                m=re.search(r'\s*\((?:see |See )?(?:the box on )?page 000\)',res)
                if not m: break
                r=sub(m)
                if isinstance(r,tuple):
                    _,cand,url=r
                    start=res.rfind(cand,0,m.start())
                    res=res[:start]+f'<a href="{url}">{cand}</a>'+res[m.end():]
                else:
                    res=res[:m.start()]+r+res[m.end():]
            new=res.replace('(page 000)','').replace('  ',' ')
            out.append(new); ch=True
        else: out.append(line)
    if ch: open(f,'w').write('\n'.join(out))
print('linked',n_link,'| dropped',n_drop); [print('  dropped after:',u) for u in unresolved]
