# 小红书 Cookie 获取指南

## 方法一：浏览器控制台（推荐）

1. **登录小红书**
   - 打开 https://www.xiaohongshu.com
   - 用手机扫码登录你的账号

2. **获取 Cookie**
   - 登录成功后，按 `F12` 打开开发者工具
   - 切换到 **Console/控制台** 标签
   - 粘贴以下代码并按回车：

```javascript
copy(document.cookie);
console.log('✅ Cookie 已复制到剪贴板！');
console.log('Cookie 长度:', document.cookie.length, '字符');
```

3. **验证 Cookie**
   - 如果看到 `✅ Cookie 已复制到剪贴板！`
   - 直接粘贴到 `.env` 文件中

---

## 方法二：网络面板

1. 登录小红书后，按 `F12`
2. 切换到 **Network/网络** 标签
3. 刷新页面（`F5`）
4. 点击任意请求（如 `home`、`api`）
5. 在右侧找到 **Request Headers/请求头**
6. 找到 `cookie:` 字段，复制整个值

---

## 方法三：使用浏览器扩展

安装 **Cookie-Editor** 扩展：
- Chrome: https://chrome.google.com/webstore/detail/cookie-editor/...
- Edge: https://microsoftedge.microsoft.com/addons/detail/...

使用步骤：
1. 安装扩展
2. 登录小红书
3. 点击扩展图标
4. 导出所有 Cookie
5. 复制 `xiaohongshu.com` 域下的 Cookie 字符串

---

## 配置到系统

获取 Cookie 后，编辑 `.env` 文件：

```bash
# 打开 .env 文件
vim .env

# 添加或修改这行（粘贴你获取的完整 Cookie）
XHS_COOKIE=your_cookie_here

# 保存并重启服务
docker-compose restart api
```

---

## 验证配置

重启后访问：
http://localhost/api/v1/xhs/stats

如果返回粉丝数等数据，说明配置成功！

---

**注意**：
- Cookie 有过期时间（通常几天到几周）
- 退出登录或修改密码会导致 Cookie 失效
- Cookie 包含敏感信息，请勿分享给他人
