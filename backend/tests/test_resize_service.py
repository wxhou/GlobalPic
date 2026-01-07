"""
单元测试 - 尺寸适配服务模块
"""
import pytest
from PIL import Image
from io import BytesIO
import base64

from app.services.resize_service import ResizeService, PlatformPreset


class TestResizeService:
    """测试尺寸适配服务"""

    def test_service_initialization(self):
        """测试服务初始化"""
        service = ResizeService()
        assert service.is_initialized is True

    def test_platform_presets_exist(self):
        """测试平台预设存在"""
        service = ResizeService()
        presets = service.get_presets()
        assert len(presets) > 0

    def test_amazon_preset(self):
        """测试亚马逊预设"""
        service = ResizeService()
        presets = service.get_presets()
        amazon_presets = [p for p in presets if "amazon" in p["id"]]
        assert len(amazon_presets) > 0
        # 亚马逊主图应该是 1000x1000
        main_preset = next((p for p in amazon_presets if p["id"] == "amazon_primary"), None)
        assert main_preset is not None
        assert main_preset["width"] == 1000
        assert main_preset["height"] == 1000

    def test_get_categories(self):
        """测试获取分类"""
        service = ResizeService()
        categories = service.get_categories()
        assert len(categories) > 0
        # 应该有电商平台、社交媒体等分类
        category_ids = [c["id"] for c in categories]
        assert "电商平台" in category_ids
        assert "社交媒体" in category_ids

    def test_aspect_ratios(self):
        """测试宽高比配置"""
        service = ResizeService()
        assert "1:1" in service.ASPECT_RATIOS
        assert "16:9" in service.ASPECT_RATIOS
        assert "9:16" in service.ASPECT_RATIOS

    def test_resample_methods(self):
        """测试重采样方法"""
        service = ResizeService()
        assert "lanczos" in service.RESAMPLE_METHODS
        assert "bilinear" in service.RESAMPLE_METHODS
        assert "bicubic" in service.RESAMPLE_METHODS
        assert "nearest" in service.RESAMPLE_METHODS


class TestResizeImage:
    """测试图像尺寸调整"""

    def test_resize_basic(self):
        """测试基本尺寸调整"""
        service = ResizeService()
        # 创建测试图像
        img = Image.new("RGB", (800, 600), color="red")

        # 调整到 400x300
        result = service.resize_image(img, 400, 300, maintain_aspect_ratio=False)

        assert result.size == (400, 300)

    def test_resize_maintain_aspect_ratio_contain(self):
        """测试保持宽高比 - contain模式"""
        service = ResizeService()
        # 创建 800x600 图像
        img = Image.new("RGB", (800, 600), color="blue")

        # 调整到 400x400，保持比例（会有边框）
        result = service.resize_image(img, 400, 400, maintain_aspect_ratio=True, fit_mode="contain")

        assert result.size == (400, 400)

    def test_resize_maintain_aspect_ratio_cover(self):
        """测试保持宽高比 - cover模式"""
        service = ResizeService()
        # 创建 800x600 图像
        img = Image.new("RGB", (800, 600), color="green")

        # 调整到 400x400，保持比例（会裁剪）
        result = service.resize_image(img, 400, 400, maintain_aspect_ratio=True, fit_mode="cover")

        assert result.size == (400, 400)

    def test_resize_lanczos_resample(self):
        """测试Lanczos重采样"""
        service = ResizeService()
        img = Image.new("RGB", (200, 200), color="yellow")

        result = service.resize_image(img, 100, 100, resample_method="lanczos")

        assert result.size == (100, 100)

    def test_resize_background_color(self):
        """测试背景颜色"""
        service = ResizeService()
        img = Image.new("RGB", (100, 100), color="red")

        # contain模式应该添加背景
        result = service.resize_image(img, 200, 200, maintain_aspect_ratio=True, fit_mode="contain", background_color="#000000")

        assert result.size == (200, 200)


class TestCropToRatio:
    """测试按比例裁剪"""

    def test_crop_16_9_from_wide(self):
        """测试从宽图像裁剪16:9"""
        service = ResizeService()
        # 创建宽图像 1600x900
        img = Image.new("RGB", (1600, 900), color="purple")

        result = service.crop_to_ratio(img, "16:9", position="center")

        assert result.size == (1600, 900)  # 已经是16:9

    def test_crop_1_1_from_rect(self):
        """测试从矩形裁剪正方形"""
        service = ResizeService()
        # 创建 800x600 图像
        img = Image.new("RGB", (800, 600), color="orange")

        result = service.crop_to_ratio(img, "1:1", position="center")

        assert result.size == (600, 600)  # 裁剪成正方形


class TestSmartResize:
    """测试智能调整尺寸"""

    def test_smart_resize_downscale(self):
        """测试缩小图像"""
        service = ResizeService()
        # 创建大图像
        img = Image.new("RGB", (4096, 4096), color="cyan")

        result = service.smart_resize(img, max_width=1024, max_height=1024)

        assert result.size == (1024, 1024)

    def test_smart_resize_no_change(self):
        """测试小图像不调整"""
        service = ResizeService()
        # 创建小图像
        img = Image.new("RGB", (500, 500), color="magenta")

        # 最大尺寸大于图像尺寸
        result = service.smart_resize(img, max_width=2048, max_height=2048)

        # 应该返回原图像的副本
        assert result.size == (500, 500)


class TestGetStatus:
    """测试服务状态"""

    def test_get_status(self):
        """测试获取服务状态"""
        service = ResizeService()
        status = service.get_status()

        assert status["initialized"] is True
        assert status["preset_count"] > 0
        assert "resample_methods" in status


class TestResizeWithRealImage:
    """使用真实图像数据测试"""

    def test_image_from_base64(self):
        """测试从base64创建图像"""
        service = ResizeService()
        # 创建测试图像并转为base64
        original = Image.new("RGB", (100, 100), color="white")
        buffer = BytesIO()
        original.save(buffer, format="JPEG")
        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # 从base64解码
        img_data = base64.b64decode(base64_str)
        loaded_img = Image.open(BytesIO(img_data))

        # 调整尺寸
        result = service.resize_image(loaded_img, 50, 50)

        assert result.size == (50, 50)


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
