#!/bin/bash
# 新媒体智能运营平台 - 数据库初始化脚本
# 支持: PostgreSQL (生产) / SQLite (开发)

set -e

echo "🚀 新媒体智能运营平台 - 数据库初始化"
echo "========================================"

# 检测数据库类型
DB_TYPE=${DB_TYPE:-sqlite}

if [ "$DB_TYPE" = "postgresql" ]; then
    echo "📦 使用 PostgreSQL 数据库"
    
    # PostgreSQL 配置
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_USER=${DB_USER:-postgres}
    DB_PASS=${DB_PASS:-postgres}
    DB_NAME=${DB_NAME:-xhs_platform}
    
    # 检查 psql 是否可用
    if ! command -v psql &> /dev/null; then
        echo "❌ 错误: 未找到 psql 命令"
        echo "请安装 PostgreSQL 客户端:"
        echo "  Mac: brew install postgresql"
        echo "  Ubuntu: sudo apt-get install postgresql-client"
        exit 1
    fi
    
    # 构建连接字符串
    export PGPASSWORD=$DB_PASS
    
    echo "🔌 连接到 PostgreSQL ($DB_HOST:$DB_PORT)..."
    
    # 检查数据库是否存在，不存在则创建
    DB_EXISTS=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")
    
    if [ "$DB_EXISTS" != "1" ]; then
        echo "📁 创建数据库: $DB_NAME"
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || {
            echo "❌ 创建数据库失败，请检查连接信息"
            exit 1
        }
    else
        echo "📁 数据库已存在: $DB_NAME"
    fi
    
    # 执行初始化 SQL
    echo "📊 初始化表结构..."
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f scripts/init_db.sql
    
    echo "✅ PostgreSQL 数据库初始化完成!"
    echo ""
    echo "连接信息:"
    echo "  DATABASE_URL=postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"
    
elif [ "$DB_TYPE" = "sqlite" ]; then
    echo "📦 使用 SQLite 数据库 (开发模式)"
    
    DB_PATH=${DB_PATH:-./data/xhs_platform.db}
    
    # 创建数据目录
    mkdir -p $(dirname $DB_PATH)
    
    # 检查 sqlite3 是否可用
    if ! command -v sqlite3 &> /dev/null; then
        echo "❌ 错误: 未找到 sqlite3 命令"
        echo "请安装 SQLite:"
        echo "  Mac: brew install sqlite"
        echo "  Ubuntu: sudo apt-get install sqlite3"
        exit 1
    fi
    
    echo "🔌 初始化 SQLite: $DB_PATH"
    
    # SQLite 需要修改 SQL 语法，使用专门的脚本
    if [ -f "scripts/init_db_sqlite.sql" ]; then
        sqlite3 $DB_PATH < scripts/init_db_sqlite.sql
    else
        echo "⚠️ 未找到 SQLite 专用脚本，将使用通用脚本(可能有兼容性问题)"
        sqlite3 $DB_PATH < scripts/init_db.sql 2>/dev/null || {
            echo "❌ SQLite 初始化失败"
            exit 1
        }
    fi
    
    echo "✅ SQLite 数据库初始化完成!"
    echo ""
    echo "连接信息:"
    echo "  DATABASE_URL=sqlite+aiosqlite:///$DB_PATH"
    
else
    echo "❌ 错误: 不支持的数据库类型: $DB_TYPE"
    echo "支持类型: postgresql, sqlite"
    exit 1
fi

echo ""
echo "📝 下一步:"
echo "  1. 复制 .env.example 为 .env"
echo "  2. 编辑 .env 填入正确的 DATABASE_URL"
echo "  3. 运行: docker-compose up -d"
echo ""
echo "✨ 数据库初始化完成!"
