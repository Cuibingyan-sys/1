#!/usr/bin/env python3
"""从 GA4 Data API 获取真实流量数据"""
import json, os, sys, datetime
import requests

GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "")
ACCESS_TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN", "")

def fetch_ga4_report():
    if not GA4_PROPERTY_ID or not ACCESS_TOKEN:
        return {"error": "GA4 未配置或 Token 不可用", "note": "需要配置 GA4 后自动获取真实数据"}
    
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    
    # 今日和昨日数据
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    week_ago = today - datetime.timedelta(days=7)
    
    date_range = {
        "startDate": week_ago.isoformat(),
        "endDate": yesterday.isoformat(),
    }
    
    # 核心指标
    request_body = {
        "dateRanges": [date_range],
        "metrics": [
            {"name": "activeUsers"},
            {"name": "screenPageViews"},
            {"name": "averageSessionDuration"},
            {"name": "bounceRate"},
        ],
        "dimensions": [
            {"name": "date"},
        ],
    }
    
    try:
        resp = requests.post(
            f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY_ID}:runReport",
            headers=headers,
            json=request_body,
            timeout=30
        )
        if resp.status_code != 200:
            return {"error": f"GA4 API 错误: {resp.status_code}", "detail": resp.text}
        
        data = resp.json()
        
        # 汇总
        totals = {}
        for row in data.get("rows", []):
            date = row["dimensionValues"][0]["value"]
            metrics = row["metricValues"]
            totals[date] = {
                "visitors": int(metrics[0]["value"]),
                "pageviews": int(metrics[1]["value"]),
                "avg_duration": float(metrics[2]["value"]),
                "bounce_rate": float(metrics[3]["value"]),
            }
        
        # 总访问量
        total_visitors = sum(d["visitors"] for d in totals.values())
        total_pageviews = sum(d["pageviews"] for d in totals.values())
        
        # 今日数据
        today_str = today.isoformat()
        today_data = totals.get(today_str, {"visitors": 0, "pageviews": 0, "avg_duration": 0, "bounce_rate": 0})
        
        return {
            "today": today_data,
            "last_7_days": {
                "total_visitors": total_visitors,
                "total_pageviews": total_pageviews,
                "daily": totals,
            },
            "fetch_time": datetime.datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {"error": str(e)}

def main():
    result = fetch_ga4_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()