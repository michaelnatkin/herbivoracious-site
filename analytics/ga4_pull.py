"""Pull GA4 reports (read-only) into analytics/out/ga4_*.json."""
import json, os, sys
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
from google_auth import creds
PROP = "properties/310663584"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
c = BetaAnalyticsDataClient(credentials=creds())
def run(name, dims, mets, start="365daysAgo", limit=250, order=None):
    r = c.run_report(RunReportRequest(property=PROP, dimensions=[Dimension(name=d) for d in dims], metrics=[Metric(name=m) for m in mets],
                                      date_ranges=[DateRange(start_date=start, end_date="today")], limit=limit))
    rows = [{**{d: v.value for d, v in zip(dims, x.dimension_values)}, **{m: v.value for m, v in zip(mets, x.metric_values)}} for x in r.rows]
    json.dump(rows, open(os.path.join(OUT, f"ga4_{name}.json"), "w"), indent=1); print(name, len(rows))
    return rows
M = ["sessions", "totalUsers", "screenPageViews", "engagementRate", "averageSessionDuration"]
run("by_month", ["yearMonth"], M, start="2023-01-01", limit=100)
run("by_channel", ["sessionDefaultChannelGroup"], M)
run("by_source", ["sessionSource", "sessionMedium"], M, limit=40)
run("top_pages", ["pagePath"], ["screenPageViews", "sessions", "engagementRate"], limit=60)
run("by_country", ["country"], ["sessions"], limit=15)
run("by_device", ["deviceCategory"], ["sessions"])
