#!/usr/bin/env python3
"""
飞书AI对话机器人 v3.0 — 联网智能问答
"""
import subprocess, json, os, sys, time, re, urllib.request, urllib.parse, ssl
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

# ── 消息发送 ──
def send_message(chat_id, text, msg_type="markdown"):
    try:
        args = ["lark-cli", "im", "+messages-send", "--chat-id", chat_id,
                "--as", "bot"]
        if msg_type == "text":
            args += ["--msg-type", "text", "--content", text]
        else:
            args += ["--markdown", text]
        result = subprocess.run(args, capture_output=True, text=True, timeout=15, env=ENV)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("ok"):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 已回复")
                return True
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 回复失败: {result.stderr[:200]}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 发送异常: {e}")
    return False

# ── 联网搜索 ──
def web_search(query, max_results=3):
    """使用 DuckDuckGo 搜索，返回结果列表"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AIBot/1.0)"
        })
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        # 解析搜索结果
        results = []
        for m in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
            link = urllib.parse.unquote(m.group(1))
            # 清理DuckDuckGo的重定向链接
            if 'uddg=' in link:
                link = re.search(r'uddg=(.*?)(?:&|$)', link)
                if link:
                    link = urllib.parse.unquote(link.group(1))
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            if title and link:
                results.append({"title": title, "url": link})
        # 提取摘要
        snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        for i, snip in enumerate(snippets[:len(results)]):
            results[i]["snippet"] = re.sub(r'<[^>]+>', '', snip).strip()
        return results[:max_results]
    except Exception as e:
        print(f"[search] 搜索失败: {e}")
        return []

# ── 意图识别 ──
def classify_intent(content):
    """识别用户意图，返回 (category, sub_category)"""
    c = content.lower()
    
    # 问候
    if any(kw in c for kw in ["你好", "hello", "hi", "在吗", "在不在", "嗨"]):
        if "?" in c or "？" in c or len(c) > 10:
            return "general"  # 带问号的问候可能是真实问题
        return "greeting"
    
    # 网站相关
    if any(kw in c for kw in ["流量", "访客", "uv", "pv", "多少人", "访问"]):
        return "traffic"
    if any(kw in c for kw in ["收益", "收入", "赚钱", "变现", "佣金", "钱", "广告费"]):
        return "revenue"
    if any(kw in c for kw in ["报告", "日报", "今日", "总结", "汇总"]):
        return "report"
    if any(kw in c for kw in ["网站地址", "网站链接", "网址", "打开网站"]):
        return "site"
    if any(kw in c for kw in ["仪表盘", "dashboard", "后台"]):
        return "dashboard"
    
    # SEO / 优化
    if any(kw in c for kw in ["seo", "排名", "搜索", "关键词", "优化网站", "百度收录", "google收录"]):
        return "seo"
    if any(kw in c for kw in ["写文章", "写内容", "生成文章", "帮写", "文案"]):
        return "write_article"
    if any(kw in c for kw in ["推广", "引流", "涨粉", "吸粉", "裂变", "营销"]):
        return "marketing"
    
    # 健康/健身（网站主题）
    if any(kw in c for kw in ["bmi", "体脂", "减肥", "减脂", "增肌", "健身", "运动", "饮食", "热量", "卡路里", "蛋白", "蛋白质", "体重", "瘦身", "健康"]):
        return "health"
    
    # 技术/开发
    if any(kw in c for kw in ["代码", "html", "css", "js", "python", "编程", "bug", "部署", "服务器", "域名", "github", "vercel", "技术"]):
        return "tech"
    
    # 帮助
    if any(kw in c for kw in ["帮助", "help", "功能", "能做什么", "你会什么", "怎么用"]):
        return "help"
    
    # 广告/变现
    if any(kw in c for kw in ["广告", "ad", "adsense", "投放", "联盟", "京东"]):
        return "ads"
    
    # 默认：联网搜索
    return "general"

# ── 智能回复 ──
def smart_reply(content, chat_id):
    intent = classify_intent(content)
    
    if intent == "greeting":
        send_message(chat_id, f"""👋 **你好，{USER_NAME}！**

我是搭载了联网搜索的 **AI数字工厂** 智能助手。

