#!/usr/bin/env python3
"""从 AdSense Reporting API 获取真实收益数据"""
import json, os, sys, datetime
import requests

ADSENSE_ACCOUNT_ID = os.environ.get("ADSENSE_ACCOUNT_ID", "")
ACCESS_TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN", "")

def fetch_adsense_report():
    if not ADSENSE_ACCOUNT_ID or not ACCESS_TOKEN:
        return {"error": "AdSense 未配置或 Token 不可用", "note": "需要配置 AdSense 后自动获取真实数据"}
    
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)
    
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    params = {
        "startDate.year": week_ago.year,
        "startDate.month": week_ago.month,
        "startDate.day": week_ago.day,
        "endDate.year": today.year,
        "endDate.month": today.month,
        "endDate.day": today.day,
        "metrics": "ESTIMATED_EARNINGS,IMPRESSIONS,CLICKS,PAGE_VIEWS_RPM",
        "dimensions": "DATE",
    }
    
    try:
        resp = requests.get(
            f"https://adsense.googleapis.com/v2/accounts/{ADSENSE_ACCOUNT_ID}/reports:generate",
            headers=headers,
            params=params,
            timeout=30
        )
        if resp.status_code != 200:
            return {"error": f"AdSense API 错误: {resp.status_code}", "detail": resp.text}
        
        data = resp.json()
        
        daily = {}
        total_earnings = 0.0
        total_impressions = 0
        total_clicks = 0
        
        for row in data.get("rows", []):
            date = row["dimensionValues"][0]["value"]
            metrics = row["metricValues"]
            earnings = float(metrics[0]["value"])
            impressions = int(metrics[1]["value"])
            clicks = int(metrics[2]["value"])
            rpm = float(metrics[3]["value"]) if len(metrics) > 3 else 0
            
            daily[date] = {
                "earnings": round(earnings, 4),
                "impressions": impressions,
                "clicks": clicks,
                "rpm": round(rpm, 2),
            }
            total_earnings += earnings
            total_impressions += impressions
            total_clicks += clicks
        
        return {
            "last_7_days": {
                "total_earnings": round(total_earnings, 4),
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "avg_rpm": round(total_earnings / max(total_impressions, 1) * 1000, 2),
            },
            "daily": daily,
            "fetch_time": datetime.datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {"error": str(e)}

def main():
    result = fetch_adsense_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()