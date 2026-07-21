#!/usr/bin/env python3
"""通过 QQ 邮箱 SMTP 发送每日流量报告"""
import json, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

# 读取最新报告
report_path = Path("reports/latest.json")
if not report_path.exists():
    print("No report found, skipping email")
    exit(0)

with open(report_path) as f:
    report = json.load(f)

# SMTP 配置
smtp_user = os.environ.get("QQ_SMTP_USER", "1906255309@qq.com")
smtp_pass = os.environ.get("QQ_SMTP_PASS", "")
smtp_server = "smtp.qq.com"
smtp_port = 465

if not smtp_pass:
    print("QQ_SMTP_PASS not set, skipping email")
    exit(0)

date = report["date"]
traffic = report["traffic"]
revenue = report["revenue"]
status = report["status"]

# 构建 HTML 邮件
html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 24px;">📊 每日流量报告</h1>
        <p style="margin: 8px 0 0; opacity: 0.9;">{date}</p>
    </div>

    <div style="background: white; padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
        <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 8px;">🚀 流量数据</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 10px; border-bottom: 1px solid #eee; color: #666;">访客数</td><td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; font-size: 18px;">{traffic['visitors']}</td></tr>
            <tr><td style="padding: 10px; border-bottom: 1px solid #eee; color: #666;">页面浏览</td><td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; font-size: 18px;">{traffic['pageviews']}</td></tr>
            <tr><td style="padding: 10px; color: #666;">数据来源</td><td style="padding: 10px; color: #888;">{traffic['note']}</td></tr>
        </table>

        <h2 style="color: #333; border-bottom: 2px solid #f59e0b; padding-bottom: 8px; margin-top: 25px;">💰 收益数据</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 10px; border-bottom: 1px solid #eee; color: #666;">预估收入</td><td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; font-size: 18px; color: #f59e0b;">{revenue['estimated_earnings']}</td></tr>
            <tr><td style="padding: 10px; border-bottom: 1px solid #eee; color: #666;">展示次数</td><td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">{revenue['impressions']}</td></tr>
            <tr><td style="padding: 10px; color: #666;">点击次数</td><td style="padding: 10px; font-weight: bold;">{revenue['clicks']}</td></tr>
        </table>

        <h2 style="color: #333; border-bottom: 2px solid #10b981; padding-bottom: 8px; margin-top: 25px;">📡 服务状态</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">网站在线</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{'✅' if status['site_online'] else '❌'}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">GA4</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{'✅' if status['ga4_configured'] else '❌'}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">GTM</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{'✅' if status['gtm_configured'] else '❌'}</td></tr>
            <tr><td style="padding: 8px;">AdSense</td><td style="padding: 8px;">{'✅' if status['adsense_configured'] else '❌'}</td></tr>
        </table>
    </div>

    <div style="background: #f8f9fa; padding: 15px; border-radius: 0 0 12px 12px; text-align: center; border: 1px solid #e0e0e0; border-top: none;">
        <a href="https://1-seven-lovat-14.vercel.app" style="color: #667eea; text-decoration: none; font-weight: bold;">🌐 访问网站</a>
        <span style="margin: 0 10px; color: #ccc;">|</span>
        <a href="https://1-seven-lovat-14.vercel.app/dashboard-data.json" style="color: #667eea; text-decoration: none;">📋 查看仪表盘数据</a>
        <p style="margin: 10px 0 0; color: #999; font-size: 12px;">此邮件由健康计算器自动发送 · {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
</body>
</html>"""

# 发送邮件
msg = MIMEMultipart("alternative")
msg["Subject"] = f"📊 健康计算器每日流量报告 - {date}"
msg["From"] = smtp_user
msg["To"] = smtp_user

msg.attach(MIMEText(html, "html", "utf-8"))

try:
    server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
    server.login(smtp_user, smtp_pass)
    server.sendmail(smtp_user, [smtp_user], msg.as_string())
    server.quit()
    print(f"Email sent successfully to {smtp_user}")
except Exception as e:
    print(f"Email send failed: {e}")
    exit(1)