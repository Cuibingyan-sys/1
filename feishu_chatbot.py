#!/usr/bin/env python3
"""
飞书AI对话机器人 v4.0 — DeepSeek V4 驱动 + 文件操作 + 对话记忆
免费额度: 新用户注册 DeepSeek 送 500万 tokens
"""

import subprocess, json, os, sys, time, re, ssl, hashlib, glob as glob_mod
import urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════
# 配置
# ══════════════════════════════════════════

USER_OPEN_ID = "ou_2a31a00927cb6a1d9cdf5de1c20351f3"
USER_NAME = "崔冰堰"
SITE_URL = "https://1-seven-lovat-14.vercel.app"
DASHBOARD_URL = f"{SITE_URL}/dashboard.html"
WORKSPACE = "/workspace/1"
CONFIG_FILE = f"{WORKSPACE}/bot_config.json"

# DeepSeek API 配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"  # V3, 等V4正式上线后改为 deepseek-v4-flash

# 对话记忆
MAX_HISTORY = 20  # 保留最近 20 轮对话
conversation_history = []

# 去重
SEEN_EVENTS = set()
MAX_SEEN = 5000

ENV = {**os.environ,
       "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1",
       "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1"}

# ══════════════════════════════════════════
# 配置管理
# ══════════════════════════════════════════

def load_config():
    """加载API密钥配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_api_key():
    """获取 DeepSeek API key"""
    config = load_config()
    return config.get("deepseek_api_key", "")

# ══════════════════════════════════════════
# 系统提示词
# ══════════════════════════════════════════

SYSTEM_PROMPT = f"""你是「AI数字工厂」的智能助手，运行在飞书机器人上。你的主人是{USER_NAME}，一位网站站长。

## 关于网站
- 网站名称：健康计算器
- 网址：{SITE_URL}
- 功能：BMI计算器、卡路里计算器、基础代谢率(BMR)、体脂率估算、理想体重计算
- 已配置：百度统计(ed8ab485d1d0f7834eec48d97566623c)、GA4(G-9HDK6XWY7J)、GTM(GTM-N26FR57S)、AdSense(ca-pub-5918744)、京东联盟(2038380499)
- 部署：GitHub(Cuibingyan-sys/1) → Vercel 自动部署
- 仪表盘：{DASHBOARD_URL}

## 你的能力
1. **网站管理**：查看流量、收益、生成报告、SEO优化建议
2. **内容创作**：写SEO文章、推广文案、产品评测
3. **文件操作**：主人可以通过命令让你读写文件
4. **知识问答**：任何问题都可以回答，包括健康、技术、商业等
5. **网站推广**：知乎/小红书/抖音/SEO策略建议

## 文件操作命令（主人可以用的）
- /read 文件名 — 读取文件内容
- /write 文件名 — 写入文件（后面跟内容）
- /list — 列出工作目录文件
- /search 关键词 — 搜索文件内容
- /report — 生成并发送流量报告
- /config — 查看当前配置

## 回复风格
- 使用Markdown格式（飞书支持）
- 简洁明了，不啰嗦
- 中文为主，专业术语可用英文
- 适当使用emoji增加可读性
- 涉及网站操作时给出具体可执行的建议

