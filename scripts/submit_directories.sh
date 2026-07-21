#!/bin/bash
# ============================================================
# 免费导航站/目录站提交脚本
# 用于向各大免费导航站提交网站URL
# 使用方式: bash submit_directories.sh
#
# 注意: 大部分导航站需要人工审核，脚本仅做自动化提交尝试
# 部分站点可能需要手动填写表单
# ============================================================

set -euo pipefail

SITE_URL="https://1-seven-lovat-14.vercel.app"
SITE_NAME="免费在线健康计算器"
SITE_DESC="免费在线BMI、体脂率、卡路里、BMR、理想体重计算器，科学减肥必备工具"
SITE_EMAIL="admin@example.com"  # 请替换为真实邮箱
SITE_CATEGORY="健康"  # 分类

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  免费导航站/目录站提交工具${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "站点: ${SITE_URL}"
echo -e "名称: ${SITE_NAME}"
echo ""
echo -e "${YELLOW}注意: 大部分导航站需要人工审核，以下仅做自动化提交尝试${NC}"
echo -e "${YELLOW}建议手工访问各站完成提交流程${NC}"
echo ""

# 结果统计
SUCCESS_COUNT=0
FAIL_COUNT=0
MANUAL_COUNT=0

# 提交函数
submit_url() {
    local name="$1"
    local submit_url="$2"
    local method="${3:-GET}"  # 默认GET
    local data="${4:-}"       # POST数据

    echo -e "${BLUE}[提交]${NC} ${name}"
    echo "  URL: ${submit_url}"

    if [ "$method" = "POST" ]; then
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "$data" \
            --max-time 10 \
            "$submit_url" 2>/dev/null) || RESPONSE="000"
    else
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
            --max-time 10 \
            "$submit_url" 2>/dev/null) || RESPONSE="000"
    fi

    if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "301" ] || [ "$RESPONSE" = "302" ]; then
        echo -e "  ${GREEN}状态: ${RESPONSE} - 页面可访问${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "  ${RED}状态: ${RESPONSE} - 可能需手动提交${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    echo ""
}

# 需要手动提交的站点
manual_submit() {
    local name="$1"
    local url="$2"
    local note="${3:-}"

    echo -e "${YELLOW}[手动]${NC} ${name}"
    echo "  地址: ${url}"
    if [ -n "$note" ]; then
        echo "  备注: ${note}"
    fi
    echo ""
    MANUAL_COUNT=$((MANUAL_COUNT + 1))
}


echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  一、可尝试自动提交的导航站${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 1. 好站推荐 (haozhan123)
submit_url "好站推荐" \
    "https://www.haozhan123.com/"

# 2. 网站目录之家
submit_url "网站目录之家" \
    "http://www.muluzhijia.com/"

# 3. 酷站大全
submit_url "酷站大全" \
    "https://www.kuzhan.net/"

# 4. 站优云
submit_url "站优云" \
    "https://www.zhanyouyun.com/"

# 5. 聚合网
submit_url "聚合网" \
    "https://www.juhew.com/"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  二、需要手动提交的导航站（重要）${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 百度站长平台
manual_submit "百度站长平台" \
    "https://ziyuan.baidu.com/linksubmit/index" \
    "添加站点 -> 验证所有权 -> 提交sitemap: ${SITE_URL}/sitemap.xml"

# 360站长平台
manual_submit "360站长平台" \
    "https://zhanzhang.so.com/" \
    "添加站点 -> 验证 -> 提交sitemap"

# 搜狗站长平台
manual_submit "搜狗站长平台" \
    "https://zhanzhang.sogou.com/" \
    "添加站点 -> 验证 -> 数据提交"

# 必应站长工具
manual_submit "Bing Webmaster Tools" \
    "https://www.bing.com/webmasters/" \
    "添加站点 -> 验证 -> 提交sitemap: ${SITE_URL}/sitemap.xml"

# Google Search Console
manual_submit "Google Search Console" \
    "https://search.google.com/search-console" \
    "添加资源 -> 验证 -> 提交sitemap"

# 神马站长平台
manual_submit "神马站长平台" \
    "https://zhanzhang.sm.cn/" \
    "UC/神马搜索站长工具"

# 头条搜索站长平台
manual_submit "头条搜索站长平台" \
    "https://zhanzhang.toutiao.com/" \
    "字节跳动旗下搜索平台"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  三、中文导航站/目录站（手动提交）${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 中文导航站列表
manual_submit "HAO123网址导航" \
    "https://www.hao123.com/feedback/index" \
    "通过反馈入口提交网址收录申请"

manual_submit "2345网址导航" \
    "https://www.2345.com/" \
    "通过底部「网址提交」提交"

manual_submit "搜狗网址导航" \
    "https://123.sogou.com/" \
    "通过反馈提交网址"

manual_submit "QQ网址导航" \
    "https://hao.qq.com/" \
    "通过意见反馈提交"

manual_submit "360导航" \
    "https://hao.360.com/" \
    "通过底部「收录申请」提交"

manual_submit "毒霸网址大全" \
    "https://www.duba.com/" \
    "通过反馈提交收录"

manual_submit "114啦网址导航" \
    "https://www.114la.com/" \
    "通过网站提交入口提交"

manual_submit "微软必应导航" \
    "https://cn.bing.com/" \
    "使用Bing Webmaster Tools提交"

manual_submit "天猫导航" \
    "https://dh.tmall.com/" \
    "通过反馈提交网址"

manual_submit "百度网址大全" \
    "https://site.baidu.com/" \
    "通过收录申请提交"

manual_submit "简洁导航" \
    "https://www.jianjie.com/" \
    "通过网站提交入口"

manual_submit "265上网导航" \
    "https://www.265.com/" \
    "通过反馈提交收录"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  四、SEO工具和站长工具平台${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

manual_submit "爱站网" \
    "https://www.aizhan.com/" \
    "查询网站数据，提交站点信息"

manual_submit "站长工具" \
    "https://tool.chinaz.com/" \
    "提交网站到站长工具数据库"

manual_submit "5118" \
    "https://www.5118.com/" \
    "SEO数据分析平台"

manual_submit "爱站SEO工具包" \
    "https://tools.aizhan.com/" \
    "网站SEO检测和优化"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  五、社交媒体和内容平台${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

manual_submit "知乎" \
    "https://www.zhihu.com/" \
    "在相关健康/减肥话题下发布高质量回答，附上链接"

manual_submit "小红书" \
    "https://www.xiaohongshu.com/" \
    "发布减肥/健康相关笔记，在合适位置放链接"

manual_submit "豆瓣" \
    "https://www.douban.com/" \
    "在减肥/健身小组中分享"

manual_submit "百度贴吧" \
    "https://tieba.baidu.com/" \
    "在减肥吧、健身吧等贴吧分享"

manual_submit "简书" \
    "https://www.jianshu.com/" \
    "发布健康相关文章并附链接"

manual_submit "CSDN" \
    "https://www.csdn.net/" \
    "发布健康计算器科普文章"

manual_submit "掘金" \
    "https://juejin.cn/" \
    "发布技术实现文章（如前端计算器开发）"

manual_submit "SegmentFault" \
    "https://segmentfault.com/" \
    "发布技术问答或文章"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  六、免费外链/友链平台${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

manual_submit "站长论坛" \
    "https://www.chinaz.com/" \
    "在站长论坛发布网站展示帖"

manual_submit "落伍者论坛" \
    "https://www.im286.net/" \
    "在站长交流区发布网站展示"

manual_submit "4414站长论坛" \
    "https://www.4414.cn/" \
    "发布网站展示帖，可交换友链"

manual_submit "搜外SEO" \
    "https://www.seowhy.com/" \
    "SEO问答和友链交换平台"

manual_submit "go9go友链平台" \
    "https://www.go9go.cn/" \
    "免费友情链接交换平台"

manual_submit "我拉网友链" \
    "https://www.55.la/" \
    "友情链接交换"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  提交统计${NC}"
echo -e "${BLUE}============================================${NC}"
echo -e "自动提交尝试: ${SUCCESS_COUNT} 成功 / ${FAIL_COUNT} 失败"
echo -e "需手动提交:   ${MANUAL_COUNT} 个站点"
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  建议操作顺序${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "第一步: 提交到搜索引擎站长平台（最重要）"
echo "  1. 百度站长平台 (ziyuan.baidu.com)"
echo "  2. Google Search Console"
echo "  3. Bing Webmaster Tools"
echo "  4. 360站长平台"
echo "  5. 搜狗站长平台"
echo "  6. 神马站长平台"
echo ""
echo "第二步: 社交媒体推广"
echo "  1. 知乎 - 发布高质量回答"
echo "  2. 小红书 - 发布笔记"
echo "  3. 微博 - 发布带话题的推文"
echo "  4. 豆瓣/贴吧 - 社区分享"
echo ""
echo "第三步: 导航站提交"
echo "  1. HAO123、2345等大型导航站"
echo "  2. 各个站长目录站"
echo ""
echo "第四步: SEO优化"
echo "  1. 使用爱站网、5118等工具分析"
echo "  2. 优化网站TDK (Title/Description/Keywords)"
echo "  3. 持续更新文章内容"
echo "  4. 交换高质量友链"
echo ""
echo -e "${YELLOW}提示: 请将脚本中的 SITE_EMAIL 替换为真实邮箱地址${NC}"