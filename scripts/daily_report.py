#!/usr/bin/env python3
"""
每日流量收益报告生成器
从 dashboard-data.json 读取数据，生成 HTML 报告
同时发送邮件到 1906255309@qq.com
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

REPORTS_DIR = Path(__file__).parent.parent / "reports"
DASHBOARD_FILE = Path(__file__).parent.parent / "dashboard-data.json"

def load_data():
    """加载 dashboard 数据"""
    if DASHBOARD_FILE.exists():
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"total_visitors": 0, "total_revenue": 0, "today_visitors": 0, "today_revenue": 0}

def generate_html_report(data, date_str):
    """生成 HTML 格式报告"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>📊 每日报告 - {date_str}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; padding: 20px; }}
.container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
.header {{ background: linear-gradient(135deg, #059669, #047857); color: #fff; padding: 32px; text-align: center; }}
.header h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
.header p {{ opacity: 0.85; font-size: 0.9rem; }}
.metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 24px; }}
.metric {{ background: #f9fafb; border-radius: 12px; padding: 20px; text-align: center; }}
.metric .value {{ font-size: 2rem; font-weight: 700; color: #059669; }}
.metric .label {{ font-size: 0.85rem; color: #6b7280; margin-top: 4px; }}
.metric.revenue .value {{ color: #d97706; }}
.section {{ padding: 0 24px 24px; }}
.section h2 {{ font-size: 1.1rem; color: #1f2937; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }}
.tips {{ background: #fefce8; border-radius: 12px; padding: 16px; margin: 0 24px 24px; }}
.tips h3 {{ font-size: 0.95rem; color: #92400e; margin-bottom: 8px; }}
.tips ul {{ padding-left: 20px; font-size: 0.85rem; color: #78716c; line-height: 1.8; }}
.footer {{ text-align: center; padding: 16px; font-size: 0.75rem; color: #9ca3af; border-top: 1px solid #e5e7eb; }}
.footer a {{ color: #059669; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 健康计算器 每日报告</h1>
    <p>{date_str}</p>
  </div>
  <div class="metrics">
    <div class="metric">
      <div class="value">{data.get('today_visitors', 0):,}</div>
      <div class="label">👥 今日访客</div>
    </div>
    <div class="metric revenue">
      <div class="value">¥{data.get('today_revenue', 0):.2f}</div>
      <div class="label">💰 今日收益</div>
    </div>
    <div class="metric">
      <div class="value">{data.get('total_visitors', 0):,}</div>
      <div class="label">📈 累计访客</div>
    </div>
    <div class="metric revenue">
      <div class="value">¥{data.get('total_revenue', 0):.2f}</div>
      <div class="label">💎 累计收益</div>
    </div>
  </div>
  <div class="section">
    <h2>📈 收益来源</h2>
    <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
      <tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">Google AdSense</td><td style="text-align:right;padding:8px;">¥{data.get('adsense_revenue', 0):.2f}</td></tr>
      <tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">京东联盟</td><td style="text-align:right;padding:8px;">¥{data.get('jd_revenue', 0):.2f}</td></tr>
      <tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">用户打赏</td><td style="text-align:right;padding:8px;">¥{data.get('donate_revenue', 0):.2f}</td></tr>
      <tr style="font-weight:700;"><td style="padding:8px;">合计</td><td style="text-align:right;padding:8px;">¥{data.get('today_revenue', 0):.2f}</td></tr>
    </table>
  </div>
  <div class="section">
    <h2>🌐 流量来源 TOP 5</h2>
    <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
      {generate_source_rows(data.get('sources', []))}
    </table>
  </div>
  <div class="tips">
    <h3>💡 今日优化建议</h3>
    <ul>
      <li>检查新部署的邮件订阅弹窗是否正常弹出</li>
      <li>查看浮动广告条点击率</li>
      <li>关注夏季减肥攻略页面的京东联盟转化</li>
      <li>如有新访客来源，及时在对应平台更新内容</li>
    </ul>
  </div>
  <div class="footer">
    健康计算器 · <a href="https://1-seven-lovat-14.vercel.app">网站</a> · <a href="https://github.com/Cuibingyan-sys/1">GitHub</a><br>
    自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} (UTC)
  </div>
</div>
</body>
</html>"""
    return html

def generate_source_rows(sources):
    if not sources:
        return '<tr><td colspan="2" style="padding:8px;text-align:center;color:#9ca3af;">暂无数据</td></tr>'
    rows = ''
    for s in sources[:5]:
        rows += f'<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">{s.get("name", "Unknown")}</td><td style="text-align:right;padding:8px;">{s.get("visitors", 0):,}</td></tr>'
    return rows

def main():
    date_str = datetime.now().strftime('%Y年%m月%d日')
    data = load_data()
    
    # 生成 HTML 报告
    html = generate_html_report(data, date_str)
    filename = f"report-{datetime.now().strftime('%Y-%m-%d')}.html"
    filepath = REPORTS_DIR / filename
    
    REPORTS_DIR.mkdir(exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 报告已生成: {filepath}")
    print(f"   今日访客: {data.get('today_visitors', 0):,}")
    print(f"   今日收益: ¥{data.get('today_revenue', 0):.2f}")

if __name__ == '__main__':
    main()