#!/usr/bin/env python3
"""通过飞书自定义机器人 Webhook 发送每日流量报告"""
import json, os, requests
from pathlib import Path
from datetime import datetime

# 读取最新报告
report_path = Path("reports/latest.json")
if not report_path.exists():
    print("No report found, skipping Feishu notification")
    exit(0)

with open(report_path) as f:
    report = json.load(f)

webhook_url = os.environ.get("FEISHU_WEBHOOK_URL", "")
if not webhook_url:
    print("FEISHU_WEBHOOK_URL not set, skipping Feishu notification")
    exit(0)

date = report["date"]
traffic = report["traffic"]
revenue = report["revenue"]
status = report["status"]

# 飞书消息卡片
card = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": f"📊 每日流量报告 - {date}"},
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**🚀 流量数据**\n访客数：**{traffic['visitors']}**  |  页面浏览：**{traffic['pageviews']}**\n数据来源：{traffic['note']}"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**💰 收益数据**\n预估收入：**{revenue['estimated_earnings']}**  |  展示：**{revenue['impressions']}**  |  点击：**{revenue['clicks']}**"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**📡 服务状态**\n网站：{'✅' if status['site_online'] else '❌'}  GA4：{'✅' if status['ga4_configured'] else '❌'}  GTM：{'✅' if status['gtm_configured'] else '❌'}  AdSense：{'✅' if status['adsense_configured'] else '❌'}"
                }
            },
            {"tag": "hr"},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "🌐 访问网站"},
                        "url": "https://1-seven-lovat-14.vercel.app",
                        "type": "default"
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "📋 查看数据"},
                        "url": "https://1-seven-lovat-14.vercel.app/dashboard-data.json",
                        "type": "default"
                    }
                ]
            }
        ]
    }
}

try:
    resp = requests.post(webhook_url, json=card, timeout=15)
    if resp.status_code == 200:
        result = resp.json()
        if result.get("code") == 0:
            print("Feishu notification sent successfully")
        else:
            print(f"Feishu API error: {result}")
    else:
        print(f"Feishu HTTP error: {resp.status_code} {resp.text}")
except Exception as e:
    print(f"Feishu notification failed: {e}")
    exit(1)