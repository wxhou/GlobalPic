"""
ModelScope API 客户端
提供图像生成和编辑的异步接口
"""
import asyncio
import base64
import io
import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from PIL import Image
import httpx

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEED = "SUCCEED"
    FAILED = "FAILED"


class ModelScopeClient:
    """ModelScope API 客户端"""

    BASE_URL = "https://api-inference.modelscope.cn"
    TIMEOUT = 60.0  # HTTP 超时
    POLL_INTERVAL = 5  # 轮询间隔（秒）
    MAX_RETRIES = 3  # 最大重试次数

    def __init__(self, api_key: str = None):
        """初始化客户端"""
        self.api_key = api_key
        self.http_client = httpx.AsyncClient(
            timeout=self.TIMEOUT,
            follow_redirects=True
        )
        self._task_locks: Dict[str, asyncio.Lock] = {}

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def close(self):
        """关闭客户端"""
        await self.http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _submit_task(
        self,
        prompt: str,
        model: str = "Tongyi-MAI/Z-Image-Turbo",
        loras: Optional[Dict[str, float]] = None,
        image: Optional[str] = None,
        mask: Optional[str] = None,
    ) -> str:
        """提交生成任务

        Args:
            prompt: 提示词
            model: 模型 ID
            loras: LoRA 配置
            image: 输入图像 (base64)
            mask: 掩码 (base64)

        Returns:
            任务 ID
        """
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
        }

        if loras:
            payload["loras"] = loras

        if image:
            payload["image"] = image

        if mask:
            payload["mask_image"] = mask

        headers = self._get_headers()
        headers["X-ModelScope-Async-Mode"] = "true"

        response = await self.http_client.post(
            f"{self.BASE_URL}/v1/images/generations",
            headers=headers,
            content=json.dumps(payload, ensure_ascii=False).encode('utf-8')
        )
        response.raise_for_status()

        task_id = response.json().get("task_id")
        if not task_id:
            raise ValueError("响应中未找到 task_id")

        logger.info(f"提交任务成功: {task_id}")
        return task_id

    async def _get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态信息
        """
        headers = self._get_headers()
        headers["X-ModelScope-Task-Type"] = "image_generation"

        response = await self.http_client.get(
            f"{self.BASE_URL}/v1/tasks/{task_id}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def _wait_for_result(
        self,
        task_id: str,
        max_wait: int = 600,  # 最大等待时间（秒）
    ) -> Dict[str, Any]:
        """等待任务完成

        Args:
            task_id: 任务 ID
            max_wait: 最大等待时间

        Returns:
            任务结果
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise TimeoutError(f"任务 {task_id} 等待超时")

            status_data = await self._get_task_status(task_id)
            task_status = status_data.get("task_status", TaskStatus.PROCESSING.value)

            logger.debug(f"任务 {task_id} 状态: {task_status}")

            if task_status == TaskStatus.SUCCEED.value:
                return {
                    "success": True,
                    "task_id": task_id,
                    "output_images": status_data.get("output_images", []),
                    "elapsed_time": elapsed,
                }
            elif task_status == TaskStatus.FAILED.value:
                error_msg = status_data.get("task_msg", "Unknown error")
                raise RuntimeError(f"任务失败: {error_msg}")

            await asyncio.sleep(self.POLL_INTERVAL)

    async def generate(
        self,
        prompt: str,
        num_images: int = 4,
        model: str = "Tongyi-MAI/Z-Image-Turbo",
        loras: Optional[Dict[str, float]] = None,
        width: int = 1024,
        height: int = 1024,
    ) -> Dict[str, Any]:
        """生成图像

        Args:
            prompt: 提示词
            num_images: 生成数量
            model: 模型 ID
            loras: LoRA 配置
            width: 图像宽度
            height: 图像高度

        Returns:
            生成结果
        """
        start_time = time.time()

        try:
            # 构建完整提示词
            full_prompt = f"{prompt}, professional photography, high quality, sharp focus, detailed"
            if width == height == 1024:
                full_prompt += ", 1024x1024"
            elif width == height == 512:
                full_prompt += ", 512x512"
            else:
                full_prompt += f", {width}x{height}"

            # 提交任务
            task_id = await self._submit_task(
                prompt=full_prompt,
                model=model,
                loras=loras,
            )

            # 等待结果
            result = await self._wait_for_result(task_id)

            # 下载并处理图像
            images = []
            for i, image_url in enumerate(result["output_images"]):
                try:
                    image_response = await self.http_client.get(image_url)
                    image_response.raise_for_status()

                    image = Image.open(io.BytesIO(image_response.content)).convert("RGB")
                    image.thumbnail((2048, 2048), Image.LANCZOS)

                    # 转换为 base64
                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG", quality=90)
                    img_str = base64.b64encode(buffer.getvalue()).decode()

                    images.append({
                        "index": i,
                        "data": f"data:image/jpeg;base64,{img_str}",
                        "size": {"width": image.width, "height": image.height},
                        "url": image_url,
                    })
                except Exception as e:
                    logger.error(f"下载图像 {i} 失败: {e}")

            processing_time = time.time() - start_time

            return {
                "success": True,
                "task_id": task_id,
                "images": images,
                "prompt_used": full_prompt,
                "processing_time": processing_time,
                "quality_score": 4.5,  # ModelScope API 生成质量稳定
                "model": model,
            }

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
        model: str = "Tongyi-MAI/Z-Image-Turbo",
    ) -> Dict[str, Any]:
        """图像修复（用于文字擦除）

        Args:
            image: 输入图像 (PIL Image)
            mask: 修复掩码 (PIL Image, 白色区域将被修复)
            prompt: 修复提示词
            num_images: 生成数量
            model: 模型 ID

        Returns:
            修复结果
        """
        start_time = time.time()

        try:
            # 转换图像为 base64
            def image_to_base64(img: Image.Image) -> str:
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode()

            image_b64 = image_to_base64(image)
            mask_b64 = image_to_base64(mask)

            # 构建完整提示词
            full_prompt = f"{prompt}, seamless inpainting, natural blending, professional quality"

            # 提交任务
            task_id = await self._submit_task(
                prompt=full_prompt,
                model=model,
                image=image_b64,
                mask=mask_b64,
            )

            # 等待结果
            result = await self._wait_for_result(task_id)

            # 下载并处理图像
            images = []
            for i, image_url in enumerate(result.get("output_images", [])):
                try:
                    image_response = await self.http_client.get(image_url)
                    image_response.raise_for_status()

                    result_img = Image.open(
                        io.BytesIO(image_response.content)
                    ).convert("RGB")

                    buffer = io.BytesIO()
                    result_img.save(buffer, format="JPEG", quality=90)
                    img_str = base64.b64encode(buffer.getvalue()).decode()

                    images.append({
                        "index": i,
                        "data": f"data:image/jpeg;base64,{img_str}",
                        "size": {"width": result_img.width, "height": result_img.height},
                        "url": image_url,
                    })
                except Exception as e:
                    logger.error(f"下载修复图像 {i} 失败: {e}")

            processing_time = time.time() - start_time

            return {
                "success": True,
                "task_id": task_id,
                "images": images,
                "prompt_used": full_prompt,
                "processing_time": processing_time,
                "quality_score": 4.5,
                "model": model,
            }

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
        result = await self.generate(
            prompt=prompt,
            num_images=1,
            width=width,
            height=height,
        )

        if result["success"]:
            img_data = base64.b64decode(
                result["images"][0]["data"].split(",")[1]
            )
            return Image.open(io.BytesIO(img_data))
        else:
            raise RuntimeError(f"背景生成失败: {result.get('error')}")


# 便捷函数：创建客户端
def create_client(api_key: str = None) -> ModelScopeClient:
    """创建 ModelScope 客户端

    Args:
        api_key: API Key，优先使用此值，否则从环境变量读取

    Returns:
        ModelScopeClient 实例
    """
    from app.core.config import settings

    key = api_key or settings.MODELSCOPE_API_KEY
    if not key:
        raise ValueError("ModelScope API Key 未配置，请设置 MODELSCOPE_API_KEY 环境变量")

    return ModelScopeClient(api_key=key)
