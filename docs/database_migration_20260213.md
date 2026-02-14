# 数据库更新脚本

## 添加 error_message 字段到 contents 表

执行以下 SQL 命令来添加新字段：

```sql
-- 添加 error_message 字段
ALTER TABLE contents ADD COLUMN IF NOT EXISTS error_message TEXT;
```

或者在容器内执行：

```bash
# 进入 PostgreSQL 容器
docker exec -it xhs_postgres psql -U postgres -d xhs_platform -c "ALTER TABLE contents ADD COLUMN IF NOT EXISTS error_message TEXT;"
```

## 说明

- `status` 字段已经是 `String(20)` 类型，支持新的 `PUBLISH_FAILED` 值
- `error_message` 字段用于记录发布失败的原因

## 状态枚举值

| 状态值 | 说明 |
|--------|------|
| CREATING | 创作中 |
| reviewing | 待审核 |
| approved | 已通过 |
| published | 已发布 |
| rejected | 已拒绝 |
| PUBLISH_FAILED | 发布失败 |
