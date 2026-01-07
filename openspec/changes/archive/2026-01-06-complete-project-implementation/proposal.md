# OpenSpec Proposal: Complete Project Implementation

## Change ID
complete-project-implementation

## Overview
完成GlobalPic AI项目的所有核心功能，实现从MVP到商业化所需的完整功能集，包括真实的AI模型集成、批量处理、文案生成、支付订阅等。

## Why

### 当前状态分析
根据已归档的初始化变更，项目已完成：
- 基础项目结构（FastAPI后端 + React前端）
- 用户认证系统（JWT）
- 图像上传/管理API
- 模拟的AI处理器
- 基础前端组件

### 仍需完成的核心功能
根据需求文档，还有以下关键功能需要实现：

1. **真实AI模型集成** (P0)
   - Z-Image-Turbo模型真实推理
   - SAM主体分割真实集成
   - EasyOCR文字检测

2. **智能文案生成** (P1)
   - 基于GPT-4o-mini的SEO优化文案
   - 多平台文案适配

3. **批量处理功能** (P2)
   - 多图并行处理
   - 批量下载

4. **商业化功能** (P1)
   - 支付订阅系统
   - API访问控制

### 业务价值
- 完整的产品功能是商业化的基础
- 真实的AI处理能力决定产品竞争力
- 商业化功能是收入来源

## What Changes

### 新增功能模块

#### Phase 1: AI模型真实集成
- **Z-Image-Turbo真实推理**: 实现真正的图像生成和编辑
- **SAM分割集成**: 产品主体精确分割
- **EasyOCR文字检测**: 文字区域识别和定位
- **图像修复(Inpainting)**: 文字擦除的修复能力

#### Phase 2: 智能文案生成
- **GPT-4o-mini集成**: 智能文案生成服务
- **多平台文案适配**: 亚马逊/TikTok/独立站等
- **SEO优化**: 关键词密度优化

#### Phase 3: 批量处理
- **并行任务处理**: 多图同时处理
- **批量下载**: ZIP打包下载
- **处理队列管理**: 优先级和进度跟踪

#### Phase 4: 商业化功能
- **支付集成**: Stripe/PayPal
- **订阅管理**: 免费/个人版/企业版
- **API认证**: API Key管理
- **用量统计**: 额度追踪

### 技术变更

#### 后端变更
```
backend/app/services/
├── zimage_service.py      # Z-Image-Turbo集成
├── sam_service.py         # SAM分割服务
├── ocr_service.py         # 文字检测服务
├── copywriting_service.py # 文案生成服务
├── batch_processor.py     # 批量处理
└── payment_service.py     # 支付服务

backend/app/api/v1/
├── ai_models.py          # AI模型管理API
├── copywriting.py        # 文案生成API
├── batch.py              # 批量处理API
└── subscription.py       # 订阅管理API
```

#### 前端变更
```
frontend/src/
├── components/
│   ├── BatchProcessor.tsx   # 批量处理界面
│   ├── CopywritingPanel.tsx # 文案生成面板
│   ├── SubscriptionPlan.tsx # 订阅套餐选择
│   └── APIKeyManager.tsx    # API密钥管理
├── pages/
│   └── BatchProcessing.tsx  # 批量处理页面
└── hooks/
    └── useBatchProcessing.ts # 批量处理Hook
```

### 架构影响
- 引入新的AI服务层（真实模型推理）
- 扩展异步任务处理能力（批量任务）
- 增加支付和订阅管理模块
- 完善API认证和权限控制

## Architecture Decisions

