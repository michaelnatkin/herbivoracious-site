import json,re,sys,html
day=int(sys.argv[1]); q=json.load(open('enrichment/queue.json'))
lo=int(sys.argv[2]) if len(sys.argv)>2 else 0
for x in [x for x in q if x['day']==day][lo:lo+5]:
    t=open('site/content/posts/%s.md'%x['slug']).read(); head,body=t.split('\n---\n',1)
    has='Frequently asked' in body
    rec=head.split('\nrecipe:')[1] if '\nrecipe:' in head else ''
    meta=[l.strip() for l in rec.split('\n') if re.match(r'  (yield|total_time|prep_time|cook_time):',l)]
    b=body.split('Frequently asked questions')[0]
    b=re.sub(r'<[^>]+>',' ',b); b=re.sub(r'\{\{[^}]*\}\}','',b); b=html.unescape(b); b=re.sub(r'\s+',' ',b)
    lim=2600 if has else 3800
    print('=====',x['slug'],'| HAS-FAQ' if has else '| NEEDS-FAQ',meta); print(b[:lim] + (' …[%d more]'%(len(b)-lim) if len(b)>lim else ''))
