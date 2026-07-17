#!/usr/bin/env python3
"""Adsterra 广告联盟集成脚本（无需ICP备案）- 将所有占位符替换为实际广告代码"""
import json, os
from pathlib import Path

# Adsterra 广告代码模板（注册后替换 YOUR_ADSTERRA_ID）
ADSTERRA_BANNER = """
<!-- Adsterra Banner Ad -->
<div id="adsterra-banner" style="text-align:center;margin:20px 0;min-height:90px;background:#FFF9E6;border:1px dashed #F0D060;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:0.85rem;color:#999;">
  <a href="https://adsterra.com/?ref=YOUR_REFERRAL" target="_blank" rel="nofollow">广告位 — 通过 Adsterra 投放</a>
</div>
<script>
(function(){
  var s = document.createElement('script');
  s.src = 'https://pl' + 'AY.ads' + 'terra.com/ads/YOUR_ADSTERRA_ID.js';
  s.async = true;
  s.onload = function(){
    var el = document.getElementById('adsterra-banner');
    if(el) el.style.display = 'none';
  };
  document.head.appendChild(s);
})();
</script>
"""

# 在所有页面底部（footer前）插入 Adsterra 广告
TARGET_FILES = [
    "index.html", "bmi.html", "bmr.html", "calorie.html", "body-fat.html",
    "ideal-weight.html", "bmi-guide.html", "calorie-guide.html", "blog.html",
    "weight-loss-guide", "protein-powder-guide", "smart-scale-compare"
]

count = 0
for fname in TARGET_FILES:
    fpath = Path(fname)
    if not fpath.exists():
        continue
    content = fpath.read_text(encoding="utf-8")
    if "adsterra" in content.lower():
        continue
    # Insert before </main> closing tag
    content = content.replace("</main>", ADSTERRA_BANNER + "\n  </main>", 1)
    if "adsterra" in content:
        fpath.write_text(content, encoding="utf-8")
        count += 1
        print(f"  ✅ {fname}")

print(f"\nAdsterra 广告代码已添加到 {count} 个页面")
print("注册 Adsterra 后，将 YOUR_ADSTERRA_ID 替换为真实ID即可")
print("注册地址: https://adsterra.com")