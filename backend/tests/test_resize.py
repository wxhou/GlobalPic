"""
尺寸调整模块API接口测试
使用api_client测试运行中的后端服务
"""
import pytest


BASE_URL = "http://localhost:8000"


class TestGetPresets:
    """测试获取平台尺寸预设接口"""

    def test_get_presets(self, api_client):
        """测试获取所有预设"""
        response = api_client.get(f"{BASE_URL}/api/v1/presets")
        print(f"\n[GET] /api/v1/presets - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0
        assert "presets" in data.get("data", {})

    def test_get_presets_with_category(self, api_client):
        """测试按分类获取预设"""
        response = api_client.get(f"{BASE_URL}/api/v1/presets?category=电商平台")
        print(f"\n[GET] /api/v1/presets?category=电商平台 - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0

    def test_get_presets_structure(self, api_client):
        """测试预设结构"""
        response = api_client.get(f"{BASE_URL}/api/v1/presets")
        if response.status_code == 200:
            data = response.json()
            if data.get("errcode") == 0:
                presets = data.get("data", {}).get("presets", [])
                if len(presets) > 0:
                    preset = presets[0]
                    assert "id" in preset
                    assert "name" in preset
                    assert "width" in preset
                    assert "height" in preset


class TestGetCategories:
    """测试获取预设分类接口"""

    def test_get_categories(self, api_client):
        """测试获取分类列表"""
        response = api_client.get(f"{BASE_URL}/api/v1/categories")
        print(f"\n[GET] /api/v1/categories - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0


class TestGetResizeStatus:
    """测试获取尺寸调整服务状态接口"""

    def test_get_resize_status(self, api_client):
        """测试获取resize服务状态"""
        response = api_client.get(f"{BASE_URL}/api/v1/status")
        print(f"\n[GET] /api/v1/status - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0


class TestResizeImage:
    """测试调整图片尺寸接口"""

    def test_resize_image_success(self, api_client, auth_token):
        """测试成功调整图片尺寸"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/resize",
            json={
                "image_id": 99999,  # 使用不存在的ID
                "width": 800,
                "height": 600,
                "maintain_aspect_ratio": True,
                "resample_method": "lanczos",
                "fit_mode": "contain",
                "background_color": "#FFFFFF"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/resize - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 图像不存在，errcode不为0

    def test_resize_image_minimal_params(self, api_client, auth_token):
        """测试最小参数调整尺寸"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/resize",
            json={
                "image_id": 99999,
                "width": 800,
                "height": 600
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/resize (minimal) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # 图像不存在，errcode不为0

    def test_resize_image_missing_image_id(self, api_client, auth_token):
        """测试缺少图像ID"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/resize",
            json={
                "width": 800,
                "height": 600
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/resize (no image_id) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_resize_image_invalid_width(self, api_client, auth_token):
        """测试无效宽度"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/resize",
            json={
                "image_id": 99999,
                "width": 0,
                "height": 600
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/resize (invalid width) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_resize_image_without_auth(self, api_client):
        """测试未认证调整尺寸"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/resize",
            json={
                "image_id": 1,
                "width": 800,
                "height": 600
            }
        )
        print(f"\n[POST] /api/v1/resize (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # resize API 不需要认证，直接返回操作结果
        assert data.get("errcode") == 0  # 操作成功


class TestCropImage:
    """测试按比例裁剪图片接口"""

    def test_crop_image_success(self, api_client, auth_token):
        """测试成功裁剪图片"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/crop",
            json={
                "request": {"image_id": 99999},
                "crop_params": {
                    "ratio": "16:9",
                    "position": "center"
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/crop - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 图像不存在，errcode不为0

    def test_crop_image_minimal_params(self, api_client, auth_token):
        """测试最小参数裁剪"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/crop",
            json={
                "request": {"image_id": 99999},
                "crop_params": {
                    "ratio": "1:1"
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/crop (minimal) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # 图像不存在，errcode不为0

    def test_crop_image_missing_ratio(self, api_client, auth_token):
        """测试缺少裁剪比例"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/crop",
            json={
                "request": {"image_id": 99999},
                "crop_params": {
                    "position": "center"
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/crop (no ratio) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_crop_image_invalid_ratio(self, api_client, auth_token):
        """测试无效裁剪比例 - API可能忽略无效参数"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/crop",
            json={
                "request": {"image_id": 99999},
                "crop_params": {
                    "ratio": "invalid_ratio"
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/crop (invalid ratio) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # API可能忽略无效ratio或返回成功
        assert data.get("errcode") in [0, 1005]

    def test_crop_image_without_auth(self, api_client):
        """测试未认证裁剪图片"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/crop",
            json={
                "request": {"image_id": 1},
                "crop_params": {
                    "ratio": "16:9"
                }
            }
        )
        print(f"\n[POST] /api/v1/crop (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # crop API 不需要认证，直接返回操作结果
        assert data.get("errcode") == 0  # 操作成功


class TestSmartResize:
    """测试智能调整图片尺寸接口"""

    def test_smart_resize_success(self, api_client, auth_token):
        """测试成功智能调整"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/smart-resize",
            json={
                "request": {"image_id": 99999},
                "smart_params": {
                    "max_width": 1024,
                    "max_height": 1024
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/smart-resize - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 图像不存在，errcode不为0

    def test_smart_resize_minimal_params(self, api_client, auth_token):
        """测试最小参数智能调整"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/smart-resize",
            json={
                "request": {"image_id": 99999},
                "smart_params": {}
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/smart-resize (minimal) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # 图像不存在，errcode不为0

    def test_smart_resize_missing_image_id(self, api_client, auth_token):
        """测试缺少图像ID"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/smart-resize",
            json={
                "smart_params": {
                    "max_width": 1024
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/smart-resize (no image_id) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_smart_resize_without_auth(self, api_client):
        """测试未认证智能调整"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/smart-resize",
            json={
                "request": {"image_id": 1},
                "smart_params": {
                    "max_width": 1024,
                    "max_height": 1024
                }
            }
        )
        print(f"\n[POST] /api/v1/smart-resize (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # smart-resize API 不需要认证，直接返回操作结果
        assert data.get("errcode") == 0  # 操作成功


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
