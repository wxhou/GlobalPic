# Z-Image-Turbo Integration Specification

## ADDED Requirements

### Requirement: 模型加载与初始化
Z-Image-Turbo模型 MUST 支持bfloat16精度和自动设备选择

#### Scenario: 模型加载
**Given** 系统启动时
**When** 调用模型加载函数
**Then** 模型加载到GPU (优先cuda, 其次mps, 最后cpu)
**And** 使用bfloat16数据类型
**And** 设置Flash Attention优化
**And** 返回加载状态和设备信息

#### Scenario: 模型预热
**Given** 模型已加载
**When** 首次生成请求到达
**Then** 执行模型预热推理
**And** 后续请求无需预热
**And** 预热时间 < 5秒

### Requirement: 图像生成
Z-Image-Turbo MUST 支持8步推理生成高质量图像

#### Scenario: 基础图像生成
**Given** 用户提供了prompt和参数
**When** 调用图像生成接口
**Then** 使用8步推理 (num_inference_steps=8)
**And** guidance_scale设置为0.0
**And** 生成4张候选图像
**And** 每张生成时间 < 15秒

#### Scenario: 风格化生成
**Given** 用户选择了目标风格 (minimal_white, modern_home等)
**When** 调用图像生成接口
**Then** 将风格转换为对应的prompt
**And** 生成符合风格的图像
**And** 支持8种预设风格

### Requirement: 图像修复(Inpainting)
Z-Image-Turbo MUST 支持局部图像修复用于文字擦除

#### Scenario: 修复掩码生成
**Given** OCR检测到文字区域
**When** 生成修复掩码
**Then** 掩码覆盖所有文字区域
**And** 边缘羽化处理避免硬边
**And** 掩码格式与模型兼容

#### Scenario: 图像修复执行
**Given** 原图和修复掩码
**When** 调用修复接口
**Then** 使用Z-Image-Turbo进行修复
**And** 修复区域与周围融合自然
**And** 擦除准确率 > 95%

### Requirement: 性能优化
系统 MUST 实现推理性能优化

#### Scenario: 批处理优化
**Given** 多个生成请求同时到达
**When** 请求数量 > 1
**Then** 自动合并为批处理
**And** GPU利用率 > 80%
**And** 总处理时间减少 > 30%

#### Scenario: 结果缓存
**Given** 相同参数的生成请求
**When** 请求在24小时内重复
**Then** 返回缓存结果
**And** 响应时间 < 100ms
**And** 缓存命中率 > 20%

### Requirement: 错误处理
系统 MUST 实现完善的错误处理机制

#### Scenario: 模型加载失败
**Given** GPU内存不足
**When** 模型加载失败
**Then** 自动尝试CPU模式
**And** 记录错误日志
**And** 返回友好的错误信息

#### Scenario: 推理超时
**Given** 推理时间超过30秒
**When** 超时触发
**Then** 中断推理任务
**And** 释放GPU内存
**And** 返回超时错误

## MODIFIED Requirements

### Requirement: async-processing: Processing API
处理API MUST 支持真实的AI模型推理

#### REMOVED: Celery Worker Configuration
- 移除模拟的任务处理逻辑
- 移除模拟的延迟等待

#### ADDED: Z-Image-Turbo Integration
```python
class ZImageService:
    """Z-Image-Turbo图像生成服务"""

    def __init__(self):
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    async def initialize(self):
        """初始化模型"""
        self.pipe = ZImagePipeline.from_pretrained(
            "Tongyi-MAI/Z-Image-Turbo",
            torch_dtype=torch.bfloat16,
        )
        self.pipe.to(self.device)

    async def generate(
        self,
        prompt: str,
        height: int = 1024,
        width: int = 1024,
        num_images: int = 4
    ) -> List[Image.Image]:
        """生成图像"""
        images = self.pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_inference_steps=8,
            guidance_scale=0.0,
            num_images_per_prompt=num_images,
        ).images
        return images
```
