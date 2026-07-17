#!/usr/bin/env python3
"""
自动创建 GA4 + GTM + AdSense 并更新网站代码
使用 OAuth 设备码流程 — 你只需要在浏览器中打开一个URL并授权
"""
import json, os, sys, time, requests
from pathlib import Path

# 使用 Google 官方设备码 OAuth 端点
CLIENT_ID = "32555940559.apps.googleusercontent.com"
CLIENT_SECRET = "ZmssLNjJy2998hD4CTg2ejr2"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/adsense",
]

TOKEN_FILE = Path("/tmp/google_token.json")

def get_device_code():
    """获取设备验证码"""
    resp = requests.post("https://oauth2.googleapis.com/device/code", data={
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPES),
    })
    if resp.status_code != 200:
        print(f"ERROR: Failed to get device code: {resp.text}")
        return None
    data = resp.json()
    print(f"\n{'='*60}")
    print(f"OPEN THIS URL: {data['verification_url']}")
    print(f"ENTER THIS CODE: {data['user_code']}")
    print(f"{'='*60}")
    print(f"Waiting for authorization... (expires in {data['expires_in']}s)")
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
            print("AUTHORIZED!")
            return token_data["access_token"]
        error = resp.json().get("error", "")
        if error == "authorization_pending":
            print("  Waiting for user to authorize...")
        elif error == "slow_down":
            interval += 5
            print("  Slowing down...")
        else:
            print(f"  ERROR: {resp.json()}")
            return None
    print("TIMEOUT: Authorization expired")
    return None

def get_access_token():
    """获取访问令牌"""
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            data = json.load(f)
        if data.get("expires_at", 0) > time.time() + 60:
            return data["access_token"]
        if "refresh_token" in data:
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
                print("Token refreshed")
                return token_data["access_token"]
    device_data = get_device_code()
    if not device_data:
        return None
    return poll_token(device_data)

def create_ga4_property(token):
    """创建 GA4 属性"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Get or create account
    resp = requests.get("https://analyticsadmin.googleapis.com/v1beta/accounts", headers=headers)
    if resp.status_code != 200:
        print(f"ERROR getting accounts: {resp.text}")
        # Try creating
        resp = requests.post(
            "https://analyticsadmin.googleapis.com/v1beta/accounts",
            headers=headers,
            json={"displayName": "Health Calculator", "regionCode": "CN"}
        )
        if resp.status_code != 200:
            print(f"ERROR creating account: {resp.text}")
            return None
    accounts = resp.json().get("accounts", [])
    if not accounts:
        resp = requests.post(
            "https://analyticsadmin.googleapis.com/v1beta/accounts",
            headers=headers,
            json={"displayName": "Health Calculator", "regionCode": "CN"}
        )
        if resp.status_code != 200:
            print(f"ERROR creating account: {resp.text}")
            return None
        accounts = [resp.json()]
    account_id = accounts[0]["name"].split("/")[-1]
    print(f"Account ID: {account_id}")
    
    # Create property
    resp = requests.post(
        "https://analyticsadmin.googleapis.com/v1beta/properties",
        headers=headers,
        json={
            "displayName": "Health Calculator - Web",
            "parent": f"accounts/{account_id}",
            "industryCategory": "HEALTH",
            "timeZone": "Asia/Shanghai",
            "currencyCode": "CNY",
        }
    )
    if resp.status_code != 200:
        print(f"ERROR creating property: {resp.text}")
        return None
    prop = resp.json()
    prop_name = prop["name"]
    prop_id = prop_name.split("/")[-1]
    print(f"Property ID: {prop_id}")
    
    # Create data stream
    resp = requests.post(
        f"https://analyticsadmin.googleapis.com/v1beta/{prop_name}/dataStreams",
        headers=headers,
        json={
            "displayName": "Main Site",
            "type": "WEB_DATA_STREAM",
            "webStreamData": {"defaultUri": "https://1-seven-lovat-14.vercel.app"}
        }
    )
    if resp.status_code == 200:
        stream = resp.json()
        measurement_id = stream.get("webStreamData", {}).get("measurementId", "")
        print(f"MEASUREMENT ID: {measurement_id}")
        return {"property_id": prop_id, "measurement_id": measurement_id}
    else:
        print(f"ERROR creating stream: {resp.text}")
        return {"property_id": prop_id, "measurement_id": None}

def create_gtm_container(token):
    """创建 GTM 容器"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.get("https://tagmanager.googleapis.com/tagmanager/v2/accounts", headers=headers)
    if resp.status_code != 200:
        print(f"ERROR getting GTM accounts: {resp.text}")
        resp = requests.post(
            "https://tagmanager.googleapis.com/tagmanager/v2/accounts",
            headers=headers,
            json={"name": "Health Calculator"}
        )
        if resp.status_code != 200:
            print(f"ERROR creating GTM account: {resp.text}")
            return None
    accounts = resp.json().get("account", [])
    if not accounts:
        resp = requests.post(
            "https://tagmanager.googleapis.com/tagmanager/v2/accounts",
            headers=headers,
            json={"name": "Health Calculator"}
        )
        if resp.status_code != 200:
            print(f"ERROR creating GTM account: {resp.text}")
            return None
        accounts = [resp.json()]
    gtm_account_id = accounts[0]["accountId"]
    print(f"GTM Account ID: {gtm_account_id}")
    
    resp = requests.post(
        f"https://tagmanager.googleapis.com/tagmanager/v2/accounts/{gtm_account_id}/containers",
        headers=headers,
        json={"name": "Health Calculator Website", "usageContext": ["web"]}
    )
    if resp.status_code == 200:
        container_id = resp.json().get("publicId", "")
        print(f"CONTAINER ID: {container_id}")
        return container_id
    else:
        print(f"ERROR creating container: {resp.text}")
        return None

