"""
智能文案生成服务
使用GPT-4o-mini生成营销文案
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class CopywritingService:
    """智能文案生成服务"""

    # 平台文案模板
    TEMPLATES = {
        "amazon": {
            "title_template": "[Brand] {product_name} - {key_benefit} | {key_feature}",
            "bullet_template": "• {feature}: {description}",
            "description_template": """{introduction}

{features}

{usage}

About Our Brand:
{brand_info}""",
        },
        "tiktok": {
            "title_template": "{product_name} ✨ {viral_description}",
            "bullet_template": "✓ {feature}",
            "description_template": """"POV: You just found the perfect {product_category}! 🔥

{introduction}

Why you need this:
{reasons}

Grab yours now! 🛒""",
        },
        "instagram": {
            "title_template": "{product_name} | {aesthetic_description}",
            "bullet_template": "✦ {feature}",
            "description_template": """{introduction}

{the_look}

✨ Key Features:
{features}

Shop the look! 💫""",
        },
        "独立站": {
            "title_template": "{product_name} | {brand_slogan}",
            "bullet_template": "▸ {feature}",
            "description_template": """{introduction}

{story}

Product Details:
{features}

Quality Guarantee:
{guarantee}""",
        },
    }

    # SEO关键词库
    SEO_KEYWORDS = {
        "general": [
            "premium quality",
            "best seller",
            "customer favorite",
            "limited edition",
            "must-have",
        ],
        "home": ["modern design", "stylish", "elegant", "minimalist", "home decor"],
        "fashion": ["trendy", "stylish", "fashionable", "chic", "classic"],
        "tech": ["innovative", "smart", "cutting-edge", "advanced", "premium"],
    }

    def __init__(self):
        self.client = None
        self.is_initialized = False
        self._model_lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """初始化文案服务"""
        if self.is_initialized:
            return True

        async with self._model_lock:
            if self.is_initialized:
                return True

            try:
                from app.core.config import settings

                # 检查API密钥
                if not settings.OPENAI_API_KEY:
                    logger.warning("OpenAI API密钥未配置，使用模拟模式")
                    return False

                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.is_initialized = True
                logger.info("Copywriting服务初始化完成")
                return True

            except Exception as e:
                logger.error(f"Copywriting服务初始化失败: {e}")
                return False

    async def generate(
        self,
        image_description: str,
        platform: str = "amazon",
        product_name: Optional[str] = None,
        count: int = 5,
        tone: str = "professional",
    ) -> Dict[str, Any]:
        """生成营销文案

        Args:
            image_description: 产品图片描述
            platform: 目标平台
            product_name: 产品名称
            count: 生成文案数量
            tone: 文案风格

        Returns:
            包含生成文案的字典
        """
        if not self.is_initialized:
            return self._generate_mock(image_description, platform, count)

        start_time = datetime.now()

        try:
            # 获取平台模板
            template = self.TEMPLATES.get(
                platform, self.TEMPLATES["amazon"]
            )

            # 构建提示词
            prompt = self._build_prompt(
                image_description,
                platform,
                product_name,
                count,
                tone,
            )

            # 调用GPT-4o-mini
            response = await asyncio.to_thread(
                self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt(platform, tone),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                )
            )

            content = response.choices[0].message.content
            processing_time = (datetime.now() - start_time).total_seconds()

            # 解析生成的文案
            copywrites = self._parse_response(content, count)

            # 生成SEO关键词
            keywords = self._generate_keywords(image_description, platform)

            return {
                "success": True,
                "copywrites": copywrites,
                "keywords": keywords,
                "platform": platform,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"文案生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds(),
            }

    def _build_prompt(
        self,
        image_description: str,
        platform: str,
        product_name: Optional[str],
        count: int,
        tone: str,
    ) -> str:
        """构建生成提示词"""
        template = self.TEMPLATES.get(platform, self.TEMPLATES["amazon"])

        return f"""
根据以下产品图片描述，为{platform}平台生成{count}条营销文案。

产品描述: {image_description}

产品名称: {product_name or '未知产品'}

文案风格: {tone}

请为每个版本生成:
1. 吸引人的标题
2. 核心卖点列表 (3-5点)
3. 详细的描述段落

输出格式(JSON):
{{
    "copywrites": [
        {{
            "title": "标题",
            "bullets": ["卖点1", "卖点2", "卖点3"],
            "description": "详细描述"
        }}
    ]
}}
"""

    def _get_system_prompt(self, platform: str, tone: str) -> str:
        """获取系统提示词"""
        tone_descriptions = {
            "professional": "专业、正式、突出产品价值",
            "casual": "轻松、友好、贴近消费者",
            "luxury": "高端、优雅、强调品质",
            "fun": "活泼、有趣、适合社交媒体",
        }

        platform_notes = {
            "amazon": "亚马逊风格需要简洁明了，突出关键词，适合SEO",
            "tiktok": "TikTok风格需要年轻化、活泼、有病毒传播潜力",
            "instagram": "Instagram风格需要美观、时尚、适合视觉展示",
            "独立站": "独立站风格需要品牌化、专业、建立信任感",
        }

        return f"""你是一位专业的电商营销文案专家。

风格要求: {tone_descriptions.get(tone, tone_descriptions['professional'])}
平台特点: {platform_notes.get(platform, '')}

