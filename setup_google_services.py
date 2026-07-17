#!/usr/bin/env python3
"""自动创建 GA4、GTM、AdSense 并更新网站代码"""
import json, os, re, sys, time, requests, subprocess
from pathlib import Path

# ========== OAuth 2.0 Device Flow ==========
CLIENT_ID = "32555940559.apps.googleusercontent.com"
CLIENT_SECRET = "ZmssLNjJy2998hD4CTg2ejr2"

# API scopes
SCOPES = [
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/adsense",
    "https://www.googleapis.com/auth/cloud-platform",
]

TOKEN_FILE = Path("/tmp/google_token.json")

def get_device_code():
    """获取设备验证码"""
    resp = requests.post("https://oauth2.googleapis.com/device/code", data={
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPES),
    })
    if resp.status_code != 200:
        print(f"❌ 获取设备码失败: {resp.text}")
        return None
    data = resp.json()
    print(f"\n{'='*60}")
    print(f"🔗 请打开以下链接进行授权:")
    print(f"   {data['verification_url']}")
    print(f"\n📝 输入验证码: {data['user_code']}")
    print(f"{'='*60}")
    print(f"\n⏳ 等待授权中... (有效期 {data['expires_in']} 秒)")
    return data

def poll_token(device_data):
    """轮询获取 token"""
    interval = device_data.get("interval", 5)
    deadline = time.time() + device_data["expires_in"]
    
    while time.time() < deadline:
        time.sleep(interval)
        resp = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "device_code": device_data["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })
        if resp.status_code == 200:
            token_data = resp.json()
            token_data["expires_at"] = time.time() + token_data["expires_in"]
            with open(TOKEN_FILE, "w") as f:
                json.dump(token_data, f)
            print("✅ 授权成功!")
            return token_data["access_token"]
        elif resp.json().get("error") == "authorization_pending":
            print("   ⏳ 等待用户授权...")
        elif resp.json().get("error") == "slow_down":
            interval += 5
            print("   ⏳ 请稍候...")
        else:
            print(f"   ❌ 错误: {resp.json()}")
            return None
    print("❌ 授权超时")
    return None

def get_access_token():
    """获取访问令牌"""
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            data = json.load(f)
        if data.get("expires_at", 0) > time.time() + 60:
            return data["access_token"]
        # Refresh token
        resp = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": data["refresh_token"],
            "grant_type": "refresh_token",
        })
        if resp.status_code == 200:
            token_data = resp.json()
            token_data["expires_at"] = time.time() + token_data["expires_in"]
            token_data["refresh_token"] = data.get("refresh_token", token_data.get("refresh_token"))
            with open(TOKEN_FILE, "w") as f:
                json.dump(token_data, f)
            print("🔄 Token 已刷新")
            return token_data["access_token"]
    
    device_data = get_device_code()
    if not device_data:
        return None
    return poll_token(device_data)


# ========== GA4 创建 ==========
def create_ga4_property(token):
    """创建 GA4 媒体资源"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 先创建或获取账号
    resp = requests.get(
        "https://analyticsadmin.googleapis.com/v1beta/accounts",
        headers=headers
    )
    if resp.status_code != 200:
        print(f"❌ 获取账号列表失败: {resp.text}")
        return None
    
    accounts = resp.json().get("accounts", [])
    account_id = None
    
    if not accounts:
        print("📝 创建新的 Google Analytics 账号...")
        resp = requests.post(
            "https://analyticsadmin.googleapis.com/v1beta/accounts",
            headers=headers,
            json={"displayName": "健康计算器 Analytics", "regionCode": "CN"}
        )
        if resp.status_code == 200:
            account_id = resp.json()["name"].split("/")[-1]
            print(f"✅ 账号创建成功: {account_id}")
        else:
            print(f"❌ 创建账号失败: {resp.text}")
            return None
    else:
        account_id = accounts[0]["name"].split("/")[-1]
        print(f"📋 使用已有账号: {account_id}")
    
    # 创建 GA4 属性
    print("📝 创建 GA4 媒体资源...")
    resp = requests.post(
        "https://analyticsadmin.googleapis.com/v1beta/properties",
        headers=headers,
        json={
            "displayName": "健康计算器 - 网站",
            "parent": f"accounts/{account_id}",
            "industryCategory": "HEALTH",
            "timeZone": "Asia/Shanghai",
            "currencyCode": "CNY",
        }
    )
    if resp.status_code == 200:
        prop = resp.json()
        prop_name = prop["name"]  # properties/XXXXXX
        prop_id = prop_name.split("/")[-1]
        print(f"✅ GA4 属性创建成功: {prop_id}")
        
        # 创建 Web 数据流
        print("📝 创建 Web 数据流...")
        resp = requests.post(
            f"https://analyticsadmin.googleapis.com/v1beta/{prop_name}/dataStreams",
            headers=headers,
            json={
                "displayName": "健康计算器主站",
                "type": "WEB_DATA_STREAM",
                "webStreamData": {
                    "defaultUri": "https://1-seven-lovat-14.vercel.app"
                }
            }
        )
        if resp.status_code == 200:
            stream = resp.json()
            measurement_id = stream.get("webStreamData", {}).get("measurementId", "")
            print(f"✅ 数据流创建成功, Measurement ID: {measurement_id}")
            return {"property_id": prop_id, "measurement_id": measurement_id}
        else:
            print(f"❌ 创建数据流失败: {resp.text}")
            return {"property_id": prop_id, "measurement_id": None}
    else:
        print(f"❌ 创建 GA4 属性失败: {resp.text}")
        return None


# ========== GTM 创建 ==========
def create_gtm_container(token):
    """创建 GTM 容器"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 获取或创建 GTM 账号
    resp = requests.get(
        "https://tagmanager.googleapis.com/tagmanager/v2/accounts",
        headers=headers
    )
    if resp.status_code != 200:
        print(f"❌ 获取 GTM 账号失败: {resp.text}")
        return None
    
    accounts = resp.json().get("account", [])
    gtm_account_id = None
    
    if not accounts:
        print("📝 创建 GTM 账号...")
        resp = requests.post(
            "https://tagmanager.googleapis.com/tagmanager/v2/accounts",
            headers=headers,
            json={"name": "健康计算器"}
        )
        if resp.status_code == 200:
            gtm_account_id = resp.json()["accountId"]
            print(f"✅ GTM 账号创建成功: {gtm_account_id}")
        else:
            print(f"❌ 创建 GTM 账号失败: {resp.text}")
            return None
    else:
        gtm_account_id = accounts[0]["accountId"]
        print(f"📋 使用已有 GTM 账号: {gtm_account_id}")
    
    # 创建容器
    print("📝 创建 GTM 容器...")
    resp = requests.post(
        f"https://tagmanager.googleapis.com/tagmanager/v2/accounts/{gtm_account_id}/containers",
        headers=headers,
        json={
            "name": "健康计算器网站",
            "usageContext": ["web"],
            "publicId": None,
        }
    )
    if resp.status_code == 200:
        container = resp.json()
        container_id = container.get("publicId", "")
        print(f"✅ GTM 容器创建成功: {container_id}")
        return container_id
    else:
        print(f"❌ 创建 GTM 容器失败: {resp.text}")
        return None


