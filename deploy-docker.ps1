# Sakura-频道总结助手 Docker 一键部署脚本 (Windows PowerShell)
# 使用方法：右键点击脚本 -> "使用 PowerShell 运行" 或在 PowerShell 中执行 ./deploy-docker.ps1

# 设置错误时停止
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sakura-频道总结助手 Docker 部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Docker 是否已安装
Write-Host "【1/6】检查 Docker 环境..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker 已安装: $dockerVersion" -ForegroundColor Green
    } else {
        throw "Docker 未安装"
    }
} catch {
    Write-Host "✗ 错误: 未检测到 Docker" -ForegroundColor Red
    Write-Host "请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 2. 检查 Docker Compose 是否可用
Write-Host "【2/6】检查 Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker Compose 已安装: $composeVersion" -ForegroundColor Green
    } else {
        throw "Docker Compose 未安装"
    }
} catch {
    Write-Host "✗ 错误: 未检测到 Docker Compose" -ForegroundColor Red
    Write-Host "Docker Desktop 应该包含 Docker Compose，请检查安装" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 3. 检查 .env 文件
Write-Host "【3/6】检查环境配置..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env 文件已存在" -ForegroundColor Green
} else {
    Write-Host "✗ .env 文件不存在" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Write-Host "正在从 .env.example 创建 .env 文件..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "✓ .env 文件已创建" -ForegroundColor Green
        Write-Host "⚠ 请编辑 .env 文件，填入正确的配置信息" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "必需的配置项：" -ForegroundColor Cyan
        Write-Host "  - TELEGRAM_API_ID" -ForegroundColor White
        Write-Host "  - TELEGRAM_API_HASH" -ForegroundColor White
        Write-Host "  - TELEGRAM_BOT_TOKEN" -ForegroundColor White
        Write-Host "  - LLM_API_KEY 或 DEEPSEEK_API_KEY" -ForegroundColor White
        Write-Host ""
        $continue = Read-Host "是否继续部署？(y/n)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-Host "已取消部署" -ForegroundColor Yellow
            Read-Host "按回车键退出"
            exit 0
        }
    } else {
        Write-Host "✗ 错误: .env.example 文件不存在" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
}

# 4. 创建必要的目录结构
Write-Host "【4/6】创建数据目录..." -ForegroundColor Yellow
$directories = @(
    "data/config",
    "data/sessions",
    "data/database",
    "data/data",
    "data/temp",
    "log"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ 创建目录: $dir" -ForegroundColor Green
    } else {
        Write-Host "✓ 目录已存在: $dir" -ForegroundColor Gray
    }
}

# 5. 停止并删除旧容器（如果存在）
Write-Host "【5/6】清理旧容器..." -ForegroundColor Yellow
$containerName = "sakura-summary-bot-pro"
try {
    $container = docker ps -a -q -f name=$containerName
    if ($container) {
        Write-Host "发现旧容器，正在停止并删除..." -ForegroundColor Yellow
        docker-compose down 2>$null
        Write-Host "✓ 旧容器已清理" -ForegroundColor Green
    } else {
        Write-Host "✓ 无旧容器需要清理" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠ 清理旧容器时出现警告，继续部署..." -ForegroundColor Yellow
}

# 6. 构建并启动容器
Write-Host "【6/6】构建并启动容器..." -ForegroundColor Yellow
Write-Host "这可能需要几分钟时间，请耐心等待..." -ForegroundColor Yellow
Write-Host ""

try {
    docker-compose up -d --build
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "✓ 部署成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "容器名称: $containerName" -ForegroundColor White
        Write-Host ""
        Write-Host "常用命令：" -ForegroundColor Cyan
        Write-Host "  查看日志: docker-compose logs -f" -ForegroundColor White
        Write-Host "  停止容器: docker-compose stop" -ForegroundColor White
        Write-Host "  启动容器: docker-compose start" -ForegroundColor White
        Write-Host "  重启容器: docker-compose restart" -ForegroundColor White
        Write-Host "  删除容器: docker-compose down" -ForegroundColor White
        Write-Host ""
        Write-Host "首次运行需要完成 Telegram 登录授权，请查看日志获取详细提示。" -ForegroundColor Yellow
    } else {
        throw "构建失败"
    }
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 部署失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查：" -ForegroundColor Yellow
    Write-Host "  1. .env 文件中的配置是否正确" -ForegroundColor White
    Write-Host "  2. Docker 是否正在运行" -ForegroundColor White
    Write-Host "  3. 网络连接是否正常" -ForegroundColor White
    Write-Host ""
    Write-Host "查看详细错误信息：" -ForegroundColor Yellow
    Write-Host "  docker-compose logs" -ForegroundColor White
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Read-Host "按回车键退出"
