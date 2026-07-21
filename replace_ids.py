#!/usr/bin/env python3
"""一键替换所有 HTML 文件中的 Google 服务占位符 ID"""
import json, sys
from pathlib import Path

CONFIG_FILE = Path("config/google_ids.json")
AMAZON_CONFIG = Path("config/affiliate_products.json")

PLACEHOLDER_GA4 = "G-9HDK6XWY7J"
PLACEHOLDER_GTM = "GTM-N26FR57S"
PLACEHOLDER_ADSENSE = "ca-pub-XXXXXXXXXXXXXXXX"
PLACEHOLDER_ASIN = "B0XXXXXX"
PLACEHOLDER_TAG = "healthtools-23"

def load_config():
    if not CONFIG_FILE.exists():
        print(f"❌ 配置文件不存在: {CONFIG_FILE}")
        print("   请先创建 config/google_ids.json 并填入真实ID")
        return None
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_amazon_config():
    if not AMAZON_CONFIG.exists():
        return None
    with open(AMAZON_CONFIG, encoding="utf-8") as f:
        return json.load(f)

def replace_in_files(ga4_id, gtm_id, adsense_id, amazon_config):
    root = Path(".")
    updated = []
    skipped = []
    
    # Files to process (all HTML files + dashboard)
    html_files = list(root.glob("*"))
    exclude = {".github", "config", "style.css", "main.js", "robots.txt", "sitemap.xml",
               "setup_google_services.py", "replace_ids.py", "google_services.json",
               "google1cc027e7196bb51b", "googleAWiwVTLTNZn5SoQQpeaVSr0BrSAEG-j7momsbF1X7JM",
               "vercel.json", "vercel.json", "dashboard-data.json", "README.md", ".gitignore", ".git"}
    
    for f in html_files:
        if f.name in exclude or f.is_dir() or f.name.startswith("."):
            continue
        
        try:
            content = f.read_text(encoding="utf-8")
        except:
            continue
        original = content
        
        # Google services
        if ga4_id and ga4_id != PLACEHOLDER_GA4:
            content = content.replace(PLACEHOLDER_GA4, ga4_id)
        if gtm_id and gtm_id != PLACEHOLDER_GTM:
            content = content.replace(PLACEHOLDER_GTM, gtm_id)
        if adsense_id and adsense_id != PLACEHOLDER_ADSENSE:
            content = content.replace(PLACEHOLDER_ADSENSE, adsense_id)
        
        # Amazon affiliate
        if amazon_config:
            tag = amazon_config.get("amazon_tag", PLACEHOLDER_TAG)
            if tag != PLACEHOLDER_TAG:
                content = content.replace(PLACEHOLDER_TAG, tag)
            
            for product_key, product in amazon_config.get("products", {}).items():
                real_asin = product.get("asin", "")
                if real_asin and real_asin != PLACEHOLDER_ASIN:
                    content = content.replace(PLACEHOLDER_ASIN, real_asin)
        
        if content != original:
            f.write_text(content, encoding="utf-8")
            updated.append(f.name)
            print(f"  ✅ 已更新: {f.name}")
        else:
            skipped.append(f.name)
    
    return updated, skipped

def main():
    print("=" * 60)
    print("  🔄 批量替换 Google 服务 ID 和联盟链接")
    print("=" * 60)
    print()
    
    config = load_config()
    if not config:
        sys.exit(1)
    
    ga4_id = config.get("ga4_measurement_id", "")
    gtm_id = config.get("gtm_container_id", "")
    adsense_id = config.get("adsense_publisher_id", "")
    amazon_config = load_amazon_config()
    
    # Validate
    has_ga4 = ga4_id and ga4_id != PLACEHOLDER_GA4
    has_gtm = gtm_id and gtm_id != PLACEHOLDER_GTM
    has_adsense = adsense_id and adsense_id != PLACEHOLDER_ADSENSE
    has_amazon = amazon_config is not None
    
    print("📋 配置检查:")
    print(f"   GA4:      {'✅ ' + ga4_id if has_ga4 else '⚠️  未配置'}")
    print(f"   GTM:      {'✅ ' + gtm_id if has_gtm else '⚠️  未配置'}")
    print(f"   AdSense:  {'✅ ' + adsense_id if has_adsense else '⚠️  未配置'}")
    print(f"   亚马逊联盟: {'✅ 已配置' if has_amazon else '⚠️  未配置'}")
    print()
    
    if not (has_ga4 or has_gtm or has_adsense or has_amazon):
        print("❌ 没有需要替换的配置，请先填写 config/google_ids.json")
        sys.exit(1)
    
    print("📝 开始替换...")
    updated, skipped = replace_in_files(ga4_id, gtm_id, adsense_id, amazon_config)
    
    print()
    print("=" * 60)
    print(f"📊 替换完成: {len(updated)} 个文件已更新, {len(skipped)} 个文件跳过")
    print("=" * 60)
    
    # Save updated config
    with open("google_services.json", "w", encoding="utf-8") as f:
        json.dump({
            "ga4_measurement_id": ga4_id if has_ga4 else None,
            "gtm_container_id": gtm_id if has_gtm else None,
            "adsense_publisher_id": adsense_id if has_adsense else None,
            "website": "https://1-seven-lovat-14.vercel.app",
            "updated_at": str(Path(".").resolve()),
        }, f, ensure_ascii=False, indent=2)
    
    print("✅ google_services.json 已更新")
    print()
    print("💡 下一步:")
    print("   git add . && git commit -m '更新 Google 服务 ID' && git push")
    print("   Vercel 将自动部署更新后的网站")

if __name__ == "__main__":
    main()