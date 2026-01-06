"""
SAM (Segment Anything Model) 主体分割服务
实现精确的产品主体分割
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
import numpy as np

logger = logging.getLogger(__name__)


class SAMService:
    """SAM主体分割服务"""

    def __init__(self):
        self.sam = None
        self.predictor = None
        self.device = "cpu"
        self.is_initialized = False
        self._model_lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """初始化SAM模型"""
        if self.is_initialized:
            return True

        async with self._model_lock:
            if self.is_initialized:
                return True

            try:
                import torch
                from segment_anything import sam_model_registry, SamPredictor

                # 设备检测
                self.device = self._detect_device()
                logger.info(f"SAM使用设备: {self.device}")

                # 模型检查点路径
                checkpoint_path = Path("models/sam_vit_h_4b8939.pth")

                if not checkpoint_path.exists():
                    logger.warning(
                        f"SAM模型检查点不存在: {checkpoint_path}，使用模拟模式"
                    )
                    return False

                # 加载模型
                logger.info("开始加载SAM模型...")
                start_time = time.time()

                self.sam = sam_model_registry["vit_h"](
                    checkpoint=str(checkpoint_path)
                )

                # 移动到设备
                if self.device == "cuda":
                    self.sam.to("cuda")
                elif self.device == "mps":
                    self.sam.to("mps")

                # 创建预测器
                self.predictor = SamPredictor(self.sam)

                load_time = time.time() - start_time
                logger.info(f"SAM模型加载完成，耗时: {load_time:.2f}秒")

                self.is_initialized = True
                return True

            except Exception as e:
                logger.error(f"SAM模型加载失败: {e}")
                self.is_initialized = False
                return False

    def _detect_device(self) -> str:
        """检测最优计算设备"""
        import torch

        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _image_to_np(self, image: Image.Image) -> np.ndarray:
        """将PIL图像转换为numpy数组"""
        return np.array(image.convert("RGB"))

    async def segment_subject(
        self,
        image: Image.Image,
        multi_mask: bool = False,
    ) -> Dict[str, Any]:
        """分割图像主体

        Args:
            image: 输入图像
            multi_mask: 是否返回多个掩码

        Returns:
            包含分割结果的字典
        """
        if not self.is_initialized:
            raise RuntimeError("SAM模型未初始化")

        start_time = time.time()

        try:
            image_np = self._image_to_np(image)

            # 设置图像到预测器
            self.predictor.set_image(image_np)

            # 自动分割
            masks, scores, logits = self.predictor.predict(
                multimask_output=multi_mask
            )

            processing_time = time.time() - start_time
            logger.info(f"SAM分割完成，耗时: {processing_time:.2f}秒")

            # 选择最佳掩码
            if multi_mask:
                best_idx = np.argmax(scores)
                best_mask = masks[best_idx]
                best_score = scores[best_idx]
            else:
                best_mask = masks
                best_score = scores

            # 转换为PIL图像
            mask_image = Image.fromarray(
                (best_mask * 255).astype(np.uint8), mode="L"
            )

            # 转换为base64
            buffer = io.BytesIO()
            mask_image.save(buffer, format="PNG")
            mask_str = base64.b64encode(buffer.getvalue()).decode()

            # 计算掩码信息
            mask_info = {
                "area": int(best_mask.sum()),
                "width": int(best_mask.shape[1]),
                "height": int(best_mask.shape[0]),
                "score": float(best_score),
            }

            # 如果需要多个掩码
            all_masks = []
            if multi_mask:
                for i, (mask, score) in enumerate(zip(masks, scores)):
                    mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
                    buf = io.BytesIO()
                    mask_img.save(buf, format="PNG")
                    all_masks.append({
                        "index": i,
                        "mask": base64.b64encode(buf.getvalue()).decode(),
                        "score": float(score),
                        "area": int(mask.sum()),
                    })

            return {
                "success": True,
                "mask": mask_str,
                "mask_info": mask_info,
                "masks": all_masks if multi_mask else None,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"SAM分割失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
            }

    async def segment_with_points(
        self,
        image: Image.Image,
        positive_points: List[Tuple[int, int]],
        negative_points: Optional[List[Tuple[int, int]]] = None,
    ) -> Dict[str, Any]:
        """使用点提示进行分割

        Args:
            image: 输入图像
            positive_points: 正样本点列表 [(x, y), ...]
            negative_points: 负样本点列表 [(x, y), ...]

        Returns:
            包含分割结果的字典
        """
        if not self.is_initialized:
            raise RuntimeError("SAM模型未初始化")

        start_time = time.time()

        try:
            image_np = self._image_to_np(image)
            self.predictor.set_image(image_np)

            # 构建输入点
            input_points = np.array(positive_points)
            input_labels = np.ones(len(positive_points))

            if negative_points:
                neg_points = np.array(negative_points)
                neg_labels = np.zeros(len(negative_points))
                input_points = np.vstack([input_points, neg_points])
                input_labels = np.concatenate([input_labels, neg_labels])

            # 预测
            masks, scores, logits = self.predictor.predict(
                point_coords=input_points,
                point_labels=input_labels,
                multimask_output=False,
            )

            processing_time = time.time() - start_time

            # 选择最佳掩码
            best_mask = masks[0]
            best_score = scores[0]

            # 转换为PIL图像
            mask_image = Image.fromarray(
                (best_mask * 255).astype(np.uint8), mode="L"
            )

            buffer = io.BytesIO()
            mask_image.save(buffer, format="PNG")
            mask_str = base64.b64encode(buffer.getvalue()).decode()

            return {
                "success": True,
                "mask": mask_str,
                "mask_info": {
                    "area": int(best_mask.sum()),
                    "score": float(best_score),
                },
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"SAM点提示分割失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
            }

    async def segment_with_box(
        self,
        image: Image.Image,
        box: Tuple[int, int, int, int],
    ) -> Dict[str, Any]:
        """使用边界框提示进行分割

        Args:
            image: 输入图像
            box: 边界框 [x1, y1, x2, y2]

        Returns:
            包含分割结果的字典
        """
        if not self.is_initialized:
            raise RuntimeError("SAM模型未初始化")

        start_time = time.time()

        try:
            image_np = self._image_to_np(image)
            self.predictor.set_image(image_np)

            # 构建输入框
            input_box = np.array(box)

            # 预测
            masks, scores, logits = self.predictor.predict(
                point_coords=None,
                point_labels=None,
                box=input_box[None, :],
                multimask_output=False,
            )

            processing_time = time.time() - start_time

            # 选择最佳掩码
            best_mask = masks[0]
            best_score = scores[0]

            # 转换为PIL图像
            mask_image = Image.fromarray(
                (best_mask * 255).astype(np.uint8), mode="L"
            )

            buffer = io.BytesIO()
            mask_image.save(buffer, format="PNG")
            mask_str = base64.b64encode(buffer.getvalue()).decode()

            return {
                "success": True,
                "mask": mask_str,
                "mask_info": {
                    "area": int(best_mask.sum()),
                    "score": float(best_score),
                },
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"SAM边界框分割失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
            }

    async def refine_mask(
        self,
        image: Image.Image,
        mask: Image.Image,
    ) -> Image.Image:
        """对掩码进行后处理优化

        Args:
            image: 原始图像
            mask: 原始掩码

        Returns:
            优化后的掩码
        """
        import cv2
        from scipy import ndimage

        mask_np = np.array(mask)

        # 1. 去除小型连通域
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            (mask_np > 127).astype(np.uint8), connectivity=8
        )
        min_area = 100  # 最小面积阈值
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] < min_area:
                mask_np[labels == i] = 0

        # 2. 形态学开运算去噪
        kernel = np.ones((3, 3), np.uint8)
        mask_np = cv2.morphologyEx(mask_np, cv2.MORPH_OPEN, kernel)

        # 3. 形态学闭运算填充空洞
        mask_np = cv2.morphologyEx(mask_np, cv2.MORPH_CLOSE, kernel)

        # 4. 高斯模糊边缘
        mask_np = cv2.GaussianBlur(mask_np, (5, 5), 0)

        # 5. 归一化
        mask_np = (mask_np > 127).astype(np.uint8) * 255

        return Image.fromarray(mask_np, mode="L")

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "is_initialized": self.is_initialized,
            "device": self.device,
            "model_type": "vit_h",
            "checkpoint": "sam_vit_h_4b8939.pth",
            "supported_modes": ["automatic", "points", "box"],
        }


# 全局服务实例
sam_service = SAMService()