## 重要规则
- 你是{USER_NAME}的专属助手，称呼她为"主人"或直接回答问题
- 如果不确定的事情，诚实说不知道，不要编造
- 涉及修改网站文件的操作，先确认再执行
- 保持友好、专业的语气"""

# ══════════════════════════════════════════
# 消息发送
# ══════════════════════════════════════════

def send_message(chat_id, text, msg_type="markdown"):
    """发送消息到飞书"""
    try:
        # 飞书消息最大 4096 字符，超长分段发送
        if len(text) > 3800:
            parts = []
            current = ""
            for line in text.split("\n"):
                if len(current) + len(line) + 1 > 3800:
                    parts.append(current)
                    current = line
                else:
                    current += ("\n" + line) if current else line
            if current:
                parts.append(current)
            
            for i, part in enumerate(parts):
                prefix = f"({i+1}/{len(parts)})\n" if len(parts) > 1 else ""
                args = ["lark-cli", "im", "+messages-send", "--chat-id", chat_id,
                        "--as", "bot"]
                if msg_type == "text":
                    args += ["--msg-type", "text", "--content", prefix + part]
                else:
                    args += ["--markdown", prefix + part]
                subprocess.run(args, capture_output=True, text=True, timeout=15, env=ENV)
                if i < len(parts) - 1:
                    time.sleep(0.5)
            return True
        
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
                return True
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 回复失败: {result.stderr[:200]}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 发送异常: {e}")
    return False

# ══════════════════════════════════════════
# 文件操作
# ══════════════════════════════════════════

def safe_path(filename):
    """确保文件路径在workspace内，防止路径穿越攻击"""
    full = os.path.abspath(os.path.join(WORKSPACE, filename))
    if not full.startswith(os.path.abspath(WORKSPACE)):
        return None
    return full

def handle_file_read(filename):
    """读取文件，返回内容"""
    path = safe_path(filename)
    if not path:
        return "❌ 非法的文件路径"
    if not os.path.exists(path):
        # 尝试模糊匹配
        candidates = glob_mod.glob(f"{WORKSPACE}/**/{filename}*", recursive=True)
        if candidates:
            return f"📁 找到相似文件:\n" + "\n".join(f"  • {os.path.relpath(c, WORKSPACE)}" for c in candidates[:10])
        return f"❌ 文件不存在: {filename}"
    if not os.path.isfile(path):
        return f"❌ 不是文件: {filename}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # 限制输出长度
        lines = content.split("\n")
        if len(lines) > 100:
            content = "\n".join(lines[:100]) + f"\n\n... (共 {len(lines)} 行，已截断)"
        if len(content) > 3500:
            content = content[:3500] + "\n\n... (内容过长，已截断)"
        rel = os.path.relpath(path, WORKSPACE)
        return f"📄 **{rel}** ({len(lines)} 行)\n```\n{content}\n```"
    except Exception as e:
        return f"❌ 读取失败: {e}"

def handle_file_write(filename, content):
    """写入文件"""
    path = safe_path(filename)
    if not path:
        return "❌ 非法的文件路径"
    # 如果文件已存在，先备份
    if os.path.exists(path):
        backup = path + ".bak"
        try:
            with open(path, "r") as src, open(backup, "w") as dst:
                dst.write(src.read())
        except:
            pass
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        rel = os.path.relpath(path, WORKSPACE)
        return f"✅ 已写入 **{rel}** ({len(content)} 字符)"
    except Exception as e:
        return f"❌ 写入失败: {e}"

def handle_file_list():
    """列出工作目录文件"""
    try:
        files = []
        for item in sorted(os.listdir(WORKSPACE)):
            full = os.path.join(WORKSPACE, item)
            if item.startswith("."):
                continue
            if os.path.isdir(full):
                files.append(f"📁 {item}/")
            else:
                size = os.path.getsize(full)
                if size > 1024*1024:
                    size_str = f"{size/(1024*1024):.1f}MB"
                elif size > 1024:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size}B"
                files.append(f"📄 {item} ({size_str})")
        return "📁 **工作目录文件**\n" + "\n".join(files[:50])
    except Exception as e:
        return f"❌ 列出失败: {e}"

def handle_file_search(keyword):
    """搜索文件内容"""
    try:
        results = []
        for root, dirs, filenames in os.walk(WORKSPACE):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in filenames:
                if fname.startswith("."):
                    continue
                fpath = os.path.join(root, fname)
                # 跳过二进制文件
                if any(fname.endswith(ext) for ext in [".png", ".jpg", ".svg", ".pyc", ".ttf", ".woff"]):
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if keyword.lower() in content.lower():
                        rel = os.path.relpath(fpath, WORKSPACE)
                        # 找匹配行
                        for i, line in enumerate(content.split("\n"), 1):
                            if keyword.lower() in line.lower():
                                results.append(f"  • **{rel}**:{i} — {line.strip()[:100]}")
                                break
                except:
                    pass
        if results:
            return f"🔍 搜索「{keyword}」找到 {len(results)} 个匹配:\n" + "\n".join(results[:20])
        return f"🔍 未找到「{keyword}」"
    except Exception as e:
        return f"❌ 搜索失败: {e}"

def handle_report():
    """生成并发送报告"""
    try:
        subprocess.run(["python3", "generate_daily_report.py"],
                      capture_output=True, timeout=30, cwd=WORKSPACE)
        subprocess.run(["python3", "send_feishu_notification.py"],
                      capture_output=True, timeout=30, cwd=WORKSPACE)
        return "📊 报告已生成并发送！"
    except Exception as e:
        return f"❌ 报告生成失败: {e}"

def handle_config():
    """查看当前配置"""
    cfg = load_config()
    has_key = bool(cfg.get("deepseek_api_key"))
    return f"""⚙️ **当前配置**
