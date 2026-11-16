#!/usr/bin/env python3
"""Ping IndexNow (Bing, Yandex and partners; Bing's index feeds ChatGPT search / Copilot) with URLs that changed in this push.
Usage: indexnow.py <before-sha> <after-sha>   |   indexnow.py --all   (submit the whole sitemap)"""
import glob,json,os,re,subprocess,sys,urllib.request
HOST="herbivoracious.com"; BASE=f"https://{HOST}"
KEY=[os.path.basename(p)[:-4] for p in glob.glob("site/static/*.txt") if re.fullmatch(r"[0-9a-f]{32}\.txt",os.path.basename(p))][0]
def permalink(path):
    t=open(path).read(); fm=t.split("---")[1] if t.startswith("---") else ""
    g=lambda k:(re.search(r'^%s:\s*"?(.*?)"?\s*$'%k,fm,re.M) or [0,""])[1]
    if re.search(r"^draft:\s*true",fm,re.M): return None
    slug=g("slug") or os.path.basename(path)[:-3]
    if "/content/posts/" in path:
        d=g("date"); return f"{BASE}/{d[:4]}/{d[5:7]}/{slug}/" if d else None
    if "/content/collections/" in path: return f"{BASE}/collections/{slug}/"
    return f"{BASE}/{slug}/"
def urls_all():
    out=[]
    for p in glob.glob("site/content/**/*.md",recursive=True):
        if p.endswith("_index.md"): continue
        u=permalink(p)
        if u: out.append(u)
    return sorted(set(out+[BASE+"/",BASE+"/collections/"]))
def urls_changed(a,b):
    names=subprocess.run(["git","diff","--name-only",a,b,"--","site/content"],capture_output=True,text=True).stdout.split()
    out=[BASE+"/"]
    for p in names:
        if p.endswith(".md") and os.path.exists(p) and not p.endswith("_index.md"):
            u=permalink(p)
            if u: out.append(u)
    return sorted(set(out))
urls=urls_all() if "--all" in sys.argv else urls_changed(sys.argv[1],sys.argv[2])
if not urls: print("nothing to submit"); sys.exit(0)
for i in range(0,len(urls),9000):
    body=json.dumps({"host":HOST,"key":KEY,"keyLocation":f"{BASE}/{KEY}.txt","urlList":urls[i:i+9000]}).encode()
    req=urllib.request.Request("https://api.indexnow.org/indexnow",data=body,headers={"Content-Type":"application/json; charset=utf-8"})
    try: r=urllib.request.urlopen(req,timeout=30); print("IndexNow",r.status,len(urls[i:i+9000]),"urls")
    except Exception as e: print("IndexNow failed (non-fatal):",e)
