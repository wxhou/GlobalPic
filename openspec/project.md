# Project Context

## Purpose
**GlobalPic AI (全球图)** 是一个面向跨境电商的智能视觉本地化平台，致力于解决中国卖家"图土、有中文、不懂欧美审美"导致点击率低的痛点。

### 项目目标
- 为跨境电商卖家提供"一键去中文 + 欧美风重绘"的营销素材生成服务
- 支持 TikTok/亚马逊/独立站等多平台视觉内容优化
- 提升产品图片的专业度和本地化水平，从而提高转化率
- 目标用户：义乌/深圳的跨境电商个体户、Dropshipping 玩家、独立站卖家

### 核心价值主张
- **智能文字抹除**：自动识别并擦除图片中的中文/水印，智能补全背景
- **AI场景重绘**：保持商品主体不变，将背景替换为欧美风格场景
- **多平台适配**：支持亚马逊、TikTok、Instagram 等主流平台尺寸要求
- **批量处理**：高效处理多张图片，提升运营效率

## Tech Stack

### 核心AI模型
- **Z-Image-Turbo** (主模型)：6B参数，Single-Stream DiT架构，sub-second推理速度
- **Z-Image-Edit** (专用编辑模型)：指令跟随能力强，支持精细编辑（待发布）
- **Segment Anything Model (SAM)**：产品主体精确分割，zero-shot分割
- **GPT-4o-mini**：智能文案生成和SEO优化

### 后端技术栈
- **Python 3.9+**：主要开发语言
- **FastAPI**：高性能API框架，支持异步处理
- **diffusers库**：Hugging Face的扩散模型库
- **PyTorch 2.0+**：深度学习框架
- **OpenCV**：图像处理和计算机视觉
- **Celery**：异步任务队列，支持并发处理
- **Redis**：缓存和会话存储
- **PostgreSQL**：关系型数据库（用户数据、订单等）

### 前端技术栈
- **React 18+** 或 **Vue 3+**：现代前端框架
- **TypeScript**：类型安全的JavaScript
- **Tailwind CSS**：实用优先的CSS框架
- **Vite**：快速构建工具
- **React Query/SWR**：数据获取和缓存

### 基础设施
- **Docker**：容器化部署
- **Kubernetes**：容器编排（生产环境）
- **AWS S3/MinIO**：对象存储
- **CloudFlare CDN**：全球内容分发
- **Grafana + Prometheus**：监控和日志

### 开发工具
- **Poetry**：Python包管理
- **Conda + YForm**：本地AI模型环境管理
  - **环境隔离**：使用conda环境隔离AI模型依赖
  - **本地管理**：YForm作为本地conda环境管理工具
  - **依赖管理**：PyTorch、diffusers、transformers等AI库版本控制
  - **环境配置**：统一的环境配置文件和环境变量管理
  - **包版本优先级**：以已安装的conda环境包版本为主，pip安装为辅
- **ESLint + Prettier**：代码格式化和检查
- **Jest + Playwright**：单元测试和端到端测试
- **GitHub Actions**：CI/CD流水线

## Project Conventions

### Code Style

#### Python代码规范
- **遵循 PEP 8 标准**，使用 Black 进行代码格式化
- **类型提示**：所有函数和方法必须包含类型注解
- **文档字符串**：使用 Google 风格的 docstring
- **命名约定**：
  - 类名：`PascalCase`
  - 函数和变量：`snake_case`
  - 常量：`UPPER_SNAKE_CASE`
  - 私有属性：`_leading_underscore`

```python
from typing import List, Optional, Dict, Any
from PIL import Image

class ImageProcessor:
    """图像处理核心类"""
    
    def __init__(self, model_path: str, cache_size: int = 100) -> None:
        self.model_path = model_path
        self.cache_size = cache_size
        
    def process_image(
        self, 
        image: Image.Image, 
        operations: List[str]
    ) -> Dict[str, Any]:
        """处理图像并返回结果
        
        Args:
            image: 输入图像
            operations: 操作列表 ['clean', 'background', 'resize']
            
        Returns:
            处理结果字典
        """
        pass
```