**我可以帮你：**
• 📊 网站监控：「流量」「收益」「报告」
• 🛠️ SEO优化：「优化」「推广」「写文章」
• 💪 健康知识：「怎么减肥」「增肌吃什么」
• 💻 技术问题：「怎么部署网站」
• 🌐 **随便问**：任何问题我都可以联网搜索找答案！

试试问我点什么吧～""")
        return
    
    if intent == "traffic":
        send_message(chat_id, f"""📊 **流量数据**

百度统计 + GA4 + GTM 已全部接入。

• 数据延迟：24-48 小时
• 实时数据：[百度统计](https://tongji.baidu.com) | [GA4](https://analytics.google.com)
• 仪表盘：[{DASHBOARD_URL}]({DASHBOARD_URL})

> 💡 每天 08:00 / 16:00 自动推送完整报告""")
        return
    
    if intent == "revenue":
        send_message(chat_id, f"""💰 **收益与变现**

**已在运行的变现渠道：**
• 京东联盟 (ID: 2038380499) — 商品佣金
• AdSense (ca-pub-5918744) — 展示广告
• 打赏 — 支付宝/微信

**变现时机建议：**
• 日均 100+ 访客 → 京东联盟审核通过
• 日均 500+ 访客 → AdSense 稳定收入 ¥10-50/天
• 日均 1000+ 访客 → 可接品牌直投

目前处于数据积累期，坚持更新内容！""")
        return
    
    if intent == "report":
        try:
            subprocess.run(["python3", "generate_daily_report.py"],
                          capture_output=True, timeout=30, cwd="/workspace/1")
            subprocess.run(["python3", "send_feishu_notification.py"],
                          capture_output=True, timeout=30, cwd="/workspace/1")
            send_message(chat_id, "📊 报告已生成并发送给你！")
        except:
            send_message(chat_id, "报告生成失败，请稍后再试")
        return
    
    if intent == "site":
        send_message(chat_id, f"🌐 网站：[{SITE_URL}]({SITE_URL})")
        return
    
    if intent == "dashboard":
        send_message(chat_id, f"📋 仪表盘：[{DASHBOARD_URL}]({DASHBOARD_URL})")
        return
    
    if intent == "seo":
        send_message(chat_id, f"""🛠️ **SEO 优化状态**

**已完成：**
• ✅ 百度统计 + GA4 双数据接入
• ✅ Google Search Console 验证
• ✅ 全站 canonical + og 标签
• ✅ 6 篇 SEO 文章发布
• ✅ 京东联盟原生广告位

**建议下一步：**
1. 百度搜索资源平台提交 sitemap
2. 每周更新 1-2 篇原创文章
3. 知乎/小红书/抖音同步分发
4. 外链建设（行业论坛、博客互链）

需要我帮你写新文章吗？""")
        return
    
    if intent == "marketing":
        send_message(chat_id, f"""📢 **推广引流建议**

**免费渠道：**
• 知乎 — 回答健康/健身话题，带网站链接
• 小红书 — 发健康计算工具测评笔记
• 抖音 — 拍"3秒测出你的BMI"短视频
• 百度贴吧 — 健身吧/减肥吧互动

**付费渠道（等流量起来后）：**
• 百度竞价 — 投"BMI计算器"关键词
• 抖音 DOU+ — 投放爆款视频

**关键指标：** 目标 3 个月内日均 1000+ 访客""")
        return
    
    if intent == "health":
        send_message(chat_id, "🔍 让我搜索最新信息...")
        results = web_search(content, 3)
        if results:
            reply = f"💪 **关于「{content[:40]}」**\n\n"
            for i, r in enumerate(results):
                reply += f"**{i+1}. {r['title']}**\n{r['snippet'][:150]}...\n🔗 {r['url']}\n\n"
            reply += f"💡 *你也可以试试我们网站上的健康计算工具：[{SITE_URL}]({SITE_URL})*"
            send_message(chat_id, reply)
        else:
            send_message(chat_id, f"💪 关于健康问题，建议你试试我们的免费计算工具：\n\n• BMI 计算器：{SITE_URL}/bmi.html\n• 卡路里计算：{SITE_URL}/calorie.html\n• 体脂率估算：{SITE_URL}/body-fat.html")
        return
    
    if intent == "tech":
        send_message(chat_id, "🔍 搜索技术资料中...")
        results = web_search(content, 3)
        if results:
            reply = f"💻 **关于「{content[:40]}」**\n\n"
            for i, r in enumerate(results):
                reply += f"**{i+1}. {r['title']}**\n{r['snippet'][:150]}...\n🔗 {r['url']}\n\n"
            send_message(chat_id, reply)
        else:
            send_message(chat_id, f"💻 关于这个问题，你可以去以下网站查找：\n\n• [Stack Overflow](https://stackoverflow.com)\n• [GitHub](https://github.com)\n• [MDN Web Docs](https://developer.mozilla.org)")
        return
    
    if intent == "help":
        send_message(chat_id, f"""🤖 **AI数字工厂 · 功能大全**

**📊 网站监控**
• 流量 / 收益 / 报告 / 仪表盘

**🛠️ 运营优化**
• SEO / 推广 / 广告 / 写文章

**💪 健康知识**（联网搜索）
• 减肥 / 增肌 / 饮食 / 健身

**💻 技术问答**（联网搜索）
• 代码 / 部署 / 域名 / GitHub

**🌐 随便问**
• 任何问题我都能联网搜索回答！

现在试试问我点什么吧～""")
        return
    
    if intent == "ads":
        send_message(chat_id, f"""📢 **广告与变现**

**当前广告位：**
• 京东联盟原生广告 — 4 个产品卡片
• AdSense 自动广告 — 页面展示广告
• 全站 11 个页面已部署 AdSense 代码

**数据：**
• AdSense ID: ca-pub-5918744
• 京东联盟 ID: 2038380499
• 百度统计 ID: ed8ab485d1d0f7834eec48d97566623c

**下一步：** 等 AdSense 审核通过后自动展示广告""")
        return
    
    if intent == "write_article":
        send_message(chat_id, f"""📝 **文章创作**

我可以帮你写以下类型的 SEO 文章：

• 健康科普类（BMI、体脂率、卡路里）
• 产品评测类（体脂秤、运动手环）
• 教程指南类（如何减肥、健身计划）
• 对比推荐类（蛋白粉选购指南）

告诉我你想写什么主题？比如「写一篇关于如何科学减肥的1500字文章」""")
        return
    
    # ── 通用问题：联网搜索 ──
    send_message(chat_id, f"🔍 正在搜索「{content[:60]}」...")
    results = web_search(content, 3)
    
    if results:
        reply = f"🔍 **关于「{content[:50]}」的搜索结果**\n\n"
        for i, r in enumerate(results):
            snippet = r.get('snippet', '')[:200]
            reply += f"**{i+1}. [{r['title']}]({r['url']})**\n{snippet}\n\n"
        reply += "---\n💡 *你可以继续问我任何问题，我会联网搜索最新信息*"
        send_message(chat_id, reply)
    else:
        send_message(chat_id, f"""🤔 关于「{content[:60]}」，我暂时没找到相关信息。

你可以试试：
• 换个角度提问
• 问我关于网站流量、收益、SEO、健康、技术等问题
• 说「帮助」查看完整功能""")

# ── 主循环 ──
def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 AI数字工厂 v3.0 启动")
    print(f"   用户: {USER_NAME} | 联网搜索: 已启用")
    sys.stdout.flush()
    
    jq_filter = f'select(.sender_id=="{USER_OPEN_ID}" and (.message_type=="text" or .message_type=="post")) | {{chat_id, message_id, content, message_type}}'
    
    proc = subprocess.Popen(
        ["lark-cli", "event", "consume", "im.message.receive_v1",
         "--as", "bot", "--jq", jq_filter],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, env=ENV
    )
    
    import select
    ready = False
    deadline = time.time() + 60
    while time.time() < deadline:
        readable, _, _ = select.select([proc.stderr], [], [], 1.0)
        if readable:
            line = proc.stderr.readline()
            if not line:
                break
            if "[event] ready" in line:
                ready = True
                break
            if "{" in line:
                try:
                    err = json.loads(line.strip())
                    if not err.get("ok", True):
                        print(f"❌ 启动错误: {err}", flush=True)
                        proc.kill()
                        return
                except:
                    pass
    
    if not ready:
        print("❌ 启动失败")
        proc.kill()
        return
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 已就绪，等待消息...")
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
                    content = event.get("content", "").strip()
                    chat_id = event.get("chat_id", "")
                    if content:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📩 「{content[:80]}」")
                        smart_reply(content, chat_id)
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
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 👋 已停止")

if __name__ == "__main__":
    main()