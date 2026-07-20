#!/usr/bin/env python3
"""
通过飞书 Bot API 发送每日流量/收益报告
用于 GitHub Actions（不依赖 lark-cli）

需要的 GitHub Secrets:
  FEISHU_APP_ID      - 飞书应用 App ID
  FEISHU_APP_SECRET  - 飞书应用 App Secret  
  FEISHU_CHAT_ID     - 飞书群聊 ID（可选，默认使用代码中的）
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

# ── 配置 ──
APP_ID = os.environ.get("FEISHU_APP_ID", "")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "oc_c449875cc7737a8c2295a6310c482023")
SITE_URL = "https://1-seven-lovat-14.vercel.app"
DASHBOARD_URL = f"{SITE_URL}/dashboard.html"

# 尝试多个路径找报告文件
REPORT_PATHS = [
    Path("reports/latest.json"),
    Path("../reports/latest.json"),
    Path("reports/daily-{}.json".format(datetime.now().strftime("%Y-%m-%d"))),
]

def get_tenant_token():
    """获取飞书 tenant_access_token"""
    if not APP_ID or not APP_SECRET:
        print("❌ 缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET 环境变量")
        return None
    
    data = json.dumps({
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("code") == 0:
            return result["tenant_access_token"]
        print(f"❌ 获取 token 失败: {result}")
    except Exception as e:
        print(f"❌ 获取 token 异常: {e}")
    return None

def send_message(token, content):
    """发送消息到飞书群"""
    data = json.dumps({
        "receive_id": CHAT_ID,
        "msg_type": "interactive",
        "content": json.dumps(content)
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("code") == 0:
            print(f"✅ 飞书消息已发送: {result['data']['message_id']}")
            return True
        print(f"❌ 发送失败: {result}")
    except Exception as e:
        print(f"❌ 发送异常: {e}")
    return False

def load_report():
    """加载报告数据"""
    for p in REPORT_PATHS:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return None

def fmt(val):
    """格式化数值"""
    if val is None or val in ("N/A", "等待数据", "等待GA4数据", "等待AdSense数据", ""):
        return "⏳ 等待中"
    if isinstance(val, (int, float)):
        if val == 0:
            return "0"
        return f"{val:,}"
    return str(val)

def build_card(report):
    """构建飞书卡片消息"""
    if not report:
        return build_empty_card()
    
    t = report.get("traffic", {})
    r = report.get("revenue", {})
    s = report.get("status", {})
    date_str = report.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    visitors = fmt(t.get("visitors", "N/A"))
    pageviews = fmt(t.get("pageviews", "N/A"))
    earnings = fmt(r.get("estimated_earnings", "N/A"))
    impressions = fmt(r.get("impressions", "N/A"))
    clicks = fmt(r.get("clicks", "N/A"))
    
    ga4_ok = s.get("ga4_configured", False)
    adsense_ok = s.get("adsense_configured", False)
    site_ok = s.get("site_online", True)
    
    return {
        "header": {
            "title": {"tag": "plain_text", "content": f"📊 每日报告 · {date_str}"},
            "template": "green"
        },
        "elements": [
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**🚀 流量数据**\n👥 访客：**{visitors}**　📄 浏览：**{pageviews}**"}
            },
            {
                "tag": "div", 
                "text": {"tag": "lark_md", "content": f"**💰 收益数据**\n💵 预估收入：**{earnings}**　👁 展示：**{impressions}**　👆 点击：**{clicks}**"}
            },
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**📡 服务状态**\n{'✅' if site_ok else '❌'} 网站 {'✅' if ga4_ok else '❌'} GA4 {'✅' if adsense_ok else '❌'} AdSense"}
            },
            {"tag": "hr"},
            {
                "tag": "action",
                "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "🌐 访问网站"}, "url": SITE_URL, "type": "default"},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "📋 查看仪表盘"}, "url": DASHBOARD_URL, "type": "primary"}
                ]
            },
            {
                "tag": "note",
                "elements": [{"tag": "plain_text", "content": "💡 在飞书机器人对话中发送 /traffic /revenue /dashboard 随时查询数据"}]
            }
        ]
    }

def build_empty_card():
    """构建空数据卡片"""
    return {
        "header": {
            "title": {"tag": "plain_text", "content": f"📊 每日报告 · {datetime.now().strftime('%Y-%m-%d')}"},
            "template": "yellow"
        },
        "elements": [
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": "⏳ **数据收集中...**\n\nGA4 和 AdSense 数据有 24-48 小时延迟。\n网站刚上线，流量数据正在积累中。"}
            },
            {"tag": "hr"},
            {
                "tag": "action",
                "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "🌐 访问网站"}, "url": SITE_URL, "type": "default"},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "📋 查看仪表盘"}, "url": DASHBOARD_URL, "type": "primary"}
                ]
            }
        ]
    }

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📊 飞书每日报告发送")
    
    # 加载报告
    report = load_report()
    if report:
        print(f"   报告日期: {report.get('date', 'unknown')}")
    else:
        print("   报告文件未找到，使用空数据")
    
    # 获取 token
    token = get_tenant_token()
    if not token:
        print("❌ 无法获取飞书 Token，请检查 FEISHU_APP_ID / FEISHU_APP_SECRET")
        sys.exit(1)
    
    # 构建并发送卡片
    card = build_card(report)
    if not send_message(token, card):
        print("❌ 飞书消息发送失败")
        sys.exit(1)
    
    print("✅ 完成")

if __name__ == "__main__":
    main()