请生成高质量的营销文案，确保:
1. 标题吸引人，包含核心卖点
2. 卖点简洁有力
3. 描述突出产品价值
4. 符合平台规范和SEO要求"""

    def _parse_response(self, content: str, count: int) -> List[Dict[str, Any]]:
        """解析生成的文案"""
        try:
            # 尝试提取JSON
            content = content.strip()

            # 查找JSON块
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            # 解析JSON
            data = json.loads(content)
            copywrites = data.get("copywrites", [])

            # 确保返回指定数量
            while len(copywrites) < count:
                copywrites.append(copywrites[0].copy())

            return copywrites[:count]

        except Exception as e:
            logger.warning(f"JSON解析失败: {e}，使用备用解析")
            return self._fallback_parse(content, count)

    def _fallback_parse(self, content: str, count: int) -> List[Dict[str, Any]]:
        """备用解析方法"""
        copywrites = []

        # 按###分隔
        sections = content.split("###")

        for i, section in enumerate(sections[1:]):
            if len(copywrites) >= count:
                break

            lines = section.strip().split("\n")
            title = lines[0].strip() if lines else f"版本{i+1}"

            bullets = [l.strip().strip("•-").strip() for l in lines[1:] if l.strip().startswith(("•", "-"))]

            description = "\n".join([l for l in lines if not l.strip().startswith(("•", "-"))])

            copywrites.append({
                "title": title,
                "bullets": bullets,
                "description": description,
            })

        return copywrites

    def _generate_keywords(
        self, image_description: str, platform: str
    ) -> List[str]:
        """生成SEO关键词"""
        # 提取产品类别
        category = "general"
        for cat in ["home", "fashion", "tech"]:
            if cat in image_description.lower():
                category = cat

        # 获取关键词
        keywords = self.SEO_KEYWORDS.get(category, self.SEO_KEYWORDS["general"])

        # 添加平台特定关键词
        platform_keywords = {
            "amazon": ["Amazon Best Seller", "Amazon Choice", "Top Rated"],
            "tiktok": ["TikTokMadeMeBuyIt", "Viral", "MustHave"],
            "instagram": ["InstaGood", "ShopNow", "Trending"],
        }

        keywords.extend(platform_keywords.get(platform, []))

        return list(set(keywords))[:10]

    def _generate_mock(
        self, image_description: str, platform: str, count: int
    ) -> Dict[str, Any]:
        """生成模拟文案（当API不可用时）"""
        import random

        copywrites = []
        sample_titles = {
            "amazon": [
                "Premium Quality Product - Best Seller Choice",
                "Top Rated Item - Customer Favorite",
                "Essential Product - Limited Edition",
            ],
            "tiktok": [
                "This changed everything! ✨",
                "You need this in your life! 🔥",
                "Best discovery ever! 💫",
            ],
            "instagram": [
                "The aesthetics you need ✨",
                "Love this look! 💫",
                "Essential vibes only ✨",
            ],
        }

        sample_bullets = [
            "Premium quality materials",
            "Durable and long-lasting",
            "Modern design aesthetic",
            "Perfect for everyday use",
            "Customer favorite item",
        ]

        sample_descriptions = {
            "amazon": "Introducing our premium product, designed to exceed your expectations. Crafted with precision and care, this item delivers exceptional value. Experience the difference today.",
            "tiktok": "POV: You just found your new favorite thing! Trust us, you need this in your life ASAP. Don't miss out on this game-changer!",
            "instagram": "The look you've been waiting for. Elevate your style with this stunning piece. Perfect for any occasion, designed to impress.",
        }

        titles = sample_titles.get(platform, sample_titles["amazon"])

        for i in range(count):
            copywrites.append({
                "title": random.choice(titles),
                "bullets": random.sample(sample_bullets, 3),
                "description": sample_descriptions.get(platform, sample_descriptions["amazon"]),
            })

        return {
            "success": True,
            "copywrites": copywrites,
            "keywords": self._generate_keywords(image_description, platform),
            "platform": platform,
            "processing_time": 0.1,
            "mock": True,
        }

    async def generate_for_product(
        self,
        product_info: Dict[str, Any],
        platform: str = "amazon",
    ) -> Dict[str, Any]:
        """为产品信息生成文案

        Args:
            product_info: 产品信息字典
            platform: 目标平台

        Returns:
            包含生成文案的字典
        """
        # 构建产品描述
        description_parts = []

        if product_info.get("name"):
            description_parts.append(f"产品名称: {product_info['name']}")

        if product_info.get("category"):
            description_parts.append(f"类别: {product_info['category']}")

        if product_info.get("features"):
            description_parts.append(f"特点: {', '.join(product_info['features'])}")

        if product_info.get("style"):
            description_parts.append(f"风格: {product_info['style']}")

        image_description = " | ".join(description_parts)

        return await self.generate(
            image_description=image_description,
            platform=platform,
            product_name=product_info.get("name"),
            count=product_info.get("copywrite_count", 5),
            tone=product_info.get("tone", "professional"),
        )

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "is_initialized": self.is_initialized,
            "model": "gpt-4o-mini",
            "supported_platforms": list(self.TEMPLATES.keys()),
            "supported_tones": ["professional", "casual", "luxury", "fun"],
        }


# 全局服务实例
copywriting_service = CopywritingService()
