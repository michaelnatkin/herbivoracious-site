"""Pull 16 months of Search Console data (read-only) into analytics/out/ as JSON."""
import datetime, json, os
from googleapiclient.discovery import build
from google_auth import creds
SITE = "sc-domain:herbivoracious.com"
sc = build("searchconsole", "v1", credentials=creds(), cache_discovery=False)
end = datetime.date.today() - datetime.timedelta(days=3)          # GSC data lags ~2-3 days
start = end - datetime.timedelta(days=480)
def q(dims, limit=25000):
    rows, start_row = [], 0
    while True:
        r = sc.searchanalytics().query(siteUrl=SITE, body={"startDate": str(start), "endDate": str(end), "dimensions": dims,
              "rowLimit": 25000, "startRow": start_row, "dataState": "final"}).execute().get("rows", [])
        rows += r
        if len(r) < 25000 or len(rows) >= limit: return rows
        start_row += 25000
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
for name, dims in (("by_month", ["date"]), ("by_page", ["page"]), ("by_query", ["query"]), ("by_page_month", ["page", "date"])):
    rows = q(dims, limit=60000 if name == "by_page_month" else 25000)
    json.dump({"start": str(start), "end": str(end), "rows": rows}, open(f"{out}/gsc_{name}.json", "w"))
    print(name, len(rows), "rows")
