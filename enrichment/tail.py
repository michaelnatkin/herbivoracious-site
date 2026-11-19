import re,sys,html
s=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 1500
t=open('site/content/posts/%s.md'%s).read(); body=t.split('\n---\n',1)[1].split('Frequently asked questions')[0]
b=re.sub(r'<[^>]+>',' ',body); b=re.sub(r'\{\{[^}]*\}\}','',b); b=html.unescape(b); b=re.sub(r'\s+',' ',b)
print('---',s); print(b[-n:])
