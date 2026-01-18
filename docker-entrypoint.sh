#!/bin/bash
set -e

echo "========================================"
echo "Sakura-频道总结助手 Docker 容器启动"
echo "========================================"

# 检查必要的环境变量
echo "检查环境变量配置..."
required_vars=("TELEGRAM_API_ID" "TELEGRAM_API_HASH" "TELEGRAM_BOT_TOKEN")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "错误: 以下必要的环境变量未设置:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo "请确保在 .env 文件中正确配置这些变量"
    exit 1
fi

# 检查AI API密钥
if [ -z "$LLM_API_KEY" ] && [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "警告: 未设置AI API密钥 (LLM_API_KEY 或 DEEPSEEK_API_KEY)"
    echo "机器人可能无法正常工作"
fi

echo "环境变量检查完成"

# 创建数据目录和文件
echo "初始化数据目录结构..."

# 创建所有必要的目录
mkdir -p /app/data/config \
         /app/data/sessions \
         /app/data/database \
         /app/data/data \
         /app/data/temp \
         /app/log

echo "数据目录结构创建完成"

# 检查会话文件
SESSION_FILE="/app/data/sessions/bot_session"
if [ ! -f "$SESSION_FILE" ]; then
    echo "注意: 未找到会话文件 $SESSION_FILE"
    echo "首次运行需要Telegram登录授权"
    echo "请按照提示完成登录流程"
fi

echo "========================================"
echo "数据目录结构:"
echo "  /app/data/config/      - 配置文件"
echo "  /app/data/sessions/    - Telegram会话文件"
echo "  /app/data/database/   - SQLite数据库"
echo "  /app/data/data/       - 运行时数据"
echo "  /app/data/temp/       - 临时文件"
echo "  /app/log/             - 日志文件"
echo "========================================"
echo "启动参数: $@"
echo "========================================"

# 执行主程序
exec "$@"
