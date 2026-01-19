"""
Z-Image-Turbo 图像生成服务
使用 ModelScope API 进行图像生成
"""
import asyncio
import base64
import io
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from app.services.modelscope_client import ModelScopeClient, create_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class ZImageService:
    """Z-Image-Turbo图像生成服务 - 基于 ModelScope API"""

    # 支持的背景风格
    STYLE_PROMPTS = {
        "minimal_white": "clean white background, minimalist, professional product photography, high quality",
        "modern_home": "modern kitchen interior, contemporary furniture, natural lighting, lifestyle scene",
        "business": "professional office desk, business environment, clean workspace, corporate setting",
        "natural": "outdoor natural lighting, window light, soft shadows, organic background",
        "amazon_standard": "white background, product center, e-commerce photography, amazon listing",
        "tiktok_vibrant": "vibrant colors, trendy background, eye-catching, social media style, Gen Z aesthetic",
        "instagram_lifestyle": "fashionable lifestyle scene, aesthetic background, Instagram-worthy, influencer style",
        "shopify_custom": "custom brand background, unique design, e-commerce ready, professional product photography",
    }

    def __init__(self):
        self._client: Optional[ModelScopeClient] = None
        self._client_lock = asyncio.Lock()
        self.is_initialized = False

    def _get_client(self) -> ModelScopeClient:
        """获取 ModelScope 客户端"""
        if self._client is None:
            raise RuntimeError("ModelScope 客户端未初始化，请先调用 initialize()")
        return self._client

    async def initialize(self) -> bool:
        """初始化服务"""
        async with self._client_lock:
            if self.is_initialized:
                return True

            try:
                self._client = create_client()
                self.is_initialized = True
                logger.info("ModelScope 客户端初始化成功")
                return True
            except ValueError as e:
                logger.error(f"ModelScope 客户端初始化失败: {e}")
                return False
            except Exception as e:
                logger.error(f"ModelScope 客户端初始化异常: {e}")
                return False

    async def warmup(self) -> None:
        """ModelScope API 无需预热"""
        logger.debug("ModelScope API 无需预热")

    def _build_prompt(
        self,
        base_prompt: str,
        style_id: Optional[str] = None,
        strength: float = 0.8,
    ) -> str:
        """构建完整的生成提示词"""
        if style_id and style_id in self.STYLE_PROMPTS:
            style_prompt = self.STYLE_PROMPTS[style_id]
            prompt = f"{base_prompt}, {style_prompt}"
        else:
            prompt = base_prompt

        quality_modifiers = ", professional photography, high quality, sharp focus, detailed"
        prompt = f"{prompt}{quality_modifiers}"

        return prompt

    async def generate(
        self,
        prompt: str,
        style_id: Optional[str] = None,
        height: int = 1024,
        width: int = 1024,
        num_images: int = 4,
        strength: float = 0.8,
    ) -> Dict[str, Any]:
        """生成图像

        Args:
            prompt: 基础提示词
            style_id: 风格ID
            height: 生成图像高度
            width: 生成图像宽度
            num_images: 生成图像数量
            strength: 风格强度

        Returns:
            包含生成结果和元数据的字典
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "ModelScope 服务未初始化",
                "processing_time": 0,
            }

        client = self._get_client()
        start_time = time.time()

        try:
            full_prompt = self._build_prompt(prompt, style_id, strength)

            result = await client.generate(
                prompt=full_prompt,
                num_images=num_images,
                model=settings.MODELSCOPE_MODEL_ID,
                width=width,
                height=height,
            )

            processing_time = time.time() - start_time

            if result["success"]:
                logger.info(f"生成{num_images}张图像，耗时: {processing_time:.2f}秒")
                return {
                    "success": True,
                    "task_id": result.get("task_id"),
                    "images": result["images"],
                    "prompt_used": full_prompt,
                    "style_id": style_id,
                    "processing_time": processing_time,
                    "quality_score": result.get("quality_score", 4.5),
                }
            else:
                return result

        except Exception as e:
            logger.error(f"图像生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
            }

    async def inpaint(
        self,
        image: Image.Image,
        mask: Image.Image,
        prompt: str,
        num_images: int = 4,
    ) -> Dict[str, Any]:
        """图像修复（用于文字擦除）

        Args:
            image: 输入图像 (PIL Image)
            mask: 修复掩码 (PIL Image, 白色区域将被修复)
            prompt: 修复提示词
            num_images: 生成图像数量

        Returns:
            包含修复结果的字典
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "ModelScope 服务未初始化",
                "processing_time": 0,
            }

        client = self._get_client()
        start_time = time.time()

        try:
            inpaint_prompt = f"{prompt}, seamless inpainting, natural blending, professional quality"

            result = await client.inpaint(
                image=image,
                mask=mask,
                prompt=inpaint_prompt,
                num_images=num_images,
                model=settings.MODELSCOPE_MODEL_ID,
            )

            processing_time = time.time() - start_time

            if result["success"]:
                logger.info(f"修复{num_images}张图像，耗时: {processing_time:.2f}秒")
                return {
                    "success": True,
                    "task_id": result.get("task_id"),
                    "images": result["images"],
                    "prompt_used": inpaint_prompt,
                    "processing_time": processing_time,
                    "quality_score": result.get("quality_score", 4.5),
                }
            else:
                return result

        except Exception as e:
            logger.error(f"图像修复失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
            }

    async def generate_background(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
    ) -> Image.Image:
        """生成背景图像

        Args:
            prompt: 背景提示词
            width: 宽度
            height: 高度

        Returns:
            生成的背景图像
        """
        if not self.is_initialized:
            raise RuntimeError("ModelScope 服务未初始化")

        client = self._get_client()
        return await client.generate_background(
            prompt=prompt,
            width=width,
            height=height,
        )

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "is_initialized": self.is_initialized,
            "api_type": "model_scope",
            "model_id": settings.MODELSCOPE_MODEL_ID,
            "supported_styles": list(self.STYLE_PROMPTS.keys()),
            "default_size": {"width": 1024, "height": 1024},
        }


# 全局服务实例
zimage_service = ZImageService()
