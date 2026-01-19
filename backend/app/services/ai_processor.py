"""
AI图像处理服务
集成 ModelScope API 进行图像处理
"""
import base64
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

from app.services.zimage_service import zimage_service
from app.services.ocr_service import ocr_service  # 保留 OCR 用于文字检测

logger = logging.getLogger(__name__)


class AIImageProcessor:
    """AI图像处理器 - 统一处理所有AI任务"""

    def __init__(self):
        self.models_loaded = False
        self.logger = logging.getLogger(__name__)

        self.model_status = {
            "zimage_turbo": False,
            "ocr": False
        }

    async def initialize_models(self) -> bool:
        """初始化AI服务"""
        self.logger.info("开始初始化AI服务...")

        try:
            # 初始化 Z-Image-Turbo (ModelScope API)
            zimage_result = await zimage_service.initialize()

            # 初始化 OCR 服务
            ocr_result = await ocr_service.initialize()

            self.model_status["zimage_turbo"] = zimage_result
            self.model_status["ocr"] = ocr_result

            self.models_loaded = zimage_result

            if self.models_loaded:
                self.logger.info("AI服务初始化完成 (ModelScope API)")
            else:
                failed = [k for k, v in self.model_status.items() if not v]
                self.logger.warning(f"部分服务初始化失败: {failed}")

            return self.models_loaded

        except Exception as e:
            self.logger.error(f"AI服务初始化失败: {e}")
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
                "error": "AI服务未初始化",
                "processing_time": 0
            }

        start_time = datetime.now()

        try:
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
        self.logger.info("开始文字抹除处理 (ModelScope API)")

        try:
            ocr_result = await ocr_service.detect_text(image)
            if not ocr_result["success"]:
                return {
                    "success": False,
                    "error": "文字检测失败"
                }

            text_regions = ocr_result["text_regions"]
            self.logger.info(f"检测到{len(text_regions)}个文字区域")

            if not text_regions:
                return {
                    "success": False,
                    "error": "未检测到文字"
                }

            mask = await ocr_service._generate_mask(image, text_regions, padding=5)

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

            output_urls = [img["data"] for img in inpaint_result["images"]]

            return {
                "output_urls": output_urls,
                "quality_score": inpaint_result["quality_score"],
                "text_regions_found": len(text_regions),
                "processing_steps": ["OCR检测", "掩码生成", "ModelScope API图像修复", "质量评估"]
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
        self.logger.info("开始背景重绘处理 (ModelScope API)")

        try:
            style_id = parameters.get("style_id", "minimal_white")

            # 使用 ModelScope API 直接生成背景和合成
            style_prompt = zimage_service.STYLE_PROMPTS.get(
                style_id,
                zimage_service.STYLE_PROMPTS["minimal_white"]
            )

            # 生成产品变体图
            results = await zimage_service.generate(
                prompt=f"Product photography, {style_prompt}",
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
                "processing_steps": ["ModelScope API背景生成", "质量评估"]
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

    def get_processing_status(self) -> Dict[str, Any]:
        """获取处理状态"""
        return {
            "models_loaded": self.models_loaded,
            "model_status": self.model_status,
            "api_type": "model_scope",
            "supported_operations": ["text_removal", "background_replacement"],
            "zimage_status": zimage_service.get_status(),
            "ocr_status": ocr_service.get_status(),
        }


# 全局AI处理器实例
ai_processor = AIImageProcessor()
