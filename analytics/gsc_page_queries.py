"""Pull page x query rows (read-only) for the real site, to ground title/meta rewrites in what people search."""
import datetime, json, os
from googleapiclient.discovery import build
from google_auth import creds
SITE = "sc-domain:herbivoracious.com"
sc = build("searchconsole", "v1", credentials=creds(), cache_discovery=False)
end = datetime.date.today() - datetime.timedelta(days=3); start = end - datetime.timedelta(days=270)
rows, sr = [], 0
while True:
    r = sc.searchanalytics().query(siteUrl=SITE, body={"startDate": str(start), "endDate": str(end), "dimensions": ["page", "query"],
        "rowLimit": 25000, "startRow": sr, "dimensionFilterGroups": [{"filters": [{"dimension": "page", "operator": "includingRegex", "expression": "^https://herbivoracious\\.com/(19|20)\\d\\d/"}]}]}).execute().get("rows", [])
    rows += r
    if len(r) < 25000 or sr >= 100000: break
    sr += 25000
json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "gsc_page_query.json"), "w"))
print(len(rows), "page-query rows")
