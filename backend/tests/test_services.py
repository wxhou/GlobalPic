"""
单元测试 - AI服务模块
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from PIL import Image
import io
import base64


class TestZImageService:
    """测试Z-Image-Turbo服务"""

    def test_service_initialization(self):
        """测试服务初始化"""
        from app.services.zimage_service import ZImageService

        service = ZImageService()
        assert service.is_initialized is False
        assert service.device == "cpu"

    def test_style_prompts_exist(self):
        """测试风格提示词存在"""
        from app.services.zimage_service import ZImageService

        service = ZImageService()
        assert len(service.STYLE_PROMPTS) > 0
        assert "minimal_white" in service.STYLE_PROMPTS
        assert "amazon_standard" in service.STYLE_PROMPTS

    def test_build_prompt(self):
        """测试提示词构建"""
        from app.services.zimage_service import ZImageService

        service = ZImageService()
        prompt = service._build_prompt("product photo", "minimal_white", 0.8)
        assert "product photo" in prompt
        assert "clean white background" in prompt.lower()


class TestSAMService:
    """测试SAM分割服务"""

    def test_service_initialization(self):
        """测试服务初始化"""
        from app.services.sam_service import SAMService

        service = SAMService()
        assert service.is_initialized is False

    def test_image_conversion(self):
        """测试图像转换"""
        from app.services.sam_service import SAMService

        service = SAMService()
        # 创建测试图像
        img = Image.new("RGB", (100, 100), color="red")
        np_array = service._image_to_np(img)
        assert np_array.shape == (100, 100, 3)


class TestOCRService:
    """测试OCR服务"""

    def test_service_initialization(self):
        """测试服务初始化"""
        from app.services.ocr_service import OCRService

        service = OCRService()
        assert service.is_initialized is False
        assert "en" in service.supported_langs
        assert "zh" in service.supported_langs

    def test_language_detection(self):
        """测试语言检测"""
        from app.services.ocr_service import OCRService

        service = OCRService()
        assert service._detect_language("Hello World") == "en"
        assert service._detect_language("你好世界") == "zh"


class TestCopywritingService:
    """测试文案生成服务"""

    def test_service_initialization(self):
        """测试服务初始化"""
        from app.services.copywriting_service import CopywritingService

        service = CopywritingService()
        assert service.is_initialized is False

    def test_templates_exist(self):
        """测试模板存在"""
        from app.services.copywriting_service import CopywritingService

        service = CopywritingService()
        assert "amazon" in service.TEMPLATES
        assert "tiktok" in service.TEMPLATES

    def test_mock_generation(self):
        """测试模拟生成"""
        from app.services.copywriting_service import CopywritingService

        service = CopywritingService()
        result = asyncio.run(service._generate_mock(
            "A red dress",
            "amazon",
            3
        ))
        assert result["success"] is True
        assert len(result["copywrites"]) == 3
        assert "mock" in result


class TestBatchProcessor:
    """测试批量处理服务"""

    def test_service_initialization(self):
        """测试服务初始化"""
        from app.services.batch_processor import BatchProcessor

        processor = BatchProcessor()
        assert processor.STATUS_PENDING == "pending"
        assert processor.STATUS_PROCESSING == "processing"
        assert processor.STATUS_COMPLETED == "completed"

    def test_estimate_time(self):
        """测试时间估算"""
        from app.services.batch_processor import BatchProcessor

        processor = BatchProcessor()
        time = processor._estimate_time(10, ["text_removal"])
        assert time > 0

    def test_status(self):
        """测试状态获取"""
        from app.services.batch_processor import BatchProcessor

        processor = BatchProcessor()
        status = processor.get_status()
        assert "active_tasks" in status
        assert "total_tasks" in status


class TestPaymentService:
    """测试支付服务"""

    def test_service_initialization(self):
        """测试服务初始化"""
        from app.services.payment_service import PaymentService

        service = PaymentService()
        assert service.is_initialized is False

    def test_plans_exist(self):
        """测试套餐存在"""
        from app.services.payment_service import PaymentService

        service = PaymentService()
        assert "free" in service.PLANS
        assert "personal" in service.PLANS
        assert "enterprise" in service.PLANS

    def test_credit_packages(self):
        """测试额度包"""
        from app.services.payment_service import PaymentService

        service = PaymentService()
        assert len(service.CREDIT_PACKAGES) > 0


class TestAPIKeyService:
    """测试API密钥服务"""

    def test_service_initialization(self):
        """测试服务初始化"""
        from app.services.payment_service import APIKeyService

        service = APIKeyService()
        assert service.is_initialized is True


class TestAIProcessor:
    """测试AI处理器"""

    def test_processor_initialization(self):
        """测试处理器初始化"""
        from app.services.ai_processor import AIImageProcessor

        processor = AIImageProcessor()
        assert processor.models_loaded is False

    def test_load_image(self):
        """测试图像加载"""
        from app.services.ai_processor import AIImageProcessor

        processor = AIImageProcessor()
        # 测试不存在的文件
        result = processor._load_image("/nonexistent/path.jpg")
        assert result is None


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