• DeepSeek API: {'✅ 已配置' if has_key else '❌ 未配置（请设置API Key）'}
• 模型: {DEEPSEEK_MODEL}
• 网站: {SITE_URL}
• 工作目录: {WORKSPACE}
• 对话记忆: {len(conversation_history)} 轮

💡 设置API Key: 在飞书发送 `/apikey sk-xxx`"""

# ══════════════════════════════════════════
# 数据加载辅助函数
# ══════════════════════════════════════════

def load_json_file(filepath):
    """加载 JSON 文件，文件不存在或解析失败返回 None"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def fmt_val(val):
    """格式化数值：N/A显示等待提示，0显示0，数字显示千分位"""
    if val is None or val == "N/A" or val == "等待数据":
        return "⏳ 等待数据中（GA4/AdSense 数据延迟24-48小时）"
    if isinstance(val, (int, float)):
        if val == 0:
            return "0"
        return f"{val:,.0f}"
    return str(val)

def fmt_num(val):
    """纯数字格式化，不做 N/A 判断（用于子字段已在上一级处理过的场景）"""
    if isinstance(val, (int, float)):
        if val == 0:
            return "0"
        return f"{val:,.0f}"
    if val is None or val == "N/A" or val == "等待数据":
        return "⏳ 等待数据中（GA4/AdSense 数据延迟24-48小时）"
    return str(val)

def load_dashboard_data():
    """加载 dashboard-data.json 和 reports/latest.json，返回合并后的数据"""
    dashboard = load_json_file(f"{WORKSPACE}/dashboard-data.json") or {}
    report = load_json_file(f"{WORKSPACE}/reports/latest.json") or {}
    return dashboard, report

# ══════════════════════════════════════════
# /traffic — 流量查询
# ══════════════════════════════════════════

def handle_traffic():
    """返回今日/累计流量数据"""
    dashboard, report = load_dashboard_data()

    # 优先从 dashboard-data.json 获取，其次从 reports/latest.json
    traffic = dashboard.get("traffic", {}) or report.get("traffic", {})
    today = traffic.get("today", {}) or {}
    total = traffic.get("total", {}) or {}
    sources = traffic.get("sources", {}) or {}

    msg = "📊 **流量数据**\n\n"
    msg += "---\n"

    # 今日流量
    msg += "### 🟢 今日流量\n"
    msg += f"• 访客数：{fmt_val(today.get('visitors'))}\n"
    msg += f"• 页面浏览：{fmt_val(today.get('pageviews'))}\n"
    msg += f"• 会话数：{fmt_val(today.get('sessions'))}\n"
    if today.get("bounce_rate") is not None:
        msg += f"• 跳出率：{fmt_val(today.get('bounce_rate'))}\n"
    if today.get("avg_duration") is not None:
        msg += f"• 平均时长：{fmt_val(today.get('avg_duration'))}\n"
    msg += "\n"

    # 累计流量
    msg += "### 🔵 累计流量\n"
    msg += f"• 访客数：{fmt_val(total.get('visitors'))}\n"
    msg += f"• 页面浏览：{fmt_val(total.get('pageviews'))}\n"
    msg += f"• 会话数：{fmt_val(total.get('sessions'))}\n"
    msg += "\n"

    # 流量来源
    if sources:
        msg += "### 📍 流量来源\n"
        for src in ["direct", "organic", "referral", "social"]:
            if src in sources:
                emoji = {"direct": "🔗", "organic": "🔍", "referral": "🔗", "social": "📱"}.get(src, "•")
                label = {"direct": "直接访问", "organic": "自然搜索", "referral": "引荐流量", "social": "社交媒体"}.get(src, src)
                msg += f"• {emoji} {label}：{fmt_val(sources[src])}\n"
        msg += "\n"

    msg += "---\n"
    msg += f"💡 更新时间：{dashboard.get('updated_at', report.get('date', '--'))}\n"
    msg += f"🔗 [打开仪表盘]({DASHBOARD_URL})"

    return msg

# ══════════════════════════════════════════
# /revenue — 收益查询
# ══════════════════════════════════════════

