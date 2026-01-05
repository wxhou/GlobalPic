# GlobalPic AI - 跨境电商视觉本地化AI

面向跨境电商的智能视觉本地化平台，提供"一键去中文 + 欧美风重绘"营销素材生成服务。

## 功能特色

- 🖼️ **智能文字抹除**: 自动识别并擦除图片中的中文/水印
- 🎨 **AI场景重绘**: 保持商品主体不变，将背景替换为欧美风格场景  
- 📱 **多平台适配**: 支持亚马逊、TikTok、Instagram等主流平台尺寸要求
- ⚡ **批量处理**: 高效处理多张图片，提升运营效率
- 🤖 **AI文案生成**: 根据图片生成符合平台SEO的英文营销文案

## 技术栈

### 后端
- **FastAPI** - 高性能API框架
- **PostgreSQL** - 主数据库
- **Redis** - 缓存和会话存储
- **Z-Image-Turbo** - 核心图像生成模型
- **SAM** - 图像分割模型
- **GPT-4-mini** - 文案生成

### 前端
- **React 18** + **TypeScript**
- **Tailwind CSS** - 样式框架
- **Vite** - 构建工具
- **React Query** - 数据获取

### 部署
- **Docker** + **Docker Compose**
- **Kubernetes** (生产环境)
- **Nginx** - 反向代理
- **CDN** - 全球内容分发

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose

### 本地开发

1. **克隆项目**
```bash
git clone https://github.com/your-org/GlobalPic.git
cd GlobalPic
```

2. **环境配置**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、API密钥等
```

3. **启动服务**
```bash
# 启动数据库和缓存
docker-compose up -d postgres redis

# 安装后端依赖
cd backend
pip install -r requirements-dev.txt

# 安装前端依赖  
cd ../frontend
npm install

# 启动后端服务
cd ../backend
uvicorn app.main:app --reload --port 8000

# 新开终端，启动前端服务
cd frontend
npm run dev
```

4. **访问应用**
- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## API文档

详细API文档请访问: [docs/api/README.md](docs/api/README.md)

## 开发指南

### 项目结构
```
GlobalPic/
├── backend/          # FastAPI后端
├── frontend/         # React前端  
├── ai/              # AI模型和配置
├── docs/            # 项目文档
├── scripts/         # 脚本工具
└── deployment/      # 部署配置
```

### 开发规范

- **代码风格**: 遵循PEP 8 (Python) + ESLint (JavaScript/TypeScript)
- **测试覆盖**: 后端 >85%, 前端 >80%
- **Git流程**: 使用 Conventional Commits 规范

## 部署

### Docker部署
```bash
# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes部署
```bash
kubectl apply -f deployment/kubernetes/
```

更多部署详情: [docs/technical/deployment.md](docs/technical/deployment.md)

## 许可证

MIT License

## 贡献

欢迎提交Issues和Pull Requests!

## 联系我们

- 项目地址: https://github.com/your-org/GlobalPic
- 技术支持: support@globalpic.ai
- 商务合作: business@globalpic.ai
