#!/bin/bash
# 更新小红书 Cookie 脚本

echo "🍪 小红书 Cookie 更新工具"
echo ""
echo "请按以下步骤操作："
echo "1. 登录 https://www.xiaohongshu.com"
echo "2. 按 F12 打开开发者工具"
echo "3. 切换到 Network 标签"
echo "4. 刷新页面"
echo "5. 找到任意请求，复制 Cookie"
echo ""
echo "然后运行:"
echo "  ./update_cookie.sh '你的Cookie字符串'"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 错误: 请提供 Cookie 字符串"
    echo "用法: $0 'cookie_string'"
    exit 1
fi

COOKIE_STRING="$1"
COOKIE_FILE="mcp/data/cookies.json"

echo "📝 更新 Cookie 文件: $COOKIE_FILE"

# 创建备份
if [ -f "$COOKIE_FILE" ]; then
    cp "$COOKIE_FILE" "${COOKIE_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 已创建备份"
fi

# 使用 Python 更新 Cookie
python3 << PYTHON_EOF
import json
import sys

cookie_str = """$COOKIE_STRING"""

# 解析 Cookie 字符串
cookies = []
for item in cookie_str.split(';'):
    item = item.strip()
    if '=' in item:
        name, value = item.split('=', 1)
        cookies.append({
            "name": name.strip(),
            "value": value.strip(),
            "domain": ".xiaohongshu.com",
            "path": "/"
        })

# 保存到文件
with open("$COOKIE_FILE", 'w') as f:
    json.dump(cookies, f, indent=2)

print(f"✅ Cookie 已更新: {len(cookies)} 个字段")
print(f"📁 文件位置: $COOKIE_FILE")
PYTHON_EOF

# 重启 MCP 服务
echo ""
echo "🔄 重启 MCP 服务..."
docker restart xiaohongshu-mcp

echo ""
echo "✨ 完成! 请刷新页面查看效果"
