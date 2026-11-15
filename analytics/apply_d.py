import json,re,glob,sys
w=json.load(open('out/desc_work.json'))
n=0
for p in sorted(glob.glob('out/d/*.json')):
    for i,d in json.load(open(p)).items():
        x=w[int(i)]; f='../site/'+x['file']
        assert len(d)<=175,(i,len(d))
        s=open(f).read(); head,rest=s.split('\n---\n',1)
        q='"'+d.replace('\\','\\\\').replace('"','\\"')+'"'
        head=re.sub(r'^description:.*\n?','',head,flags=re.M)
        head=re.sub(r'^(title:.*)$',lambda m:m.group(1)+f'\ndescription: {q}',head,count=1,flags=re.M)
        open(f,'w').write(head+'\n---\n'+rest); n+=1
print(n,'applied')
