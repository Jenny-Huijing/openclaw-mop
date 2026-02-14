# 小红书 MCP 接入文档

## ✅ 接入完成状态

| 组件 | 状态 | 说明 |
|------|------|------|
| MCP 服务 | 🟢 运行中 | 端口 18060，13个工具可用 |
| 后端配置 | 🟢 已配置 | MCP_ENABLED=true |
| 健康检查 | 🟢 通过 | Session 管理正常 |
| 登录状态 | 🟢 已登录 | Cookie 有效 |
| 工具调用 | 🟢 可用 | 全部 13 个工具可调用 |

## 🔑 关键技术要点

### Session ID 管理

MCP Streamable HTTP 协议要求在 `initialize` 响应中获取 `Mcp-Session-Id`，并在后续所有请求中携带：

```python
# 1. Initialize 获取 Session ID
async with session.post(mcp_url, json=init_payload) as resp:
    session_id = resp.headers.get('Mcp-Session-Id')

# 2. 后续请求携带 Session ID
headers = {
    "Content-Type": "application/json",
    "Mcp-Session-Id": session_id
}
```

### 初始化流程

```
1. POST /mcp (initialize) 
   ← Response: 200 OK + Mcp-Session-Id header
   
2. POST /mcp (notifications/initialized)
   Headers: Mcp-Session-Id: xxx
   ← Response: 202 Accepted
   
3. POST /mcp (tools/call)
   Headers: Mcp-Session-Id: xxx
   ← Response: 200 OK + result
```

## 📁 文件变更

### 新增文件
- `backend/app/services/xhs_mcp.py` - MCP 客户端 (完整版)
- `scripts/test_mcp.py` - 测试脚本
- `scripts/debug_mcp.py` - 调试脚本

### 修改文件
- `backend/.env` - 添加 MCP_URL 和 MCP_ENABLED
- `backend/app/core/config.py` - MCP 配置项
- `backend/app/services/xhs_crawler.py` - 集成 MCP 优先调用
- `backend/app/services/__init__.py` - 导出 MCP 客户端
- `docker-compose.yml` - MCP 环境变量

## 🔧 可用 MCP 工具 (13个)

| 工具名 | 说明 | 状态 |
|--------|------|------|
| check_login_status | 检查登录状态 | ✅ |
| list_feeds | 获取推荐列表 | ✅ |
| search_feeds | 搜索帖子 | ✅ |
| publish_content | 发布图文 | ✅ |
| publish_with_video | 发布视频 | ✅ |
| get_feed_detail | 获取帖子详情 | ✅ |
| post_comment_to_feed | 发表评论 | ✅ |
| reply_comment_in_feed | 回复评论 | ✅ |
| like_feed | 点赞帖子 | ✅ |
| favorite_feed | 收藏帖子 | ✅ |
| user_profile | 获取用户资料 | ✅ |
| get_login_qrcode | 获取登录二维码 | ✅ |
| delete_cookies | 删除 Cookies | ✅ |

## 🧪 测试命令

```bash
cd /Users/irvinglu/.openclaw/workspace/nmop/backend
python3 ../scripts/test_mcp.py
```

## 🔌 Docker 网络配置

### 本地开发
```bash
MCP_URL=http://localhost:18060/mcp
```

### Docker 环境
```yaml
services:
  api:
    environment:
      - MCP_URL=http://host.docker.internal:18060/mcp
      - MCP_ENABLED=true
```

## 🍪 Cookies 配置

MCP 服务使用 `mcp/data/cookies.json` 中的 Cookie 进行小红书认证。

当前状态: ✅ 已配置并有效

## 🚀 使用示例

### 在运营平台中使用

```python
from app.services.xhs_mcp import get_mcp_client

async def example():
    client = get_mcp_client()
    
    # 检查登录
    status = await client.check_login_status()
    print(f"登录状态: {status}")
    
    # 获取推荐内容
    notes = await client.get_notes(limit=10)
    
    # 搜索内容
    results = await client.search_notes("美食", limit=5)
    
    # 发布笔记
    result = await client.publish_note(
        title="测试标题",
        content="测试内容",
        images=["/path/to/image.jpg"],
        tags=["美食", "探店"]
    )
```

### 爬虫服务自动回退

`xhs_crawler.py` 已配置为优先使用 MCP，失败时自动回退到传统 Cookie 爬虫。

## 📚 参考资料

- MCP 协议规范: https://modelcontextprotocol.io
- xiaohongshu-mcp 项目: https://github.com/xpzouying/xiaohongshu-mcp
- 官方文档: https://www.haha.ai/xiaohongshu-mcp
