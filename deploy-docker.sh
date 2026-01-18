#!/bin/bash
# Sakura-频道总结助手 Docker 一键部署脚本 (Linux/macOS)
# 使用方法：chmod +x deploy-docker.sh && ./deploy-docker.sh

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${CYAN}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_white() {
    echo -e "${WHITE}$1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 主函数
main() {
    echo -e "${CYAN}========================================${NC}"
    print_info "Sakura-频道总结助手 Docker 部署"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    # 1. 检查 Docker 是否已安装
    print_info "【1/6】检查 Docker 环境..."
    if command_exists docker; then
        docker_version=$(docker --version)
        print_success "Docker 已安装: $docker_version"
    else
        print_error "未检测到 Docker"
        print_warning "请先安装 Docker: https://docs.docker.com/get-docker/"
        read -p "按回车键退出"
        exit 1
    fi

    # 2. 检查 Docker Compose 是否可用
    print_info "【2/6】检查 Docker Compose..."
    if command_exists docker-compose; then
        compose_version=$(docker-compose --version)
        print_success "Docker Compose 已安装: $compose_version"
    else
        print_error "未检测到 Docker Compose"
        print_warning "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
        read -p "按回车键退出"
        exit 1
    fi

    # 3. 检查 .env 文件
    print_info "【3/6】检查环境配置..."
    if [ -f ".env" ]; then
        print_success ".env 文件已存在"
    else
        print_warning ".env 文件不存在"
        if [ -f ".env.example" ]; then
            print_warning "正在从 .env.example 创建 .env 文件..."
            cp .env.example .env
            print_success ".env 文件已创建"
            print_warning "请编辑 .env 文件，填入正确的配置信息"
            echo ""
            print_info "必需的配置项："
            print_white "  - TELEGRAM_API_ID"
            print_white "  - TELEGRAM_API_HASH"
            print_white "  - TELEGRAM_BOT_TOKEN"
            print_white "  - LLM_API_KEY 或 DEEPSEEK_API_KEY"
            echo ""
            read -p "是否继续部署？(y/n): " continue
            if [ "$continue" != "y" ] && [ "$continue" != "Y" ]; then
                print_warning "已取消部署"
                read -p "按回车键退出"
                exit 0
            fi
        else
            print_error "错误: .env.example 文件不存在"
            read -p "按回车键退出"
            exit 1
        fi
    fi

    # 4. 创建必要的目录结构
    print_info "【4/6】创建数据目录..."
    directories=(
        "data/config"
        "data/sessions"
        "data/database"
        "data/data"
        "data/temp"
        "log"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "创建目录: $dir"
        else
            print_white "✓ 目录已存在: $dir"
        fi
    done

    # 5. 停止并删除旧容器（如果存在）
    print_info "【5/6】清理旧容器..."
    container_name="sakura-summary-bot-pro"
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        print_warning "发现旧容器，正在停止并删除..."
        docker-compose down 2>/dev/null || true
        print_success "旧容器已清理"
    else
        print_white "✓ 无旧容器需要清理"
    fi

    # 6. 构建并启动容器
    print_info "【6/6】构建并启动容器..."
    print_warning "这可能需要几分钟时间，请耐心等待..."
    echo ""

    if docker-compose up -d --build; then
        echo ""
        echo -e "${CYAN}========================================${NC}"
        print_success "部署成功！"
        echo -e "${CYAN}========================================${NC}"
        echo ""
        print_white "容器名称: $container_name"
        echo ""
        print_info "常用命令："
        print_white "  查看日志: docker-compose logs -f"
        print_white "  停止容器: docker-compose stop"
        print_white "  启动容器: docker-compose start"
        print_white "  重启容器: docker-compose restart"
        print_white "  删除容器: docker-compose down"
        echo ""
        print_warning "首次运行需要完成 Telegram 登录授权，请查看日志获取详细提示。"
    else
        echo ""
        echo -e "${RED}========================================${NC}"
        print_error "部署失败"
        echo -e "${RED}========================================${NC}"
        echo ""
        print_warning "请检查："
        print_white "  1. .env 文件中的配置是否正确"
        print_white "  2. Docker 是否正在运行"
        print_white "  3. 网络连接是否正常"
        echo ""
        print_warning "查看详细错误信息："
        print_white "  docker-compose logs"
        read -p "按回车键退出"
        exit 1
    fi

    echo ""
    read -p "按回车键退出"
}

# 执行主函数
main