### AI模型服务架构
```
┌─────────────────────────────────────────────────────────┐
│                   AI Service Layer                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ ZImageService│  │ SAMService  │  │ OCRService  │    │
│  │ (图像生成)   │  │ (主体分割)  │  │ (文字检测)  │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │           │
│         └────────────────┼────────────────┘           │
│                          ▼                            │
│              ┌─────────────────────┐                 │
│              │  UnifiedProcessor   │                 │
│              │  (统一处理接口)     │                 │
│              └─────────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

### 批量处理架构
- 使用BackgroundTasks处理单个任务
- Celery管理批量任务队列
- Redis跟踪任务进度
- WebSocket推送进度更新

### 支付架构
- Stripe处理订阅和按需付费
- Webhook处理支付事件
- PostgreSQL存储订阅状态

## Requirements

### Requirement: Z-Image-Turbo模型集成
Z-Image-Turbo MUST 支持真实的图像生成和编辑功能

#### Scenario: 图像生成
**Given** 用户选择了目标风格和参数
**When** 用户提交图像生成请求
**Then** 系统使用Z-Image-Turbo生成4张候选图
**And** 每张图生成时间 < 15秒
**And** 返回结果包含质量评分

#### Scenario: 图像编辑(修复)
**Given** 用户上传了包含文字的产品图
**When** 用户请求文字擦除
**Then** 系统识别文字区域并生成修复掩码
**And** 使用Z-Image-Turbo进行图像修复
**And** 擦除准确率 > 95%

### Requirement: SAM主体分割集成
SAM MUST 精确分割产品主体，边界准确率 > 98%

#### Scenario: 主体检测
**Given** 用户上传了产品图片
**When** 系统执行主体分割
**Then** 返回产品主体的二值掩码
**And** 分割时间 < 3秒
**And** 边界准确率 > 98%

#### Scenario: 多主体处理
**Given** 图片包含多个产品主体
**When** 用户选择要保留的主体
**Then** 系统只保留选中的主体掩码
**And** 其他主体被擦除

### Requirement: OCR文字检测
EasyOCR MUST 准确检测图片中的文字区域

#### Scenario: 文字区域识别
**Given** 用户上传了包含文字的图片
**When** 系统执行OCR检测
**Then** 返回文字区域的边界框
**And** 识别置信度 > 90%
**And** 支持中英文混合识别

### Requirement: 智能文案生成
GPT-4o-mini MUST 根据图片生成符合SEO要求的营销文案

#### Scenario: 文案生成
**Given** 用户选择了目标平台
**When** 用户请求生成营销文案
**Then** 系统生成5条不同风格的文案
**And** 文案包含产品关键词
**And** 符合平台SEO要求

#### Scenario: 文案适配
**Given** 用户选择了亚马逊平台
**When** 系统生成文案
**Then** 文案符合亚马逊SEO规范
**And** 标题包含核心关键词
**And** 描述突出产品卖点

### Requirement: 批量处理
系统 MUST 支持最多50张图片同时处理

#### Scenario: 批量任务创建
**Given** 用户上传了多张图片
**When** 用户选择批量处理
**Then** 系统创建批量任务
**And** 返回任务ID和预估时间
**And** 用户可以查看处理进度

#### Scenario: 批量结果下载
**Given** 批量处理完成
**When** 用户请求下载结果
**Then** 系统打包所有结果为ZIP
**And** 下载链接有效期24小时

### Requirement: 支付订阅
系统 MUST 支持订阅制和按需付费两种模式

#### Scenario: 订阅购买
**Given** 用户选择了$19/月个人版
**When** 用户完成支付
**Then** 用户账户升级为个人版
**And** 获得无限处理额度
**And** 订阅续费日期记录

#### Scenario: 按需购买
**Given** 用户选择了10张图片包
**When** 用户完成支付
**Then** 用户账户增加10次处理额度
**And** 额度永不过期

### Requirement: 企业版API
企业版用户 MUST 可以通过API Key访问服务

#### Scenario: API Key生成
**Given** 企业版用户请求API访问
**When** 用户生成API Key
**Then** 系统返回API Key
**And** 可以设置IP白名单
**And** 可以设置调用频率限制

#### Scenario: API调用
**Given** 用户使用有效API Key调用
**When** 请求通过认证
**Then** 返回处理结果
**And** 扣除对应额度

## Dependencies
- OpenAI API Key (GPT-4o-mini)
- Stripe账户 (支付处理)
- 足够的GPU资源 (模型推理)
- 扩展的Redis内存 (批量任务队列)

## Timeline Estimate
- Phase 1 (AI集成): 2-3周
- Phase 2 (文案生成): 1周
- Phase 3 (批量处理): 1周
- Phase 4 (商业化): 2周

## Risks and Mitigation
1. **GPU资源不足**: 使用云GPU服务，实施批处理优化
2. **API限流**: 实现缓存机制，申请更高配额
3. **支付安全**: 使用Stripe官方SDK，实施签名验证
