import json,sys
w=json.load(open('out/desc_work.json')); a,b=int(sys.argv[1]),int(sys.argv[2])
for i in range(a,min(b,len(w))):
    x=w[i]; print(f"[{i}] {x['title']} {'(R)' if x['recipe'] else ''}\n   {x['text'][:340]}")