# ========== AdSense 申请 ==========
def check_adsense(token):
    """检查 AdSense 状态"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        "https://adsense.googleapis.com/v2/accounts",
        headers=headers
    )
    if resp.status_code == 200:
        accounts = resp.json().get("accounts", [])
        if accounts:
            pub_id = accounts[0]["name"].split("/")[-1]
            print(f"📋 AdSense 发布商ID: {pub_id}")
            return pub_id
    print("⚠️ AdSense 账号未找到或未激活，需要手动在 adsense.google.com 申请")
    return None


# ========== 更新 HTML 文件 ==========
def update_html_files(ga4_id, gtm_id, adsense_id):
    """更新所有 HTML 文件中的 Google 服务 ID"""
    html_dir = Path(".")
    files_updated = 0
    
    for html_file in html_dir.glob("*.html"):
        if html_file.name == "dashboard.html":
            continue  # Dashboard 单独处理
        
        content = html_file.read_text(encoding="utf-8")
        original = content
        
        if ga4_id:
            content = content.replace("G-XXXXXXXXXX", ga4_id)
        if gtm_id:
            content = content.replace("GTM-XXXXXXX", gtm_id)
        if adsense_id:
            content = content.replace("ca-pub-XXXXXXXXXXXXXXXX", adsense_id)
        
        if content != original:
            html_file.write_text(content, encoding="utf-8")
            files_updated += 1
            print(f"  ✅ 更新: {html_file.name}")
    
    print(f"\n📊 共更新 {files_updated} 个文件")
    return files_updated


# ========== 主流程 ==========
def main():
    print("🚀 开始自动设置 Google 服务...")
    print(f"   网站: https://1-seven-lovat-14.vercel.app")
    print()
    
    # 1. 获取认证
    token = get_access_token()
    if not token:
        print("❌ 无法获取 Google 认证，退出")
        sys.exit(1)
    
    # 2. 创建 GA4
    print("\n📊 [1/4] 创建 Google Analytics 4...")
    ga4_result = create_ga4_property(token)
    ga4_id = ga4_result.get("measurement_id") if ga4_result else None
    
    # 3. 创建 GTM
    print("\n🏷️ [2/4] 创建 Google Tag Manager...")
    gtm_id = create_gtm_container(token)
    
    # 4. 检查 AdSense
    print("\n💰 [3/4] 检查 Google AdSense...")
    adsense_id = check_adsense(token)
    
    # 5. 更新文件
    print("\n📝 [4/4] 更新网站代码...")
    if ga4_id or gtm_id or adsense_id:
        update_html_files(ga4_id, gtm_id, adsense_id)
    
    # 6. 输出结果
    print(f"\n{'='*60}")
    print("📋 设置结果汇总:")
    print(f"   GA4 测量 ID:     {ga4_id or '❌ 未创建'}")
    print(f"   GTM 容器 ID:     {gtm_id or '❌ 未创建'}")
    print(f"   AdSense 发布商:  {adsense_id or '⚠️ 需要手动申请'}")
    print(f"{'='*60}")
    
    # 7. 保存结果到文件
    result = {
        "ga4_measurement_id": ga4_id,
        "gtm_container_id": gtm_id,
        "adsense_publisher_id": adsense_id,
        "website": "https://1-seven-lovat-14.vercel.app",
    }
    with open("google_services.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    if ga4_id or gtm_id:
        print("\n✅ 网站代码已更新，准备提交到 GitHub...")
        return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())