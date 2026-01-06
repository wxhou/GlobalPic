"""
OCR文字检测服务
使用EasyOCR实现中英文文字检测
"""
import asyncio
import base64
import io
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class OCRService:
    """OCR文字检测服务"""

    def __init__(self):
        self.reader = None
        self.is_initialized = False
        self._model_lock = asyncio.Lock()

        # 支持的语言
        self.supported_langs = ["en", "zh"]

    async def initialize(self) -> bool:
        """初始化OCR模型"""
        if self.is_initialized:
            return True

        async with self._model_lock:
            if self.is_initialized:
                return True

            try:
                import easyocr

                logger.info("开始加载EasyOCR模型...")
                start_time = time.time()

                # 加载中英文模型
                self.reader = easyocr.Reader(
                    self.supported_langs,
                    gpu=self._detect_gpu(),
                    verbose=False,
                )

                load_time = time.time() - start_time
                logger.info(f"EasyOCR模型加载完成，耗时: {load_time:.2f}秒")

                self.is_initialized = True
                return True

            except Exception as e:
                logger.error(f"EasyOCR模型加载失败: {e}")
                self.is_initialized = False
                return False

    def _detect_gpu(self) -> bool:
        """检测是否使用GPU"""
        try:
            import torch

            if torch.cuda.is_available():
                return True
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return True
            else:
                return False
        except:
            return False

    def _image_to_np(self, image: Image.Image) -> np.ndarray:
        """将PIL图像转换为numpy数组"""
        return np.array(image.convert("RGB"))

    async def detect_text(
        self,
        image: Image.Image,
        min_confidence: float = 0.3,
    ) -> Dict[str, Any]:
        """检测图像中的文字

        Args:
            image: 输入图像
            min_confidence: 最小置信度

        Returns:
            包含检测结果的字典
        """
        if not self.is_initialized:
            raise RuntimeError("OCR模型未初始化")

        start_time = time.time()

        try:
            image_np = self._image_to_np(image)

            # 检测文字
            results = await asyncio.to_thread(
                self.reader.readtext,
                image_np,
                detail=1,
                paragraph=False,
            )

            processing_time = time.time() - start_time
            logger.info(f"OCR检测完成，耗时: {processing_time:.2f}秒，检出{len(results)}个文字区域")

            # 解析结果
            text_regions = []
            for bbox, text, confidence in results:
                if confidence >= min_confidence:
                    # 转换边界框格式
                    x1, y1 = bbox[0]
                    x2, y2 = bbox[2]

                    # 检测语言
                    lang = self._detect_language(text)

                    text_regions.append({
                        "text": text,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "confidence": float(confidence),
                        "language": lang,
                    })

            # 按位置排序（从左到右，从上到下）
            text_regions = self._sort_regions(text_regions)

            # 计算整体置信度
            avg_confidence = (
                sum(r["confidence"] for r in text_regions) / len(text_regions)
                if text_regions
                else 0.0
            )

            return {
                "success": True,
                "text_regions": text_regions,
                "total_regions": len(text_regions),
                "average_confidence": avg_confidence,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"OCR检测失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
            }

    async def detect_text_for_inpainting(
        self,
        image: Image.Image,
        padding: int = 5,
    ) -> Dict[str, Any]:
        """检测文字并生成修复掩码

        Args:
            image: 输入图像
            padding: 掩码边缘padding

        Returns:
            包含文字区域和修复掩码的字典
        """
        # 检测文字
        result = await self.detect_text(image)

        if not result["success"]:
            return result

        # 生成掩码
        mask = await self._generate_mask(image, result["text_regions"], padding)

        # 转换掩码为base64
        buffer = io.BytesIO()
        mask.save(buffer, format="PNG")
        mask_str = base64.b64encode(buffer.getvalue()).decode()

        return {
            "success": True,
            "text_regions": result["text_regions"],
            "mask": mask_str,
            "total_regions": result["total_regions"],
            "processing_time": result["processing_time"],
        }

    async def _generate_mask(
        self,
        image: Image.Image,
        text_regions: List[Dict[str, Any]],
        padding: int = 5,
    ) -> Image.Image:
        """生成文字掩码

        Args:
            image: 原始图像
            text_regions: 文字区域列表
            padding: 边缘padding

        Returns:
            文字掩码图像
        """
        width, height = image.size
        mask = Image.new("L", (width, height), 0)

        from PIL import ImageDraw

        draw = ImageDraw.Draw(mask)

        for region in text_regions:
            bbox = region["bbox"]
            x1, y1, x2, y2 = bbox

            # 添加padding
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(width, x2 + padding)
            y2 = min(height, y2 + padding)

            # 绘制掩码区域
            draw.rectangle([x1, y1, x2, y2], fill=255)

        return mask

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 简单的语言检测
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")

        if chinese_chars > 0:
            return "zh"
        else:
            return "en"

    def _sort_regions(
        self, regions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """对文字区域进行排序（从左到右，从上到下）"""

        def sort_key(region):
            bbox = region["bbox"]
            x1, y1 = bbox[0], bbox[1]
            # 按行排序，容差50像素
            return (int(y1 / 50), x1)

        return sorted(regions, key=sort_key)

    async def extract_text(
        self,
        image: Image.Image,
    ) -> Dict[str, Any]:
        """提取图像中的所有文字

        Args:
            image: 输入图像

        Returns:
            包含提取文字的字典
        """
        if not self.is_initialized:
            raise RuntimeError("OCR模型未初始化")

        start_time = time.time()

        try:
            image_np = self._image_to_np(image)

            # 检测文字
            results = await asyncio.to_thread(
                self.reader.readtext,
                image_np,
                detail=0,  # 只返回文字
                paragraph=True,
            )

            processing_time = time.time() - start_time

            # 合并所有文字
            all_text = "\n".join(results)

            # 统计信息
            total_chars = len(all_text.replace("\n", ""))
            chinese_chars = sum(
                1 for c in all_text if "\u4e00" <= c <= "\u9fff"
            )

            return {
                "success": True,
                "text": all_text,
                "lines": results,
                "total_chars": total_chars,
                "chinese_chars": chinese_chars,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"文字提取失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
            }

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "is_initialized": self.is_initialized,
            "supported_languages": self.supported_langs,
            "gpu_enabled": self._detect_gpu(),
        }


# 全局服务实例
ocr_service = OCRService()
