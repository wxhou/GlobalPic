# Smart Copywriting Specification

## ADDED Requirements

### Requirement: GPT-4o-mini集成
系统 MUST 使用GPT-4o-mini生成营销文案

#### Scenario: API初始化
**Given** 系统启动时
**When** 调用文案服务初始化
**Then** 配置OpenAI API密钥
**And** 设置模型为 gpt-4o-mini
**And** 配置请求参数 (temperature=0.7, max_tokens=500)

#### Scenario: 文案生成
**Given** 用户上传产品图片
**When** 调用文案生成接口
**Then** 系统分析图片内容
**And** 调用GPT-4o-mini生成文案
**And** 返回5条不同风格的文案
**And** 生成时间 < 5秒

### Requirement: 多平台文案适配
系统 MUST 根据目标平台生成适配的文案

#### Scenario: 亚马逊文案
**Given** 用户选择亚马逊平台
**When** 生成文案
**Then** 标题符合亚马逊规范 (200字符内)
**And** 描述包含核心关键词
**And** 突出产品卖点和使用场景

#### Scenario: TikTok文案
**Given** 用户选择TikTok平台
**When** 生成文案
**Then** 风格年轻化、活泼
**And** 包含热门标签
**And** 适合短视频描述

#### Scenario: 独立站文案
**Given** 用户选择独立站平台
**When** 生成文案
**Then** 风格专业、品牌化
**And** 包含品牌关键词
**And** 适合SEO优化

### Requirement: SEO优化
系统 MUST 生成符合SEO要求的文案

#### Scenario: 关键词优化
**Given** 产品类别和特点
**When** 生成SEO文案
**Then** 标题包含核心关键词
**And** 描述关键词密度2-5%
**And** 避免关键词堆砌

#### Scenario: 多语言支持
**Given** 支持中英文双语
**When** 生成多语言文案
**Then** 英文文案语法正确
**And** 中文翻译自然流畅
**And** 保持原意一致

### Requirement: 文案管理
系统 MUST 支持文案的存储和复用

#### Scenario: 文案保存
**Given** 用户生成了满意的文案
**When** 用户保存文案
**Then** 文案存储到用户账户
**And** 可以随时查看和编辑
**And** 支持导出功能

#### Scenario: 文案模板
**Given** 系统预设文案模板
**When** 用户选择模板
**Then** 基于模板生成个性化文案
**And** 保持模板结构和风格
**And** 支持用户自定义模板

## MODIFIED Requirements

### Requirement: image-processing: 文案生成
GPT-4o-mini MUST 根据图片生成符合SEO要求的英文营销文案

#### ADDED: Copywriting Service
```python
class CopywritingService:
    """智能文案生成服务"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.templates = {
            "amazon": {
                "title": "【品牌】{产品名} - {核心卖点}",
                "structure": "开头引入 + 产品描述 + 使用场景 + 购买理由"
            },
            "tiktok": {
                "title": "{产品名} | {爆款描述}",
                "structure": "吸引注意 + 产品亮点 + 行动号召"
            },
            "independent": {
                "title": "{产品名} | {品牌slogan}",
                "structure": "品牌故事 + 产品价值 + 差异化优势"
            }
        }

    async def generate(
        self,
        image_description: str,
        platform: str,
        count: int = 5
    ) -> List[str]:
        """生成营销文案"""
        prompt = self._build_prompt(image_description, platform, count)
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return self._parse_response(response)

    def _build_prompt(
        self,
        image_description: str,
        platform: str,
        count: int
    ) -> str:
        """构建生成提示词"""
        template = self.templates.get(platform, self.templates["amazon"])
        return f"""
根据以下产品图片描述，为{platform}平台生成{count}条营销文案。

产品描述: {image_description}

模板结构: {template['structure']}

要求:
1. 每条文案独立完整
2. 标题不超过平台限制
3. 包含产品核心卖点
4. 语言生动有吸引力
5. SEO友好

输出格式: 每条文案用###分隔
"""
```
