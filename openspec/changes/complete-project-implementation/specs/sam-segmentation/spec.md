# SAM Segmentation Specification

## ADDED Requirements

### Requirement: 模型加载
SAM模型 MUST 支持zero-shot主体分割

#### Scenario: 模型初始化
**Given** 系统启动时
**When** 调用SAM模型加载
**Then** 加载 sam_vit_h_4b8939.pth 模型
**And** 模型加载到GPU
**And** 加载时间 < 30秒

#### Scenario: 模型配置
**Given** SAM模型已加载
**When** 配置分割参数
**Then** 设置分割模式 (automatic_mask, box prompts)
**And** 设置IoU阈值 > 0.9
**And** 设置稳定性分数阈值 > 0.9

### Requirement: 主体分割
系统 MUST 精确分割产品主体，边界准确率 > 98%

#### Scenario: 自动主体分割
**Given** 用户上传产品图片
**When** 调用自动分割接口
**Then** SAM自动检测主体区域
**And** 返回二值掩码
**And** 分割时间 < 3秒
**And** 边界准确率 > 98%

#### Scenario: 提示词分割
**Given** 用户指定分割区域 (边界框或点)
**When** 调用提示词分割接口
**Then** SAM根据提示词分割
**And** 返回指定区域的掩码
**And** 分割结果与提示词一致

### Requirement: 多主体处理
系统 MUST 支持多主体选择和处理

#### Scenario: 多主体检测
**Given** 图片包含多个产品
**When** 调用多主体检测
**Then** 返回所有检测到的主体掩码
**And** 每个主体有独立的掩码
**And** 按面积排序返回

#### Scenario: 主体选择
**Given** 多个主体被检测到
**When** 用户选择特定主体
**Then** 系统只保留选中的掩码
**And** 其他主体被排除
**And** 返回单一主体掩码

### Requirement: 掩码后处理
系统 MUST 对分割掩码进行后处理

#### Scenario: 掩码优化
**Given** 原始分割掩码
**When** 执行掩码优化
**Then** 去除小型噪点
**And** 平滑边缘轮廓
**And** 填充内部空洞

#### Scenario: 边缘羽化
**Given** 优化后的二值掩码
**When** 执行边缘羽化
**Then** 生成羽化掩码
**And** 羽化范围 2-5像素
**And** 用于平滑合成

## MODIFIED Requirements

### Requirement: image-processing: 主体分割提取
SAM MUST 精确提取产品主体用于背景重绘

#### ADDED: SAM Integration
```python
class SAMService:
    """SAM主体分割服务"""

    def __init__(self):
        self.sam = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    async def initialize(self):
        """初始化SAM模型"""
        self.sam = sam_model_registry["vit_h"](
            checkpoint="models/sam_vit_h_4b8939.pth"
        )
        self.sam.to(self.device)
        self.predictor = SamPredictor(self.sam)

    async def segment_subject(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        """分割图像主体"""
        self.predictor.set_image(image)
        masks, scores, _ = self.predictor.predict(
            multimask_output=True
        )
        # 选择最高分的掩码
        best_mask = masks[np.argmax(scores)]
        return best_mask
```

#### MODIFIED: Processing Steps
- 原步骤: 模拟的主体分割
- 新步骤: 使用SAM进行真实主体分割
- 新增: 掩码后处理优化
- 新增: 边缘羽化处理
