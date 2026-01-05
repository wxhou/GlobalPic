#!/bin/bash

# GlobalPic AI 项目初始化脚本
# 用于快速设置开发环境

set -e

echo "🚀 开始初始化 GlobalPic AI 项目..."

# 检查依赖
check_dependencies() {
    echo "📋 检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    echo "✅ 依赖检查通过"
}

# 创建环境配置文件
setup_environment() {
    echo "⚙️  设置环境配置..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 已创建 .env 文件，请根据需要修改配置"
    else
        echo "📝 .env 文件已存在"
    fi
}

# 启动数据库服务
start_databases() {
    echo "🗄️  启动数据库服务..."
    
    docker-compose up -d postgres redis minio
    
    echo "⏳ 等待数据库启动..."
    sleep 10
    
    echo "✅ 数据库服务启动完成"
}

# 安装后端依赖
install_backend_deps() {
    echo "🐍 安装后端依赖..."
    
    cd backend
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 未安装"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d venv ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # 安装依赖
    pip install -r requirements.txt
    
    echo "✅ 后端依赖安装完成"
    cd ..
}

# 安装前端依赖
install_frontend_deps() {
    echo "📦 安装前端依赖..."
    
    cd frontend
    
    if ! command -v npm &> /dev/null; then
        echo "❌ Node.js/npm 未安装"
        exit 1
    fi
    
    npm install
    
    echo "✅ 前端依赖安装完成"
    cd ..
}

# 运行数据库迁移
run_migrations() {
    echo "🔄 运行数据库迁移..."
    
    cd backend
    
    if [ -f alembic.ini ]; then
        source venv/bin/activate
        alembic upgrade head
    else
        echo "⚠️  Alembic 配置文件不存在，跳过迁移"
    fi
    
    cd ..
}

# 创建必要的目录
create_directories() {
    echo "📁 创建必要目录..."
    
    mkdir -p data/{raw,processed,samples,cache}
    mkdir -p logs
    mkdir -p uploads
    mkdir -p ai/models
    
    echo "✅ 目录创建完成"
}

# 显示完成信息
show_completion() {
    echo ""
    echo "🎉 GlobalPic AI 项目初始化完成！"
    echo ""
    echo "📋 下一步操作："
    echo "1. 编辑 .env 文件配置你的环境变量"
    echo "2. 启动开发服务器："
    echo "   - 后端: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    echo "   - 前端: cd frontend && npm run dev"
    echo ""
    echo "🌐 服务访问地址："
    echo "   - 前端: http://localhost:5173"
    echo "   - 后端 API: http://localhost:8000"
    echo "   - API 文档: http://localhost:8000/docs"
    echo "   - MinIO 控制台: http://localhost:9001"
    echo ""
    echo "📚 更多文档请查看 docs/ 目录"
}

# 主函数
main() {
    check_dependencies
    setup_environment
    create_directories
    start_databases
    install_backend_deps
    install_frontend_deps
    run_migrations
    show_completion
}

main "$@"