def handle_revenue():
    """返回今日/累计收益数据"""
    dashboard, report = load_dashboard_data()

    revenue = dashboard.get("revenue", {}) or report.get("revenue", {})
    today = revenue.get("today", {}) or {}
    total = revenue.get("total", {}) or {}

    msg = "💰 **收益数据**\n\n"
    msg += "---\n"

    # 今日收益
    msg += "### 🟢 今日收益\n"
    msg += f"• 📢 AdSense 预估：{fmt_val(today.get('adsense'))}\n"
    msg += f"• 🛒 京东联盟：{fmt_val(today.get('jd'))}\n"
    msg += f"• ☕ 打赏收入：{fmt_val(today.get('tips'))}\n"
    msg += "\n"

    # 累计收益
    msg += "### 🔵 累计收益\n"
    msg += f"• 📢 AdSense 预估：{fmt_val(total.get('adsense'))}\n"
    msg += f"• 🛒 京东联盟：{fmt_val(total.get('jd'))}\n"
    msg += f"• ☕ 打赏收入：{fmt_val(total.get('tips'))}\n"
    msg += "\n"

    # 收益汇总
    today_total = None
    if today.get("adsense") and today.get("jd") and today.get("tips"):
        try:
            t_vals = []
            for k in ["adsense", "jd", "tips"]:
                v = today[k]
                if isinstance(v, (int, float)):
                    t_vals.append(v)
            if t_vals:
                today_total = sum(t_vals)
        except Exception:
            pass

    if today_total is not None:
        msg += f"📊 **今日合计**：{fmt_num(today_total)}\n"

    msg += "---\n"
    msg += f"💡 更新时间：{dashboard.get('updated_at', report.get('date', '--'))}\n"
    msg += f"🔗 [打开仪表盘]({DASHBOARD_URL})"

    return msg

# ══════════════════════════════════════════
# /dashboard — 完整仪表盘
# ══════════════════════════════════════════

def handle_dashboard():
    """返回完整仪表盘数据（流量+收益+服务状态）"""
    dashboard, report = load_dashboard_data()

    traffic = dashboard.get("traffic", {}) or report.get("traffic", {})
    revenue = dashboard.get("revenue", {}) or report.get("revenue", {})
    services = dashboard.get("services", {}) or {}

    t_today = traffic.get("today", {}) or {}
    t_total = traffic.get("total", {}) or {}
    r_today = revenue.get("today", {}) or {}
    r_total = revenue.get("total", {}) or {}

    msg = "📈 **AI数字工厂 · 仪表盘**\n\n"
    msg += "---\n"

    # 流量概览
    msg += "### 📊 流量概览\n"
    msg += "| 指标 | 今日 | 累计 |\n"
    msg += "|------|------|------|\n"
    msg += f"| 👤 访客 | {fmt_val(t_today.get('visitors'))} | {fmt_val(t_total.get('visitors'))} |\n"
    msg += f"| 👁 页面浏览 | {fmt_val(t_today.get('pageviews'))} | {fmt_val(t_total.get('pageviews'))} |\n"
    msg += f"| 📋 会话 | {fmt_val(t_today.get('sessions'))} | {fmt_val(t_total.get('sessions'))} |\n"
    msg += "\n"

    # 收益概览
    msg += "### 💰 收益概览\n"
    msg += "| 来源 | 今日 | 累计 |\n"
    msg += "|------|------|------|\n"
    msg += f"| 📢 AdSense | {fmt_val(r_today.get('adsense'))} | {fmt_val(r_total.get('adsense'))} |\n"
    msg += f"| 🛒 京东联盟 | {fmt_val(r_today.get('jd'))} | {fmt_val(r_total.get('jd'))} |\n"
    msg += f"| ☕ 打赏 | {fmt_val(r_today.get('tips'))} | {fmt_val(r_total.get('tips'))} |\n"
    msg += "\n"

    # 流量来源
    sources = traffic.get("sources", {})
    if sources:
        msg += "### 📍 流量来源\n"
        for src in ["direct", "organic", "referral", "social"]:
            if src in sources:
                emoji = {"direct": "🔗", "organic": "🔍", "referral": "🔗", "social": "📱"}.get(src, "•")
                label = {"direct": "直接访问", "organic": "自然搜索", "referral": "引荐流量", "social": "社交媒体"}.get(src, src)
                msg += f"• {emoji} {label}：{fmt_val(sources[src])}\n"
        msg += "\n"

    # 服务状态
    if services:
        msg += "### 🟢 服务状态\n"
        svc_list = [
            ("ga4", "📊", "GA4 分析"),
            ("adsense", "💰", "Google AdSense"),
            ("baidu_tongji", "📈", "百度统计"),
            ("gtm", "🏷", "Google Tag Manager"),
            ("jd_alliance", "🛒", "京东联盟"),
        ]
        for key, emoji, label in svc_list:
            if key in services:
                status = services[key]
                if status in ("active", "ok", "connected", "正常"):
                    msg += f"• {emoji} {label}：✅ 正常\n"
                elif status in ("pending", "waiting", "等待"):
                    msg += f"• {emoji} {label}：⏳ 等待数据\n"
                elif status in ("error", "failed", "异常"):
                    msg += f"• {emoji} {label}：❌ 异常\n"
                else:
                    msg += f"• {emoji} {label}：{status}\n"
        msg += "\n"

    msg += "---\n"
    msg += f"💡 更新时间：{dashboard.get('updated_at', report.get('date', '--'))}\n"
    msg += f"🔗 [打开仪表盘]({DASHBOARD_URL})"

    return msg

