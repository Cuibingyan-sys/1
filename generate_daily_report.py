#!/usr/bin/env python3
"""每日报告生成脚本 — 生成报告JSON并尝试从GA4/AdSense获取数据"""
import json, os, datetime
from pathlib import Path

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
today = now.strftime("%Y-%m-%d")

report = {
    "generated_at": now.isoformat(),
    "date": today,
    "website": "https://1-seven-lovat-14.vercel.app",
    "traffic": {
        "visitors": "N/A",
        "pageviews": "N/A",
        "top_pages": [],
        "sources": [],
        "note": "需要配置 GA4 后自动获取真实数据"
    },
    "revenue": {
        "estimated_earnings": "N/A",
        "impressions": "N/A",
        "clicks": "N/A",
        "note": "需要配置 AdSense 后自动获取真实数据"
    },
    "status": {
        "site_online": True,
        "ga4_configured": False,
        "adsense_configured": False,
        "gtm_configured": False,
    }
}

# Try to fetch GA4 data
ga4_prop = os.environ.get("GA4_PROPERTY_ID", "")
ga4_token = os.environ.get("GOOGLE_ACCESS_TOKEN", "")

if ga4_prop and ga4_token:
    try:
        import requests
        yesterday = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        headers = {"Authorization": f"Bearer {ga4_token}", "Content-Type": "application/json"}
        resp = requests.post(
            f"https://analyticsdata.googleapis.com/v1beta/properties/{ga4_prop}:runReport",
            headers=,
            json={
                "dateRanges": [{"startDate": yesterday, "endDate": yesterday}],
                "metrics": [
                    {"name": "activeUsers"},
                    {"name": "screenPageViews"},
                    {"name": "averageSessionDuration"},
                ],
            },
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("rows"):
                metrics = data["rows"][0]["metricValues"]
                report["traffic"]["visitors"] = int(metrics[0]["value"])
                report["traffic"]["pageviews"] = int(metrics[1]["value"])
                report["traffic"]["note"] = "GA4 实时数据"
                report["status"]["ga4_configured"] = True
        else:
            print(f"GA4 API error: {resp.status_code}")
    except Exception as e:
        print(f"GA4 fetch failed: {e}")

# Try to fetch AdSense data
adsense_acct = os.environ.get("ADSENSE_ACCOUNT_ID", "")
if adsense_acct and ga4_token:
    try:
        import requests
        yesterday = now - datetime.timedelta(days=1)
        params = {
            "startDate.year": yesterday.year,
            "startDate.month": yesterday.month,
            "startDate.day": yesterday.day,
            "endDate.year": yesterday.year,
            "endDate.month": yesterday.month,
            "endDate.day": yesterday.day,
            "metrics": "ESTIMATED_EARNINGS,IMPRESSIONS,CLICKS",
        }
        resp = requests.get(
            f"https://adsense.googleapis.com/v2/accounts/{adsense_acct}/reports:generate",
            headers={"Authorization": f"Bearer {ga4_token}"},
            params=params,
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("rows"):
                metrics = data["rows"][0]["metricValues"]
                report["revenue"]["estimated_earnings"] = float(metrics[0]["value"])
                report["revenue"]["impressions"] = int(metrics[1]["value"])
                report["revenue"]["clicks"] = int(metrics[2]["value"])
                report["revenue"]["note"] = "AdSense 实时数据"
                report["status"]["adsense_configured"] = True
        else:
            print(f"AdSense API error: {resp.status_code}")
    except Exception as e:
        print(f"AdSense fetch failed: {e}")

# Check if services config exists
svc_file = Path("google_services.json")
if svc_file.exists():
    with open(svc_file) as f:
        svc = json.load(f)
    if svc.get("ga4_measurement_id"):
        report["status"]["ga4_configured"] = True
    if svc.get("adsense_publisher_id"):
        report["status"]["adsense_configured"] = True
    if svc.get("gtm_container_id"):
        report["status"]["gtm_configured"] = True

# Save reports
os.makedirs("reports", exist_ok=True)
report_path = f"reports/daily-{today}.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

with open("reports/latest.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

dashboard_data = {
    "updated": now.isoformat(),
    "traffic": report["traffic"],
    "revenue": report["revenue"],
    "status": report["status"],
}
with open("dashboard-data.json", "w", encoding="utf-8") as f:
    json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

print(f"Daily report generated: {today}")
print(json.dumps(report, ensure_ascii=False, indent=2))