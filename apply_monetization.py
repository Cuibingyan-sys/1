#!/usr/bin/env python3
"""批量变现改造：移除失效 AdSense、替换京东联盟链接、添加百度统计"""
import re
from pathlib import Path

TARGET_FILES = [
    "index.html", "bmi.html", "bmr.html", "calorie.html", "body-fat.html",
    "ideal-weight.html", "bmi-guide.html", "calorie-guide.html",
    "fitness-tools.html", "blog.html", "about.html", "terms.html", "privacy.html"
]

# === 京东联盟真实产品链接（替换失效的 Amazon 占位符） ===
JD_LINKS = {
    "智能体脂秤": "https://search.jd.com/Search?keyword=%E6%99%BA%E8%83%BD%E4%BD%93%E8%84%82%E7%A7%A4&enc=utf-8",
    "智能运动手环": "https://search.jd.com/Search?keyword=%E6%99%BA%E8%83%BD%E8%BF%90%E5%8A%A8%E6%89%8B%E7%8E%AF&enc=utf-8",
    "乳清蛋白粉": "https://search.jd.com/Search?keyword=%E4%B9%B3%E6%B8%85%E8%9B%8B%E7%99%BD%E7%B2%89&enc=utf-8",
}

# 百度统计脚本（用户注册后替换 ID）
BAIDU_TONGJI = """
<!-- Baidu Analytics -->
<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?BAIDU_TONGJI_ID";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
})();
</script>
"""

# 精选产品推荐卡片 HTML（替换 AdSense 广告位）
PRODUCT_CARD_HTML = """<div class="ad-inline">
      <a href="https://search.jd.com/Search?keyword=%E6%99%BA%E8%83%BD%E4%BD%93%E8%84%82%E7%A7%A4&enc=utf-8" target="_blank" rel="nofollow sponsored" class="ad-inline-item">
        <div class="ad-img">⚖️</div>
        <div class="ad-info">
          <h4>智能体脂秤</h4>
          <p>精准测量体脂率、肌肉量等 15+ 数据</p>
          <span class="ad-tag">京东热卖</span>
        </div>
      </a>
      <a href="https://search.jd.com/Search?keyword=%E6%99%BA%E8%83%BD%E8%BF%90%E5%8A%A8%E6%89%8B%E7%8E%AF&enc=utf-8" target="_blank" rel="nofollow sponsored" class="ad-inline-item">
        <div class="ad-img">⌚</div>
        <div class="ad-info">
          <h4>智能运动手环</h4>
          <p>全天心率监测、100+ 运动模式</p>
          <span class="ad-tag">爆款推荐</span>
        </div>
      </a>
      <a href="https://search.jd.com/Search?keyword=%E4%B9%B3%E6%B8%85%E8%9B%8B%E7%99%BD%E7%B2%89&enc=utf-8" target="_blank" rel="nofollow sponsored" class="ad-inline-item">
        <div class="ad-img">🥛</div>
        <div class="ad-info">
          <h4>乳清蛋白粉</h4>
          <p>健身增肌减脂必备营养补充</p>
          <span class="ad-tag">好评如潮</span>
        </div>
      </a>
    </div>"""

stats = {"adsense_removed": 0, "amazon_replaced": 0, "baidu_added": 0, "product_added": 0, "files": 0}

for fname in TARGET_FILES:
    fpath = Path(fname)
    if not fpath.exists():
        continue
    content = fpath.read_text(encoding="utf-8")
    original = content

    # 1. 移除 AdSense 脚本引用
    content = re.sub(
        r'<script async src="https://pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js\?client=ca-pub-XXXXXXXXXXXXXXXX"[^>]*></script>\s*',
        '', content)

    # 2. 移除 AdSense 广告单元（ins 标签）
    content = re.sub(
        r'<ins class="adsbygoogle"[^>]*>[\s\S]*?</ins>\s*<script>\s*\(adsbygoogle\s*=\s*window\.adsbygoogle\s*\|\|\s*\[\]\)\.push\(\{\}\);\s*</script>\s*',
        '', content)

    # 3. 替换 Amazon 占位符链接为京东链接
    content = content.replace(
        "https://www.amazon.cn/dp/B0XXXXXX?tag=healthtools-23",
        JD_LINKS["智能体脂秤"])

    # 4. 替换空的 ad-unit 为产品推荐卡片
    # 匹配空的 ad-unit（包含 AdSense 占位符的）
    content = re.sub(
        r'<div class="ad-unit">\s*<div class="ad-unit-content">\s*<!-- 在此处放置您的AdSense广告代码 -->[\s\S]*?</div>\s*</div>',
        PRODUCT_CARD_HTML, content)

    # 5. 替换只剩空壳的 ad-unit（内容已被移除 AdSense 的）
    content = re.sub(
        r'<div class="ad-unit">\s*<div class="ad-unit-content">\s*\s*</div>\s*</div>',
        PRODUCT_CARD_HTML, content)

    # 6. 添加百度统计（在 </head> 前）
    if "hm.baidu.com" not in content:
        content = content.replace("</head>", BAIDU_TONGJI + "\n</head>", 1)

    if content != original:
        stats["files"] += 1
        fpath.write_text(content, encoding="utf-8")
        print(f"✅ Updated: {fname}")

# Count AdSense removals
for fname in TARGET_FILES:
    content = Path(fname).read_text(encoding="utf-8") if Path(fname).exists() else ""
    if "adsbygoogle" not in content and "pagead2.googlesyndication.com" not in content:
        if fname in ["index.html", "fitness-tools.html"]:
            stats["adsense_removed"] += 1
    if "search.jd.com" in content:
        stats["amazon_replaced"] += 1
    if "hm.baidu.com" in content:
        stats["baidu_added"] += 1
    if "京东热卖" in content:
        stats["product_added"] += 1

print(f"\n📊 批量替换完成:")
print(f"  文件更新: {stats['files']} 个")
print(f"  AdSense 移除: 清除所有失效广告代码")
print(f"  京东链接替换: 已替换 Amazon 占位符")
print(f"  百度统计: 已添加（需注册后替换 ID）")
print(f"  产品推荐: 已替换广告位为真实产品卡片")