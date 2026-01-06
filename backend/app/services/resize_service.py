"""
尺寸适配服务
提供图像尺寸调整和平台适配功能
"""
import logging
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageResampling
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PlatformPreset:
    """平台尺寸预设"""
    id: str
    name: str
    width: int
    height: int
    description: str


class ResizeService:
    """尺寸适配服务"""

    # 电商平台尺寸预设
    PLATFORM_PRESETS: List[PlatformPreset] = [
        # 亚马逊
        PlatformPreset("amazon_primary", "亚马逊主图", 1000, 1000, "亚马逊主图标准尺寸"),
        PlatformPreset("amazon_lifestyle", "亚马逊场景图", 500, 500, "亚马逊变体场景图"),
        PlatformPreset("amazon_infographic", "亚马逊图文信息", 1000, 1500, "图文详情页"),
        # Shopify
        PlatformPreset("shopify_main", "Shopify主图", 2048, 2048, "标准产品主图"),
        PlatformPreset("shopify_thumbnail", "Shopify缩略图", 100, 100, "产品列表缩略图"),
        # Instagram
        PlatformPreset("instagram_square", "Instagram方图", 1080, 1080, "Instagram标准"),
        PlatformPreset("instagram_portrait", "Instagram竖图", 1080, 1350, "Instagram竖版"),
        PlatformPreset("instagram_story", "Instagram故事", 1080, 1920, "Stories格式"),
        # TikTok
        PlatformPreset("tiktok_feed", "TikTok信息流", 1080, 1920, "TikTok视频封面"),
        # 独立站
        PlatformPreset("ecommerce_standard", "独立站标准", 1200, 1200, "通用电商主图"),
        PlatformPreset("ecommerce_banner", "独立站横幅", 1920, 600, "网站横幅广告"),
        # 缩略图
        PlatformPreset("thumbnail_small", "小缩略图", 150, 150, "网格视图"),
        PlatformPreset("thumbnail_medium", "中缩略图", 300, 300, "列表视图"),
        # 社交媒体
        PlatformPreset("facebook_post", "Facebook帖子", 1200, 630, "动态图片"),
        PlatformPreset("twitter_card", "Twitter卡片", 1200, 628, "链接卡片"),
        PlatformPreset("pinterest_pin", "Pinterest图钉", 1000, 1500, "标准Pin"),
        # 京东/淘宝
        PlatformPreset("jd_main", "京东主图", 800, 800, "京东主图"),
        PlatformPreset("taobao_main", "淘宝主图", 800, 800, "淘宝主图"),
        PlatformPreset("taobao_detail", "淘宝详情", 750, 10000, "淘宝详情页"),
    ]

    # 常见比例
    ASPECT_RATIOS: Dict[str, Tuple[float, str]] = {
        "1:1": (1.0, "正方形"),
        "4:3": (4/3, "标准"),
        "3:4": (3/4, "竖版标准"),
        "16:9": (16/9, "宽银幕"),
        "9:16": (9/16, "竖屏"),
        "3:2": (3/2, "经典"),
        "2:3": (2/3, "肖像"),
    }

    # 重采样方法映射
    RESAMPLE_METHODS: Dict[str, int] = {
        "lanczos": Image.Resampling.LANCZOS,
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
        "nearest": Image.Resampling.NEAREST,
    }

    def __init__(self):
        self.is_initialized = True

    def get_presets(self, category: Optional[str] = None) -> List[Dict]:
        """获取尺寸预设列表"""
        presets = []
        for preset in self.PLATFORM_PRESETS:
            if category is None or self._get_preset_category(preset.id) == category:
                presets.append({
                    "id": preset.id,
                    "name": preset.name,
                    "width": preset.width,
                    "height": preset.height,
                    "description": preset.description,
                })
        return presets

    def _get_preset_category(self, preset_id: str) -> str:
        """获取预设分类"""
        categories = {
            "amazon": "电商平台",
            "shopify": "独立站",
            "instagram": "社交媒体",
            "tiktok": "短视频",
            "thumbnail": "缩略图",
            "facebook": "社交媒体",
            "twitter": "社交媒体",
            "pinterest": "社交媒体",
            "jd": "国内平台",
            "taobao": "国内平台",
            "ecommerce": "独立站",
        }
        for key, category in categories.items():
            if key in preset_id:
                return category
        return "其他"

    def get_categories(self) -> List[Dict]:
        """获取分类列表"""
        categories = set()
        for preset in self.PLATFORM_PRESETS:
            categories.add(self._get_preset_category(preset.id))
        return [{"id": cat, "name": cat} for cat in sorted(categories)]

    def resize_image(
        self,
        image: Image.Image,
        target_width: int,
        target_height: int,
        maintain_aspect_ratio: bool = True,
        resample_method: str = "lanczos",
        fit_mode: str = "contain",
        background_color: str = "#FFFFFF",
    ) -> Image.Image:
        """
        调整图像尺寸

        Args:
            image: 原始图像
            target_width: 目标宽度
            target_height: 目标高度
            maintain_aspect_ratio: 是否保持宽高比
            resample_method: 重采样方法 (lanczos, bilinear, bicubic, nearest)
            fit_mode: 适配模式 (cover, contain, fill, stretch)
            background_color: 背景颜色

        Returns:
            调整后的图像
        """
        original_width, original_height = image.size
        resample = self.RESAMPLE_METHODS.get(resample_method, Image.Resampling.LANCZOS)

        if maintain_aspect_ratio and fit_mode != "stretch":
            # 计算保持宽高比的尺寸
            aspect_ratio = original_width / original_height
            target_ratio = target_width / target_height

            if fit_mode == "contain":
                # 完整包含，可能有边框
                if aspect_ratio > target_ratio:
                    # 宽度优先
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)
                else:
                    # 高度优先
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)

                # 创建目标尺寸的图像
                result = Image.new("RGB", (target_width, target_height), background_color)
                paste_x = (target_width - new_width) // 2
                paste_y = (target_height - new_height) // 2
                resized = image.resize((new_width, new_height), resample)
                result.paste(resized, (paste_x, paste_y))
                return result

            elif fit_mode == "cover":
                # 完全覆盖，可能被裁剪
                if aspect_ratio > target_ratio:
                    # 高度优先，会裁剪宽度
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)
                else:
                    # 宽度优先，会裁剪高度
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)

                resized = image.resize((new_width, new_height), resample)

                # 裁剪到目标尺寸
                left = (new_width - target_width) // 2
                top = (new_height - target_height) // 2
                return resized.crop((left, top, left + target_width, top + target_height))

            elif fit_mode == "fill":
                # 拉伸填充（不使用宽高比）
                return image.resize((target_width, target_height), resample)

        else:
            # 直接拉伸或stretch模式
            return image.resize((target_width, target_height), resample)

    def crop_to_ratio(
        self,
        image: Image.Image,
        ratio: str,
        position: str = "center",
    ) -> Image.Image:
        """
        按比例裁剪图像

        Args:
            image: 原始图像
            ratio: 比例 (如 "16:9", "1:1")
            position: 裁剪位置 (center, top, bottom, left, right)
        """
        if ratio not in self.ASPECT_RATIOS:
            raise ValueError(f"不支持的比例: {ratio}")

        aspect_ratio = self.ASPECT_RATIOS[ratio][0]
        original_width, original_height = image.size
        original_ratio = original_width / original_height

        if original_ratio > aspect_ratio:
            # 图像太宽，裁剪左右
            new_width = int(original_height * aspect_ratio)
            if position == "left":
                left = 0
            elif position == "right":
                left = original_width - new_width
            else:
                left = (original_width - new_width) // 2
            return image.crop((left, 0, left + new_width, original_height))
        else:
            # 图像太高，裁剪上下
            new_height = int(original_width / aspect_ratio)
            if position == "top":
                top = 0
            elif position == "bottom":
                top = original_height - new_height
            else:
                top = (original_height - new_height) // 2
            return image.crop((0, top, original_width, top + new_height))

    def smart_resize(
        self,
        image: Image.Image,
        max_width: int = 2048,
        max_height: int = 2048,
        resample_method: str = "lanczos",
    ) -> Image.Image:
        """
        智能调整尺寸（限制最大尺寸，保持比例）
        """
        original_width, original_height = image.size

        if original_width <= max_width and original_height <= max_height:
            return image.copy()

        ratio = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)

        return image.resize((new_width, new_height), self.RESAMPLE_METHODS.get(
            resample_method, Image.Resampling.LANCZOS
        ))

    def get_status(self) -> Dict:
        """获取服务状态"""
        return {
            "initialized": self.is_initialized,
            "preset_count": len(self.PLATFORM_PRESETS),
            "categories": [cat["id"] for cat in self.get_categories()],
            "resample_methods": list(self.RESAMPLE_METHODS.keys()),
        }


# 全局服务实例
resize_service = ResizeService()
