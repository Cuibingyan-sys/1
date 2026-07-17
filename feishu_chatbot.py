#!/usr/bin/env python3
"""
飞书双向对话机器人 v2
后台运行: nohup python3 feishu_chatbot.py &
"""
import subprocess, json, os, sys, time, threading
from datetime import datetime

USER_OPEN_ID = "ou_2a31a00927cb6a1d9cdf5de1c20351f3"
USER_NAME = "崔冰堰"
SITE_URL = "https://1-seven-lovat-14.vercel.app"
DASHBOARD_URL = f"{SITE_URL}/dashboard.html"
SEEN_EVENTS = set()
MAX_SEEN = 5000

ENV = {**os.environ,
       "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1",
       "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1"}

def send_message(chat_id, text):
    """发送飞书消息"""
    try:
        result = subprocess.run(
            ["lark-cli", "im", "+messages-send",
             "--chat-id", chat_id,
             "--markdown", text,
             "--as", "bot"],
            capture_output=True, text=True, timeout=15, env=ENV
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("ok"):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 已回复")
                return True
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 回复失败: {result.stderr[:200]}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 发送异常: {e}")
    return False

def handle_message(event):
    content = event.get("content", "").strip()
    chat_id = event.get("chat_id", "")
    message_type = event.get("message_type", "text")
    
    if message_type == "interactive":
        send_message(chat_id, "抱歉，我还不能处理卡片消息，请发送文字～")
        return
    if not content:
        return
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📩 「{content[:80]}」")
    content_lower = content.lower()
    
    if any(kw in content_lower for kw in ["你好", "hello", "hi", "在吗", "在不在"]):
        send_message(chat_id, f"""👋 **你好，{USER_NAME}！**

我是你的 **AI数字工厂** 专属助手，可以帮你：

• 📊 **查看数据**：说"流量""收益""报告"
• 🌐 **网站管理**：说"网站状态""仪表盘"
• 🛠️ **优化建议**：说"优化""SEO""变现"
• 📝 **每日报告**：说"今天报告"

现在想聊什么？""")
    
    elif any(kw in content_lower for kw in ["流量", "访客", "uv", "pv", "数据"]):
        send_message(chat_id, f"""📊 **流量数据概览**

百度统计和 GA4 已接入，数据正在收集中。

• **实时数据**：[百度统计后台](https://tongji.baidu.com)
• **GA4**：[Google Analytics](https://analytics.google.com)
• **仪表盘**：[{DASHBOARD_URL}]({DASHBOARD_URL})

> 💡 数据有 24-48 小时延迟，明天 08:00 收到第一份完整报告""")
    
    elif any(kw in content_lower for kw in ["收益", "收入", "赚钱", "变现", "佣金", "钱"]):
        send_message(chat_id, f"""💰 **收益与变现**

当前变现渠道：
• **京东联盟**：商品推荐佣金 (ID: 2038380499)
• **AdSense**：展示广告收益 (ca-pub-5918744)
• **打赏**：用户自愿赞赏

**变现时机：**
• 日均 100+ 访客 → 京东联盟审核通过率高
• 日均 500+ 访客 → AdSense 稳定收入
• 日均 1000+ 访客 → 可接品牌直投广告

现在处于数据积累阶段，坚持发布优质内容！""")
    
    elif any(kw in content_lower for kw in ["报告", "日报", "今日", "今天"]):
        try:
            subprocess.run(["python3", "generate_daily_report.py"],
                          capture_output=True, timeout=30, cwd="/workspace/1")
            subprocess.run(["python3", "send_feishu_notification.py"],
                          capture_output=True, timeout=30, cwd="/workspace/1")
            send_message(chat_id, "📊 报告已生成并发送给你，请查看上一条消息～")
        except Exception as e:
            send_message(chat_id, f"报告生成失败，请稍后再试")
    
    elif any(kw in content_lower for kw in ["优化", "seo", "建议", "改进"]):
        send_message(chat_id, f"""🛠️ **SEO & 优化建议**

**已完成：**
• ✅ 百度统计 + GA4 双数据
• ✅ 京东联盟原生广告位
• ✅ 信任条 + 社交证明
• ✅ 每日自动监控

**下一步：**
1. 百度搜索资源平台提交网站
2. Google Search Console 验证
3. 每周 1-2 篇 SEO 文章
4. 知乎/小红书/抖音引流

需要我帮你写新文章吗？""")
    
    elif any(kw in content_lower for kw in ["网站", "状态", "在线", "dashboard", "仪表盘", "地址"]):
        send_message(chat_id, f"""🌐 **网站状态**

• 网站：[{SITE_URL}]({SITE_URL})
• 仪表盘：[{DASHBOARD_URL}]({DASHBOARD_URL})
• 仓库：[GitHub](https://github.com/Cuibingyan-sys/1)

所有配置已完成 ✅""")
    
    elif any(kw in content_lower for kw in ["帮助", "help", "功能", "能做什么"]):
        send_message(chat_id, f"""🤖 **功能列表**

• 说"**流量**" → 查看数据
• 说"**收益**" → 变现分析
• 说"**报告**" → 生成报告
• 说"**优化**" → SEO 建议
• 说"**网站**" → 网站状态
• 说"**帮助**" → 此列表

试试对我说点什么吧～""")
    
    else:
        send_message(chat_id, f"""🤔 收到：「{content[:50]}」

我能处理的话题：**流量 / 收益 / 报告 / 优化 / 网站 / 帮助**

说"帮助"查看完整功能～""")

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 飞书对话机器人启动")
    print(f"   用户: {USER_NAME} ({USER_OPEN_ID})")
    sys.stdout.flush()
    
    jq_filter = f'select(.sender_id=="{USER_OPEN_ID}" and (.message_type=="text" or .message_type=="post")) | {{chat_id, message_id, content, message_type, create_time}}'
    
    proc = subprocess.Popen(
        ["lark-cli", "event", "consume", "im.message.receive_v1",
         "--as", "bot", "--jq", jq_filter],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, env=ENV
    )
    
    import select
    ready = False
    deadline = time.time() + 60
    stderr_lines = []
    while time.time() < deadline:
        readable, _, _ = select.select([proc.stderr], [], [], 1.0)
        if readable:
            line = proc.stderr.readline()
            if not line:
                break
            stderr_lines.append(line.strip())
            if "[event] ready" in line:
                ready = True
                break
            if "error" in line.lower() and "{" in line:
                print(f"[stderr] {line.strip()}", flush=True)
    
    if not ready:
        print("❌ 事件监听启动失败")
        for l in stderr_lines[-5:]:
            print(f"  {l}")
        proc.kill()
        return
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 事件监听就绪，等待消息...")
    sys.stdout.flush()
    
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                msg_id = event.get("message_id", "")
                if msg_id and msg_id not in SEEN_EVENTS:
                    SEEN_EVENTS.add(msg_id)
                    if len(SEEN_EVENTS) > MAX_SEEN:
                        SEEN_EVENTS.clear()
                    handle_message(event)
            except json.JSONDecodeError:
                pass
    except KeyboardInterrupt:
        pass
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 👋 机器人已停止")

if __name__ == "__main__":
    main()