#### 前端代码规范
- **React Hooks 优先**：使用函数组件和Hooks
- **TypeScript 严格模式**：启用严格类型检查
- **组件命名**：PascalCase for components, camelCase for props
- **CSS-in-JS**：使用Styled Components或Emotion

```typescript
interface ImageUploadProps {
  onUpload: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
}

export const ImageUpload: React.FC<ImageUploadProps> = ({
  onUpload,
  maxFiles = 9,
  acceptedTypes = ['image/jpeg', 'image/png', 'image/webp']
}) => {
  // 组件实现
};
```

### Architecture Patterns

#### 后端架构
- **分层架构**：Controller -> Service -> Repository -> Model
- **依赖注入**：使用FastAPI的Depends注入依赖
- **异步优先**：所有I/O操作使用async/await
- **微服务设计**：图像处理、用户管理、支付等模块解耦

```python
# 典型的服务层结构
class ImageProcessingService:
    def __init__(
        self,
        zimage_service: ZImageService,
        sam_service: SAMService,
        cache: CacheService
    ) -> None:
        self.zimage = zimage_service
        self.sam = sam_service
        self.cache = cache
        
    async def process_image(self, request: ProcessRequest) -> ProcessResponse:
        # 业务逻辑处理
        pass
```

#### 前端架构
- **组件化设计**：可复用的UI组件库
- **状态管理**：React Query + Context API
- **路由设计**：React Router v6，懒加载路由
- **错误边界**：捕获和处理组件错误

#### API设计规范
- **RESTful风格**：清晰的资源URL和HTTP方法
- **版本控制**：API路径包含版本号 `/api/v1/`
- **统一响应格式**：
```json
{
  "success": true,
  "data": {},
  "message": "Success",
  "timestamp": "2025-12-28T10:20:49Z"
}
```

### Testing Strategy

#### 测试金字塔
1. **单元测试** (70%)：函数和类的独立测试
2. **集成测试** (20%)：API和数据库集成测试
3. **端到端测试** (10%)：完整的用户流程测试

#### 测试工具和框架
- **后端测试**：
  - pytest：测试框架
  - pytest-asyncio：异步测试支持
  - pytest-cov：代码覆盖率
  - Factory Boy：测试数据生成
  - httpx：HTTP客户端测试

```python
import pytest
from unittest.mock import AsyncMock

class TestImageProcessingService:
    @pytest.fixture
    def service(self):
        return ImageProcessingService(mock_zimage, mock_sam)
        
    @pytest.mark.asyncio
    async def test_process_image_success(self, service):
        # 测试用例
        pass
```

- **前端测试**：
  - Jest：单元测试
  - React Testing Library：组件测试
  - Playwright：端到端测试

#### 测试覆盖率要求
- **核心业务逻辑**：> 90%
- **API端点**：> 85%
- **工具函数**：> 95%
- **前端组件**：> 80%

### Git Workflow

#### 分支策略
- **main分支**：生产环境代码，稳定的发布版本
- **develop分支**：开发分支，集成所有新功能
- **feature分支**：`feature/功能名称`，开发新功能
- **hotfix分支**：`hotfix/问题描述`，紧急修复
- **release分支**：`release/版本号`，发布准备

#### 提交规范
使用 **Conventional Commits** 格式：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型 (type)**：
- `feat`：新功能
- `fix`：Bug修复
- `docs`：文档更新
- `style`：代码格式调整
- `refactor`：代码重构
- `test`：测试相关
- `chore`：构建过程或辅助工具的变动

**示例**：
```
feat(ai): add Z-Image-Turbo integration for background replacement

- Implement Z-Image-Turbo model for fast background generation
- Add support for 10+ western style backgrounds
- Optimize inference time to <10 seconds

Closes #123
```

#### Pull Request流程
1. **创建PR前**：确保所有测试通过，代码覆盖率达标
2. **PR模板**：包含变更描述、测试截图、风险评估
3. **Code Review**：至少1名团队成员review
4. **自动化检查**：CI流水线必须通过
5. **合并策略**：使用Squash and Merge

## Domain Context