# ══════════════════════════════════════════
# 命令处理
# ══════════════════════════════════════════

def handle_command(content, chat_id):
    """处理文件操作命令，返回 (是否已处理, 回复内容)"""
    c = content.strip()
    
    if c.startswith("/apikey "):
        key = c[len("/apikey "):].strip()
        if key.startswith("sk-"):
            cfg = load_config()
            cfg["deepseek_api_key"] = key
            save_config(cfg)
            return True, "✅ DeepSeek API Key 已保存！现在机器人可以用大模型回答问题了。"
        return True, "❌ API Key 格式不正确，应该是 sk- 开头。请在 [platform.deepseek.com](https://platform.deepseek.com) 获取。"
    
    if c.startswith("/read "):
        filename = c[len("/read "):].strip()
        return True, handle_file_read(filename)
    
    if c.startswith("/write "):
        parts = c[len("/write "):].strip().split("\n", 1)
        filename = parts[0].strip()
        content = parts[1] if len(parts) > 1 else ""
        if not content:
            return True, "❌ 用法: /write 文件名\\n文件内容"
        return True, handle_file_write(filename, content)
    
    if c == "/list":
        return True, handle_file_list()
    
    if c.startswith("/search "):
        keyword = c[len("/search "):].strip()
        return True, handle_file_search(keyword)
    
    if c == "/report":
        send_message(chat_id, "⏳ 正在生成报告...")
        return True, handle_report()
    
    if c == "/traffic":
        return True, handle_traffic()
    
    if c == "/revenue":
        return True, handle_revenue()
    
    if c == "/dashboard":
        return True, handle_dashboard()
    
    if c == "/config":
        return True, handle_config()
    
    if c == "/help":
        return True, f"""🤖 **AI数字工厂 v4.0 命令列表**

**网站数据**
• `/traffic` — 查看今日/累计流量
• `/revenue` — 查看今日/累计收益
• `/dashboard` — 完整仪表盘（流量+收益+服务状态）
• `/report` — 生成并发送流量报告

**文件操作**
• `/read 文件名` — 读取文件
• `/write 文件名` — 写入文件（换行后输入内容）
• `/list` — 列出文件
• `/search 关键词` — 搜索文件内容

**设置**
• `/config` — 查看配置
• `/apikey sk-xxx` — 设置 DeepSeek API Key

**其他**
• 直接发送任何问题，我会用 AI 回答
• 支持 Markdown 格式"""
    
    return False, None

# ══════════════════════════════════════════
# DeepSeek API 调用
# ══════════════════════════════════════════

def call_deepseek(user_message):
    """调用 DeepSeek API"""
    api_key = get_api_key()
    if not api_key:
        return None
    
    try:
        # 构建消息列表
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # 添加历史对话（最近N轮）
        for h in conversation_history[-MAX_HISTORY:]:
            messages.append({"role": "user", "content": h["user"]})
            if h.get("assistant"):
                messages.append({"role": "assistant", "content": h["assistant"]})
        
        # 添加当前消息
        messages.append({"role": "user", "content": user_message})
        
        data = json.dumps({
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }).encode("utf-8")
        
        req = urllib.request.Request(DEEPSEEK_API_URL, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "FeishuBot/4.0"
        })
        
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        
        if "choices" in result and len(result["choices"]) > 0:
            reply = result["choices"][0]["message"]["content"]
            # 记录 token 用量
            usage = result.get("usage", {})
            if usage:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 tokens: {usage.get('total_tokens', '?')} "
                      f"(提示: {usage.get('prompt_tokens', '?')} + 补全: {usage.get('completion_tokens', '?')})")
            return reply
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ API 返回异常: {json.dumps(result, ensure_ascii=False)[:300]}")
        return None
        
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ DeepSeek HTTP {e.code}: {body[:300]}")
        if e.code == 401:
            return "❌ API Key 无效或已过期。请在 [platform.deepseek.com](https://platform.deepseek.com) 重新获取。"
        if e.code == 402:
            return "❌ 余额不足。请在 DeepSeek 平台充值。"
        return f"❌ API 错误 ({e.code})，请稍后再试"
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ DeepSeek 调用异常: {e}")
        return None

