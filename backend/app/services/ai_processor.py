"""
AI图像处理服务
集成真实的AI模型进行图像处理
"""
import base64
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

from app.services.zimage_service import zimage_service
from app.services.sam_service import sam_service
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)


class AIImageProcessor:
    """AI图像处理器 - 统一处理所有AI任务"""

    def __init__(self):
        self.models_loaded = False
        self.logger = logging.getLogger(__name__)

        # 模型状态
        self.model_status = {
            "zimage_turbo": False,
            "sam": False,
            "easyocr": False
        }

    async def initialize_models(self) -> bool:
        """初始化AI模型"""
        self.logger.info("开始初始化AI模型...")

        try:
            # 初始化各个服务
            results = await asyncio.gather(
                zimage_service.initialize(),
                sam_service.initialize(),
                ocr_service.initialize(),
                return_exceptions=True
            )

            # 更新模型状态
            self.model_status["zimage_turbo"] = (
                not isinstance(results[0], Exception) and results[0]
            )
            self.model_status["sam"] = (
                not isinstance(results[1], Exception) and results[1]
            )
            self.model_status["easyocr"] = (
                not isinstance(results[2], Exception) and results[2]
            )

            self.models_loaded = all(self.model_status.values())

            if self.models_loaded:
                self.logger.info("所有AI模型初始化完成")
            else:
                failed = [k for k, v in self.model_status.items() if not v]
                self.logger.warning(f"部分模型初始化失败: {failed}")

            return self.models_loaded

        except Exception as e:
            self.logger.error(f"AI模型初始化失败: {e}")
            return False

    async def process_image(
        self,
        image_path: str,
        operation_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理图像"""
        if not self.models_loaded:
            return {
                "success": False,
                "error": "AI模型未初始化",
                "processing_time": 0
            }

        start_time = datetime.now()

        try:
            # 加载图像
            image = self._load_image(image_path)
            if image is None:
                return {
                    "success": False,
                    "error": "无法加载图像",
                    "processing_time": 0
                }

            if operation_type == "text_removal":
                result = await self._process_text_removal(image, parameters)
            elif operation_type == "background_replacement":
                result = await self._process_background_replacement(image, parameters)
            else:
                return {
                    "success": False,
                    "error": f"不支持的操作类型: {operation_type}",
                    "processing_time": (datetime.now() - start_time).total_seconds()
                }

            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "processing_time": processing_time,
                "result": result
            }

        except Exception as e:
            self.logger.error(f"图像处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }

    async def _process_text_removal(
        self,
        image: Image.Image,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """文字抹除处理"""
        self.logger.info("开始文字抹除处理")

        try:
            # 步骤1: OCR文字检测
            ocr_result = await ocr_service.detect_text(image)
            if not ocr_result["success"]:
                return {
                    "success": False,
                    "error": "文字检测失败"
                }

            text_regions = ocr_result["text_regions"]
            self.logger.info(f"检测到{len(text_regions)}个文字区域")

            # 步骤2: 生成修复掩码
            mask = await ocr_service._generate_mask(image, text_regions, padding=5)

            # 步骤3: 使用Z-Image-Turbo进行修复
            inpaint_result = await zimage_service.inpaint(
                image=image,
                mask=mask,
                prompt="Clean background, no text, professional product photography",
                num_images=4
            )

            if not inpaint_result["success"]:
                return {
                    "success": False,
                    "error": "图像修复失败"
                }

            # 提取结果URLs
            output_urls = [img["data"] for img in inpaint_result["images"]]

            return {
                "output_urls": output_urls,
                "quality_score": inpaint_result["quality_score"],
                "text_regions_found": len(text_regions),
                "processing_steps": ["OCR检测", "掩码生成", "图像修复", "质量评估"]
            }

        except Exception as e:
            self.logger.error(f"文字抹除处理失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _process_background_replacement(
        self,
        image: Image.Image,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """背景重绘处理"""
        self.logger.info("开始背景重绘处理")

        try:
            style_id = parameters.get("style_id", "minimal_white")

            # 步骤1: SAM主体分割
            seg_result = await sam_service.segment_subject(image)
            if not seg_result["success"]:
                return {
                    "success": False,
                    "error": "主体分割失败"
                }

            # 步骤2: 获取掩码
            mask = sam_service._decode_mask(seg_result["mask"])

            # 步骤3: 使用Z-Image-Turbo生成背景
            background = await zimage_service.generate_background(
                prompt=zimage_service.STYLE_PROMPTS.get(
                    style_id,
                    zimage_service.STYLE_PROMPTS["minimal_white"]
                ),
                width=image.width,
                height=image.height
            )

            # 步骤4: 合成最终图像
            from app.services.zimage_service import zimage_service as zservice
            composite = zservice._composite_image(image, background, mask)

            # 生成4张变体
            results = await zimage_service.generate(
                prompt="Product photography, clean composition, professional lighting",
                style_id=style_id,
                width=image.width,
                height=image.height,
                num_images=4
            )

            if not results["success"]:
                return {
                    "success": False,
                    "error": "背景生成失败"
                }

            output_urls = [img["data"] for img in results["images"]]

            return {
                "output_urls": output_urls,
                "quality_score": results["quality_score"],
                "background_style": style_id,
                "prompt_used": results["prompt_used"],
                "processing_steps": ["SAM分割", "背景生成", "图像合成", "质量评估"]
            }

        except Exception as e:
            self.logger.error(f"背景重绘处理失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _load_image(self, image_path: str) -> Optional[Image.Image]:
        """加载图像"""
        try:
            path = Path(image_path)
            if path.exists():
                return Image.open(path).convert("RGB")
            return None
        except Exception as e:
            self.logger.error(f"加载图像失败: {e}")
            return None

    def _generate_background_prompt(self, style_id: str) -> str:
        """生成背景提示词"""
        style_prompts = {
            "minimal_white": "clean white background, minimalist, professional product photography",
            "modern_home": "modern kitchen interior, contemporary furniture, natural lighting",
            "business": "professional office desk, business environment, clean workspace",
            "natural": "outdoor natural lighting, window light, soft shadows, organic",
            "amazon_standard": "white background, product center, e-commerce photography",
            "tiktok_vibrant": "vibrant colors, trendy background, eye-catching, social media",
            "instagram_lifestyle": "fashionable lifestyle scene, aesthetic background",
            "shopify_custom": "custom brand background, unique design, e-commerce ready"
        }

        base_prompt = style_prompts.get(style_id, style_prompts["minimal_white"])
        quality_modifiers = ", professional, high quality, sharp focus, detailed"

        return f"{base_prompt}{quality_modifiers}"

    def get_processing_status(self) -> Dict[str, Any]:
        """获取处理状态"""
        return {
            "models_loaded": self.models_loaded,
            "model_status": self.model_status,
            "supported_operations": ["text_removal", "background_replacement"],
            "zimage_status": zimage_service.get_status(),
            "sam_status": sam_service.get_status(),
            "ocr_status": ocr_service.get_status(),
        }


# 导入asyncio
import asyncio

# 全局AI处理器实例
ai_processor = AIImageProcessor()
