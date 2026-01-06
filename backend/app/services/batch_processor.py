"""
批量处理服务
支持多图并行处理和批量下载
"""
import asyncio
import base64
import io
import json
import logging
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import uuid

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量处理服务"""

    # 处理状态
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self._task_lock = asyncio.Lock()

    async def create_task(
        self,
        user_id: int,
        image_data_list: List[Dict[str, Any]],
        operations: List[str],
        style_id: str = "minimal_white",
    ) -> Dict[str, Any]:
        """创建批量处理任务

        Args:
            user_id: 用户ID
            image_data_list: 图片数据列表 [{image: base64, filename: str}, ...]
            operations: 操作列表 ["text_removal", "background_replacement"]
            style_id: 风格ID

        Returns:
            任务信息字典
        """
        task_id = str(uuid.uuid4())

        async with self._task_lock:
            self.tasks[task_id] = {
                "task_id": task_id,
                "user_id": user_id,
                "status": self.STATUS_PENDING,
                "total_images": len(image_data_list),
                "processed_images": 0,
                "success_count": 0,
                "failed_count": 0,
                "operations": operations,
                "style_id": style_id,
                "image_data": image_data_list,
                "results": [],
                "errors": [],
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "progress": 0.0,
            }

        # 异步执行任务
        asyncio.create_task(self._process_task(task_id))

        return {
            "task_id": task_id,
            "status": self.STATUS_PENDING,
            "total_images": len(image_data_list),
            "estimated_time": self._estimate_time(len(image_data_list), operations),
        }

    async def _process_task(self, task_id: str) -> None:
        """处理批量任务"""
        async with self._task_lock:
            if task_id not in self.tasks:
                return
            task = self.tasks[task_id]

        try:
            # 更新状态
            task["status"] = self.STATUS_PROCESSING
            await self._update_task(task_id)

            # 初始化AI服务
            from app.services.zimage_service import zimage_service
            from app.services.sam_service import sam_service
            from app.services.ocr_service import ocr_service

            # 初始化服务
            await asyncio.gather(
                zimage_service.initialize(),
                sam_service.initialize(),
                ocr_service.initialize(),
            )

            # 逐个处理图片
            for i, image_data in enumerate(task["image_data"]):
                # 检查是否已取消
                async with self._task_lock:
                    if self.tasks[task_id]["status"] == self.STATUS_CANCELLED:
                        return

                try:
                    # 解码图片
                    image = self._decode_image(image_data["image"])

                    # 处理单张图片
                    result = await self._process_single_image(
                        image, task["operations"], task["style_id"]
                    )

                    async with self._task_lock:
                        task["processed_images"] += 1
                        task["success_count"] += 1 if result["success"] else 0
                        task["failed_count"] += 0 if result["success"] else 1
                        task["results"].append(
                            {
                                "index": i,
                                "filename": image_data.get("filename", f"image_{i}.jpg"),
                                "success": result["success"],
                                "output": result.get("output") if result["success"] else None,
                                "error": result.get("error") if not result["success"] else None,
                            }
                        )
                        task["progress"] = (
                            task["processed_images"] / task["total_images"]
                        ) * 100

                    await self._update_task(task_id)

                except Exception as e:
                    logger.error(f"处理图片{i}失败: {e}")
                    async with self._task_lock:
                        task["processed_images"] += 1
                        task["failed_count"] += 1
                        task["errors"].append({"index": i, "error": str(e)})
                        task["progress"] = (
                            task["processed_images"] / task["total_images"]
                        ) * 100

            # 任务完成
            async with self._task_lock:
                task["status"] = (
                    self.STATUS_COMPLETED
                    if task["success_count"] > 0
                    else self.STATUS_FAILED
                )
                task["completed_at"] = datetime.now().isoformat()

            await self._update_task(task_id)
            logger.info(f"批量任务{task_id}完成: 成功{task['success_count']}, 失败{task['failed_count']}")

        except Exception as e:
            logger.error(f"批量任务{task_id}执行失败: {e}")
            async with self._task_lock:
                task["status"] = self.STATUS_FAILED
                task["errors"].append({"error": str(e)})
                task["completed_at"] = datetime.now().isoformat()
            await self._update_task(task_id)

    async def _process_single_image(
        self, image: Image.Image, operations: List[str], style_id: str
    ) -> Dict[str, Any]:
        """处理单张图片"""
        from app.services.zimage_service import zimage_service
        from app.services.sam_service import sam_service
        from app.services.ocr_service import ocr_service

        start_time = time.time()

        try:
            output_urls = []

            for operation in operations:
                if operation == "text_removal":
                    # 文字擦除
                    ocr_result = await ocr_service.detect_text(image)
                    if ocr_result["success"] and ocr_result["text_regions"]:
                        mask = await ocr_service._generate_mask(
                            image, ocr_result["text_regions"], padding=5
                        )
                        result = await zimage_service.inpaint(
                            image, mask, "Clean background, no text, professional product photography"
                        )
                    else:
                        # 无文字，直接返回原图
                        result = {"success": True, "images": [{"data": self._encode_image(image)}]}

                elif operation == "background_replacement":
                    # 背景重绘
                    seg_result = await sam_service.segment_subject(image)
                    if seg_result["success"]:
                        mask = self._decode_mask(seg_result["mask"])
                        # 生成新背景
                        from app.services.zimage_service import zimage_service
                        background = await zimage_service.generate_background(
                            zimage_service.STYLE_PROMPTS.get(style_id, zimage_service.STYLE_PROMPTS["minimal_white"]),
                            width=image.width,
                            height=image.height,
                        )
                        # 合成
                        output = self._composite_image(image, background, mask)
                        result = {"success": True, "images": [{"data": self._encode_image(output)}]}
                    else:
                        result = {"success": False, "error": "分割失败"}

                else:
                    result = {"success": False, "error": f"不支持的操作: {operation}"}

                if result["success"]:
                    output_urls.extend(result.get("images", []))

            return {
                "success": len(output_urls) > 0,
                "output": output_urls,
                "processing_time": time.time() - start_time,
            }

        except Exception as e:
            logger.error(f"单张图片处理失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        async with self._task_lock:
            task = self.tasks.get(task_id)
            if not task:
                return None

            return {
                "task_id": task_id,
                "status": task["status"],
                "total_images": task["total_images"],
                "processed_images": task["processed_images"],
                "success_count": task["success_count"],
                "failed_count": task["failed_count"],
                "progress": task["progress"],
                "created_at": task["created_at"],
                "completed_at": task.get("completed_at"),
            }

    async def get_task_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        async with self._task_lock:
            task = self.tasks.get(task_id)
            if not task:
                return None

            return {
                "task_id": task_id,
                "status": task["status"],
                "results": task["results"],
                "errors": task["errors"],
                "success_count": task["success_count"],
                "failed_count": task["failed_count"],
            }

    async def cancel_task(self, task_id: str, user_id: int) -> bool:
        """取消任务"""
        async with self._task_lock:
            task = self.tasks.get(task_id)
            if not task or task["user_id"] != user_id:
                return False

            if task["status"] in [self.STATUS_COMPLETED, self.STATUS_FAILED]:
                return False

            task["status"] = self.STATUS_CANCELLED
            task["completed_at"] = datetime.now().isoformat()
            return True

    async def generate_download_package(self, task_id: str) -> Optional[str]:
        """生成下载ZIP包

        Returns:
            ZIP文件的base64编码或None
        """
        task = await self.get_task_results(task_id)
        if not task or task["status"] != self.STATUS_COMPLETED:
            return None

        try:
            buffer = io.BytesIO()

            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for result in task["results"]:
                    if result["success"] and result.get("output"):
                        for i, output in enumerate(result["output"]):
                            filename = f"{result['filename']}_{i}.jpg"
                            zipf.writestr(filename, base64.b64decode(output["data"].split(",")[1]))

            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode()

        except Exception as e:
            logger.error(f"生成下载包失败: {e}")
            return None

    async def _update_task(self, task_id: str) -> None:
        """更新任务到Redis或数据库"""
        # TODO: 实现持久化存储
        pass

    def _estimate_time(
        self, image_count: int, operations: List[str]
    ) -> int:
        """估算处理时间（秒）"""
        base_time_per_image = 10  # 基础时间
        operation_multiplier = len(operations)

        return int(image_count * base_time_per_image * operation_multiplier * 0.8)

    def _decode_image(self, image_data: str) -> Image.Image:
        """解码base64图片"""
        if image_data.startswith("data:image"):
            image_data = image_data.split(",")[1]

        img_bytes = base64.b64decode(image_data)
        return Image.open(io.BytesIO(img_bytes))

    def _encode_image(self, image: Image.Image) -> str:
        """编码图片为base64"""
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        return f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    def _decode_mask(self, mask_data: str) -> Image.Image:
        """解码掩码"""
        mask_bytes = base64.b64decode(mask_data)
        return Image.open(io.BytesIO(mask_bytes)).convert("L")

    def _composite_image(
        self, foreground: Image.Image, background: Image.Image, mask: Image.Image
    ) -> Image.Image:
        """合成图像"""
        # 调整背景大小
        background = background.resize(foreground.size)

        # 转换掩码为RGBA
        mask = mask.convert("L")
        mask = mask.resize(foreground.size)

        # 创建合成图像
        # 使用掩码将前景合成到背景上
        result = background.copy()

        # 确保前景和背景模式一致
        foreground_rgba = foreground.copy()
        foreground_rgba.putalpha(mask)

        result.paste(foreground_rgba, (0, 0), foreground_rgba)

        return result

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "active_tasks": sum(
                1 for t in self.tasks.values() if t["status"] == self.STATUS_PROCESSING
            ),
            "total_tasks": len(self.tasks),
            "supported_operations": ["text_removal", "background_replacement"],
            "supported_styles": list(
                __import__("app.services.zimage_service", fromlist=["zimage_service"])
                .zimage_service.STYLE_PROMPTS.keys()
            ),
        }


# 全局服务实例
batch_processor = BatchProcessor()
