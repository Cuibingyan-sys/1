#!/bin/bash
# ============================================================
# 百度站长平台 - 批量URL推送脚本
# 使用方式: bash baidu_push.sh <你的百度统计token>
#
# 百度站长平台URL推送API文档:
# https://ziyuan.baidu.com/linksubmit/index
# ============================================================

set -euo pipefail

# --- 配置 ---
# 百度站长平台推送接口
BAIDU_API_URL="http://data.zz.baidu.com/urls"

# 站点域名
SITE="https://1-seven-lovat-14.vercel.app"

# --- 参数检查 ---
if [ $# -lt 2 ]; then
    echo "用法: bash baidu_push.sh <site> <token>"
    echo ""
    echo "参数说明:"
    echo "  site   - 在百度站长平台验证的站点域名 (如: https://1-seven-lovat-14.vercel.app)"
    echo "  token  - 百度站长平台提供的推送接口调用token"
    echo ""
    echo "获取token步骤:"
    echo "  1. 登录百度站长平台: https://ziyuan.baidu.com/"
    echo "  2. 添加并验证站点"
    echo "  3. 进入「数据引入」->「链接提交」"
    echo "  4. 复制「接口调用地址」中的 token 参数"
    echo ""
    exit 1
fi

SITE="$1"
TOKEN="$2"

# --- 所有需要推送的URL列表 ---
URLS=(
    "${SITE}/"
    "${SITE}/index.html"
    "${SITE}/bmi.html"
    "${SITE}/bmr.html"
    "${SITE}/calorie.html"
    "${SITE}/bodyfat.html"
    "${SITE}/ideal-weight.html"
    "${SITE}/shop.html"
    "${SITE}/articles/"
    "${SITE}/articles/bmi-guide.html"
    "${SITE}/articles/weight-loss-tips.html"
    "${SITE}/articles/calorie-counting.html"
    "${SITE}/articles/body-fat-explained.html"
    "${SITE}/articles/healthy-diet-plan.html"
)

# --- 构建推送数据（每行一个URL）---
URL_DATA=""
for url in "${URLS[@]}"; do
    URL_DATA+="${url}"$'\n'
done

echo "============================================"
echo "  百度站长平台 - URL推送工具"
echo "============================================"
echo "站点: ${SITE}"
echo "推送URL数量: ${#URLS[@]}"
echo "推送列表:"
for url in "${URLS[@]}"; do
    echo "  - ${url}"
done
echo ""

# --- 执行推送 ---
echo "正在推送到百度站长平台..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Content-Type: text/plain" \
    --data-binary "${URL_DATA}" \
    "${BAIDU_API_URL}?site=${SITE}&token=${TOKEN}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo ""
echo "HTTP状态码: ${HTTP_CODE}"
echo "返回内容: ${BODY}"
echo ""

# --- 解析结果 ---
if [ "$HTTP_CODE" = "200" ]; then
    # 尝试解析返回的JSON结果
    SUCCESS=$(echo "$BODY" | grep -o '"success":[0-9]*' | grep -o '[0-9]*' || echo "0")
    REMAIN=$(echo "$BODY" | grep -o '"remain":[0-9]*' | grep -o '[0-9]*' || echo "N/A")

    echo "============================================"
    echo "  推送结果"
    echo "============================================"
    echo "成功推送: ${SUCCESS} 条"
    echo "今日剩余配额: ${REMAIN} 条"
    echo ""
    echo "提示: 百度每天推送配额有限，请合理使用。"
else
    echo "============================================"
    echo "  推送失败！"
    echo "============================================"
    echo "请检查:"
    echo "  1. token是否正确"
    echo "  2. 站点是否已在百度站长平台验证"
    echo "  3. 站点域名是否与百度站长平台登记的一致"
fi

echo ""
echo "============================================"
echo "  其他提交方式建议"
echo "============================================"
echo "1. 手动提交sitemap:"
echo "   登录百度站长平台 -> 数据引入 -> 链接提交 -> sitemap提交"
echo "   提交地址: ${SITE}/sitemap.xml"
echo ""
echo "2. 自动推送JS代码（嵌入网站页面）:"
echo "   <script>"
echo "   (function(){"
echo "     var bp = document.createElement('script');"
echo "     var curProtocol = window.location.protocol.split(':')[0];"
echo "     if (curProtocol === 'https') {"
echo "       bp.src = 'https://zz.bdstatic.com/linksubmit/push.js';"
echo "     } else {"
echo "       bp.src = 'http://push.zhanzhang.baidu.com/push.js';"
echo "     }"
echo "     var s = document.getElementsByTagName('script')[0];"
echo "     s.parentNode.insertBefore(bp, s);"
echo "   })();"
echo "   </script>"
echo ""