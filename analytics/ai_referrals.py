#!/usr/bin/env python3
"""AI-assistant visibility report. Run monthly: python3 ai_referrals.py [start-date]
1) GA4: sessions arriving from AI assistants / AI search (ChatGPT, Perplexity, Claude, Gemini, Copilot, ...) and the pages they land on.
2) Search Console: how many queries look like prompts (long, conversational) and which pages they hit.
Saves out/ai_referrals_<date>.json so month-over-month change is easy to see."""
import datetime,json,os,re,sys
from google_auth import creds
from googleapiclient.discovery import build
START=sys.argv[1] if len(sys.argv)>1 else (datetime.date.today()-datetime.timedelta(days=90)).isoformat()
AI=re.compile(r'chatgpt|openai|perplexity|claude|anthropic|gemini|copilot|you\.com|phind|kagi|meta\.ai|deepseek|grok|poe\.com|bing\.com/chat|search\.brave',re.I)
ga=build('analyticsdata','v1beta',credentials=creds())
def run(dims,limit=500):
    body={"dateRanges":[{"startDate":START,"endDate":"today"}],"dimensions":[{"name":d} for d in dims],"metrics":[{"name":"sessions"},{"name":"engagedSessions"}],"limit":limit}
    r=ga.properties().runReport(property='properties/310663584',body=body).execute()
    return [([x['value'] for x in row['dimensionValues']],int(row['metricValues'][0]['value']),int(row['metricValues'][1]['value'])) for row in r.get('rows',[])]
src=[r for r in run(['sessionSource']) if AI.search(r[0][0])]
land=[r for r in run(['sessionSource','landingPage'],2000) if AI.search(r[0][0])]
total=sum(r[1] for r in run(['sessionDefaultChannelGroup']))
print(f'Since {START}: {sum(r[1] for r in src)} AI-assistant sessions of {total} total ({100*sum(r[1] for r in src)/max(total,1):.2f}%)')
for r in sorted(src,key=lambda r:-r[1]): print(f'  {r[0][0]:28} {r[1]:5} sessions  {r[2]:4} engaged')
print('Top landing pages from AI sources:')
agg={}
for (s,p),n,e in land: agg[p]=agg.get(p,0)+n
for p,n in sorted(agg.items(),key=lambda x:-x[1])[:10]: print(f'  {n:4}  {p}')
gsc=build('searchconsole','v1',credentials=creds())
rows=gsc.searchanalytics().query(siteUrl='sc-domain:herbivoracious.com',body={"startDate":START,"endDate":datetime.date.today().isoformat(),"dimensions":["query"],"rowLimit":25000}).execute().get('rows',[])
rows=[r for r in rows if re.fullmatch(r"[a-z0-9 '\-&,?.]+",r['keys'][0].lower())]
long=[r for r in rows if len(r['keys'][0].split())>=7]
prompt=[r for r in rows if re.search(r'^(guide me|give me|help me|walk me|suggest|recommend|what is the best|can you|show me)|\b(featuring|using only|that (uses|use|can))\b',r['keys'][0])]
print(f'Search Console: {len(rows)} queries, {len(long)} with 7+ words, {len(prompt)} prompt-like (impressions {sum(r["impressions"] for r in prompt)})')
out=dict(start=START,ai_sessions=[(r[0][0],r[1],r[2]) for r in src],landing=sorted(agg.items(),key=lambda x:-x[1])[:25],gsc_prompt_like=[(r['keys'][0],r['impressions'],r['clicks']) for r in sorted(prompt,key=lambda r:-r['impressions'])[:40]])
os.makedirs('out',exist_ok=True); fn=f'out/ai_referrals_{datetime.date.today().isoformat()}.json'; json.dump(out,open(fn,'w'),indent=1); print('saved',fn)
