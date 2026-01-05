# background-replacement Specification

## Purpose
TBD - created by archiving change initialize-core-image-processing. Update Purpose after archive.
## Requirements
### Requirement: 主体分割

**Scenario**:
- 使用SAM模型分割图像主体
- 精确识别产品边界
- 处理时间 < 3秒
- 边界准确率 > 98%
- 支持复杂背景场景

### Requirement: 背景生成

**Scenario**:
- 使用Z-Image-Turbo生成新背景
- 支持多种欧美风格
- 保持光照一致性
- 边缘自然过渡
- 生成4张候选图

### Requirement: 风格选择

**Scenario**:
- 提供8种预设风格
- 极简白色、现代家居、商业环境、自然光线
- 亚马逊标准、TikTok风格、Instagram风格、Shopify定制
- 支持自定义提示词
- 风格预览缩略图