def check_adsense(token):
    """检查 AdSense 状态"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get("https://adsense.googleapis.com/v2/accounts", headers=headers)
    if resp.status_code == 200:
        accounts = resp.json().get("accounts", [])
        if accounts:
            pub_id = accounts[0]["name"].split("/")[-1]
            print(f"AdSense Publisher ID: {pub_id}")
            return pub_id
    print("AdSense not found - needs manual application at adsense.google.com")
    return None

def update_html_files(ga4_id, gtm_id, adsense_id):
    """替换所有 HTML 文件中的占位符"""
    html_dir = Path(".")
    updated = 0
    for f in sorted(html_dir.glob("*.html")):
        if f.name.startswith("."):
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except:
            continue
        original = content
        if ga4_id:
            content = content.replace("G-XXXXXXXXXX", ga4_id)
        if gtm_id:
            content = content.replace("GTM-XXXXXXX", gtm_id)
        if adsense_id:
            content = content.replace("ca-pub-XXXXXXXXXXXXXXXX", adsense_id)
        if content != original:
            f.write_text(content, encoding="utf-8")
            updated += 1
            print(f"  Updated: {f.name}")
    print(f"Total files updated: {updated}")
    return updated

def main():
    print("=" * 60)
    print("AUTO SETUP GOOGLE SERVICES")
    print("https://1-seven-lovat-14.vercel.app")
    print("=" * 60)
    
    token = get_access_token()
    if not token:
        print("FATAL: Cannot get Google access token")
        sys.exit(1)
    
    print("\n[1/3] Creating Google Analytics 4...")
    ga4_result = create_ga4_property(token)
    ga4_id = ga4_result.get("measurement_id") if ga4_result else None
    
    print("\n[2/3] Creating Google Tag Manager...")
    gtm_id = create_gtm_container(token)
    
    print("\n[3/3] Checking Google AdSense...")
    adsense_id = check_adsense(token)
    
    result = {
        "ga4_measurement_id": ga4_id,
        "gtm_container_id": gtm_id,
        "adsense_publisher_id": adsense_id,
        "website": "https://1-seven-lovat-14.vercel.app",
    }
    
    print(f"\n{'='*60}")
    print("RESULTS:")
    print(f"  GA4:      {ga4_id or 'FAILED'}")
    print(f"  GTM:      {gtm_id or 'FAILED'}")
    print(f"  AdSense:  {adsense_id or 'Manual setup needed'}")
    print(f"{'='*60}")
    
    if ga4_id or gtm_id or adsense_id:
        print("\nUpdating website code...")
        update_html_files(ga4_id, gtm_id, adsense_id)
    
    with open("google_services.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\nDone! google_services.json saved")
    return 0

if __name__ == "__main__":
    sys.exit(main())