### 跨境电商视觉营销
- **视觉本地化**：将中国产品图转换为符合目标市场审美的图片
- **平台适配**：不同电商平台对图片有特定要求（尺寸、背景、内容）
- **文化敏感**：避免文化冲突，使用目标市场接受的视觉元素
- **转化率优化**：通过高质量图片提升点击率和转化率

### AI图像处理领域
- **扩散模型**：基于潜在扩散的图像生成技术
- **图像修复**：使用AI智能填补图像中不需要的部分
- **语义分割**：精确分离图像中的不同对象
- **风格迁移**：保持内容不变，改变视觉风格

### 核心业务流程
1. **图片上传**：用户上传原始产品图片
2. **AI分析**：检测文字、分析主体、识别风格
3. **智能处理**：执行文字擦除、背景替换等操作
4. **质量检测**：评估生成结果的准确性和美观度
5. **结果输出**：提供多张候选图供用户选择

## Important Constraints

### 技术约束
- **GPU内存限制**：消费级设备16GB VRAM，企业级H800 GPU最优
- **处理时间要求**：单张图片处理时间 < 30秒
- **并发限制**：支持100个用户同时在线处理
- **模型依赖**：Z-Image-Edit模型尚未发布，需要备用方案
- **环境管理**：必须使用conda yform环境进行AI模型部署
  - 环境隔离：每个AI模型独立conda环境
  - 版本锁定：关键依赖版本固定，避免兼容性冲突
  - 本地管理：YForm作为本地conda环境管理工具

### 性能约束
- **响应时间**：API响应时间 < 2秒
- **图片质量**：输出分辨率最低1024x1024，支持4K
- **处理准确率**：文字擦除准确率 > 95%，主体保真度 > 98%
- **系统可用性**：99.9%在线时间保证

### 业务约束
- **成本控制**：单张图片处理成本 < $0.022
- **用户隐私**：图片处理后自动删除，保护用户隐私
- **内容合规**：遵守各平台内容政策，避免违规内容生成
- **地域限制**：受目标市场法律法规约束

### 安全约束
- **数据传输**：所有图片上传使用HTTPS加密
- **访问控制**：API接口需要有效的认证令牌
- **数据隔离**：用户数据严格隔离，防止信息泄露
- **审计日志**：记录所有关键操作的审计日志

## External Dependencies

### AI模型服务
- **Z-Image-Turbo模型**：
  - 源：Hugging Face (Tongyi-MAI/Z-Image-Turbo)
  - 用途：核心图像生成和编辑
  - 版本：v1.0（当前稳定版本）

- **SAM模型**：
  - 源：Meta Research
  - 用途：产品主体精确分割
  - 版本：sam_vit_h_4b8939.pth

### 云服务依赖
- **AWS S3**：图片存储和CDN分发
- **CloudFlare**：全球内容分发网络
- **OpenAI API**：GPT-4o-mini用于文案生成
- **第三方OCR**：文字检测和识别服务

### 支付和订阅
- **Stripe**：处理订阅付费和按需付费
- **PayPal**：国际支付支持
- **支付宝/微信支付**：中国用户支付

### 监控和分析
- **Sentry**：错误监控和性能追踪
- **Google Analytics**：用户行为分析
- **Mixpanel**：产品使用情况分析
- **LogRocket**：前端错误重现

### 第三方API
- **SendGrid/Mailgun**：邮件服务
- **Twilio**：短信验证
- **Cloudinary**：图片处理和优化
- **Redis Cloud**：托管Redis服务

### 开发工具
- **GitHub**：代码仓库和CI/CD
- **Figma**：UI/UX设计协作
- **Notion**：项目文档和知识库
- **Slack**：团队沟通和通知
- **Conda + YForm**：本地AI模型环境管理工具
  - 用途：本地conda环境的版本化管理和快速部署
  - 集成方式：与现有conda环境无缝集成，支持环境导出和恢复

### 风险和备用方案
- **模型备用**：Stable Diffusion + ControlNet作为Z-Image-Edit的备用方案
- **云服务备份**：多云部署，避免单点故障
- **CDN备用**：多个CDN提供商切换机制
- **支付备用**：多个支付渠道并行运行

---

**文档版本**：v1.0  
**最后更新**：2025-12-28  
**维护者**：GlobalPic AI 团队
