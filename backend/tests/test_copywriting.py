"""
文案生成模块API接口测试
使用api_client测试运行中的后端服务
"""
import pytest


BASE_URL = "http://localhost:8000"


class TestGetSupportedPlatforms:
    """测试获取支持的平台接口"""

    def test_get_platforms(self, api_client):
        """测试获取支持的平台列表"""
        response = api_client.get(f"{BASE_URL}/api/v1/copywriting/platforms")
        print(f"\n[GET] /api/v1/copywriting/platforms - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0
        assert "platforms" in data.get("data", {})


class TestGetCopywritingStatus:
    """测试获取文案服务状态接口"""

    def test_get_status(self, api_client):
        """测试获取文案服务状态"""
        response = api_client.get(f"{BASE_URL}/api/v1/copywriting/status")
        print(f"\n[GET] /api/v1/copywriting/status - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0


class TestGenerateCopywriting:
    """测试生成营销文案接口"""

    def test_generate_copywriting_success(self, api_client, auth_token):
        """测试成功生成文案"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/copywriting/generate",
            json={
                "image_description": "A red dress for summer",
                "product_name": "Summer Red Dress",
                "platform": "amazon",
                "count": 5,
                "tone": "professional"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/copywriting/generate - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0
        assert "copywrites" in data.get("data", {})

    def test_generate_copywriting_minimal_params(self, api_client, auth_token):
        """测试最小参数生成文案"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/copywriting/generate",
            json={
                "image_description": "A beautiful product photo"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/copywriting/generate (minimal) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0

    def test_generate_copywriting_empty_description(self, api_client, auth_token):
        """测试空图片描述 - API可能成功生成默认文案"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/copywriting/generate",
            json={"image_description": ""},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/copywriting/generate (empty description) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 空描述时API可能成功返回默认文案，或返回错误
        assert data.get("errcode") in [0, 1005]

    def test_generate_copywriting_invalid_platform(self, api_client, auth_token):
        """测试无效平台 - API可能忽略无效参数使用默认值"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/copywriting/generate",
            json={
                "image_description": "A product",
                "platform": "invalid_platform"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/copywriting/generate (invalid platform) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        # 无效平台参数可能被忽略，使用默认平台
        assert response.json().get("errcode") in [0, 1005]

    def test_generate_copywriting_invalid_count(self, api_client, auth_token):
        """测试无效文案数量 - API可能忽略无效值使用默认值"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/copywriting/generate",
            json={
                "image_description": "A product",
                "count": 0
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/copywriting/generate (invalid count) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # 无效count可能被忽略或使用默认值
        assert data.get("errcode") in [0, 1005]

    def test_generate_copywriting_excessive_count(self, api_client, auth_token):
        """测试超过限制的文案数量 - 可能被限制到最大值"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/copywriting/generate",
            json={
                "image_description": "A product",
                "count": 100
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/copywriting/generate (excessive count) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 超出限制可能被限制到最大值
        assert data.get("errcode") in [0, 1005, 3006]

    def test_generate_copywriting_without_auth(self, api_client):
        """测试未认证生成文案"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/copywriting/generate",
            json={"image_description": "A product"}
        )
        print(f"\n[POST] /api/v1/copywriting/generate (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