# ══════════════════════════════════════════
# 联网搜索（备用）
# ══════════════════════════════════════════

def web_search(query, max_results=3):
    """DuckDuckGo 搜索，API不可用时的备用方案"""
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
        
        results = []
        for m in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
            link = urllib.parse.unquote(m.group(1))
            if 'uddg=' in link:
                match = re.search(r'uddg=(.*?)(?:&|$)', link)
                if match:
                    link = urllib.parse.unquote(match.group(1))
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            if title and link:
                results.append({"title": title, "url": link})
        
        snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        for i, snip in enumerate(snippets[:len(results)]):
            results[i]["snippet"] = re.sub(r'<[^>]+>', '', snip).strip()
        return results[:max_results]
    except Exception as e:
        print(f"[search] 搜索失败: {e}")
        return []

# ══════════════════════════════════════════
# 智能回复
# ══════════════════════════════════════════

def smart_reply(content, chat_id):
    """处理消息并回复"""
    # 1. 先检查是否是命令
    is_cmd, cmd_result = handle_command(content, chat_id)
    if is_cmd:
        send_message(chat_id, cmd_result)
        # 记录对话
        conversation_history.append({"user": content, "assistant": cmd_result})
        if len(conversation_history) > MAX_HISTORY * 2:
            conversation_history.pop(0)
        return
    
    # 2. 尝试 DeepSeek API
    api_key = get_api_key()
    if api_key:
        send_message(chat_id, "🤔 _思考中..._")
        reply = call_deepseek(content)
        if reply:
            send_message(chat_id, reply)
            conversation_history.append({"user": content, "assistant": reply})
            if len(conversation_history) > MAX_HISTORY * 2:
                conversation_history.pop(0)
            return
    
    # 3. 备用：联网搜索
    if not api_key:
        # 提示设置API Key
        send_message(chat_id, f"""⚠️ **尚未配置 DeepSeek API Key**

没有 API Key 的话我只能用基础的联网搜索，不够智能。

**获取免费 API Key（3步）：**
1. 打开 [platform.deepseek.com](https://platform.deepseek.com)
2. 注册账号（手机号即可）
3. 在「API Keys」页面创建 Key，复制

**然后在飞书发送：**
`/apikey sk-你的密钥`

新用户送 **500 万 tokens 免费额度**，够用几个月！""")
    
    send_message(chat_id, "🔍 正在搜索...")
    results = web_search(content, 3)
    if results:
        reply = f"🔍 **关于「{content[:50]}」**\n\n"
        for i, r in enumerate(results):
            snippet = r.get('snippet', '')[:200]
            reply += f"**{i+1}. [{r['title']}]({r['url']})**\n{snippet}\n\n"
        reply += "---\n💡 *配置 DeepSeek API Key 后我可以更智能地回答，发送 `/apikey sk-xxx` 设置*"
        send_message(chat_id, reply)
    else:
        send_message(chat_id, f"""🤔 关于「{content[:60]}」，我暂时没找到相关信息。

你可以试试：
• 换个角度提问
• 问我关于网站流量、收益、SEO、健康、技术等问题
• 发送 `/help` 查看完整功能
• 发送 `/apikey sk-xxx` 配置 AI 大模型""")

# ══════════════════════════════════════════
# 主循环
# ══════════════════════════════════════════

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 AI数字工厂 v4.0 启动")
    print(f"   用户: {USER_NAME}")
    print(f"   模型: {DEEPSEEK_MODEL}")
    
    api_key = get_api_key()
    if api_key:
        print(f"   DeepSeek API: ✅ 已配置 ({api_key[:10]}...)")
    else:
        print(f"   DeepSeek API: ❌ 未配置 — 使用联网搜索备用模式")
        print(f"   💡 设置方法: 在飞书发送 /apikey sk-xxx")
    
    print(f"   对话记忆: {MAX_HISTORY} 轮")
    print(f"   文件操作: 已启用")
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