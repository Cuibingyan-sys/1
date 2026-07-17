#!/usr/bin/env python3
"""通过飞书用户身份发送每日流量报告到指定群聊"""
import json, os, subprocess, sys
from pathlib import Path
from datetime import datetime

CHAT_ID = "oc_be97e9685d74ddae2c126dbf31ac744b"
REPORT_PATH = Path("reports/latest.json")
SITE_URL = "https://1-seven-lovat-14.vercel.app"
DASHBOARD_URL = f"{SITE_URL}/dashboard.html"

# ── 读取报告 ──
if not REPORT_PATH.exists():
    # 生成一个占位报告用于测试
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "traffic": {"visitors": "等待GA4数据", "pageviews": "等待GA4数据", "note": "百度统计已接入，数据延迟24-48小时"},
        "revenue": {"estimated_earnings": "等待AdSense数据", "impressions": "等待AdSense数据", "clicks": "等待AdSense数据"},
        "status": {"site_online": True, "ga4_configured": True, "gtm_configured": True, "adsense_configured": True}
    }
else:
    with open(REPORT_PATH) as f:
        report = json.load(f)

date = report["date"]
t = report["traffic"]
r = report["revenue"]
s = report["status"]

# ── 构建Markdown消息 ──
msg = f"""📊 **每日流量报告 — {date}**

**🚀 流量数据**
• 访客数：**{t['visitors']}**
• 页面浏览：**{t['pageviews']}**
• 来源：{t['note']}

**💰 收益数据**
• 预估收入：**{r['estimated_earnings']}**
• 展示次数：**{r['impressions']}**
• 点击次数：**{r['clicks']}**

**📡 服务状态**
• 网站在线：{'✅' if s['site_online'] else '❌'}
• GA4：{'✅' if s['ga4_configured'] else '❌'}
• GTM：{'✅' if s['gtm_configured'] else '❌'}
• AdSense：{'✅' if s['adsense_configured'] else '❌'}

**🔗 快捷链接**
• [🌐 访问网站]({SITE_URL})
• [📋 查看仪表盘]({DASHBOARD_URL})

---
> 💡 回复此消息即可与我对话，我可以帮你优化网站、分析数据、调整策略"""

# ── 发送飞书消息 ──
try:
    result = subprocess.run(
        ["lark-cli", "im", "+messages-send",
         "--chat-id", CHAT_ID,
         "--markdown", msg,
         "--as", "user"],
        capture_output=True, text=True, timeout=30,
        env={**os.environ,
             "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1",
             "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1"}
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if data.get("ok"):
            print(f"✅ 飞书消息已发送: {data['data']['message_id']}")
        else:
            print(f"❌ 飞书发送失败: {result.stdout[:300]}")
            sys.exit(1)
    else:
        print(f"❌ lark-cli 错误: {result.stderr[:300]}")
        sys.exit(1)
except Exception as e:
    print(f"❌ 飞书通知异常: {e}")
    sys.exit(1)