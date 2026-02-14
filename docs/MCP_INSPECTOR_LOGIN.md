# 使用 MCP Inspector 登录小红书

## 1. 安装 MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```

## 2. 配置连接

在 Inspector 界面中配置 MCP 服务器：
- **URL**: `http://localhost:18060/mcp`
- **Type**: HTTP

## 3. 登录步骤

### 步骤1：检查登录状态
- 选择工具：`check_login_status`
- 点击执行

如果未登录，会显示二维码

### 步骤2：扫码登录
1. 打开小红书 App
2. 扫描二维码
3. 在 Inspector 中确认登录成功

### 步骤3：验证登录
再次执行 `check_login_status`，确认显示已登录

## 4. 获取账号数据

登录成功后，可以使用以下工具：

### 获取推荐流
- 工具：`list_feeds`
- 返回：推荐笔记列表

### 获取用户主页
- 工具：`user_profile`
- 参数：
  - `user_id`: 用户ID
  - `xsec_token`: 从 list_feeds 中获取

### 发布笔记
- 工具：`publish_note`
- 参数：
  - `title`: 标题
  - `content`: 内容
  - `images`: 图片路径（相对于 /app/images）

## 5. 目录结构

```
mcp/
├── data/
│   └── cookies.json      # 登录后自动生成
├── images/               # 发布图片存放目录
│   └── your-image.jpg
└── docker-compose.yml
```

## 注意事项

1. **Cookie 文件**：登录成功后自动保存在 `./data/cookies.json`
2. **图片路径**：发布笔记时，图片路径要相对于 `/app/images`
3. **二维码过期**：如果二维码过期，需要重新执行 check_login_status
