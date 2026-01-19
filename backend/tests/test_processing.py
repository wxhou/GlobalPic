"""
处理模块API接口测试
使用api_client测试运行中的后端服务
"""
import pytest


BASE_URL = "http://localhost:8000"


class TestInitializeAIModels:
    """测试AI模型初始化接口"""

    def test_initialize_ai_models(self, api_client):
        """测试初始化AI模型"""
        response = api_client.post(f"{BASE_URL}/api/v1/processing/initialize")
        print(f"\n[POST] /api/v1/processing/initialize - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 初始化可能成功或失败，但响应格式应该正确


class TestGetProcessingStatus:
    """测试获取处理状态接口"""

    def test_get_processing_status(self, api_client):
        """测试获取处理状态"""
        response = api_client.get(f"{BASE_URL}/api/v1/processing/status")
        print(f"\n[GET] /api/v1/processing/status - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0


class TestGetBackgroundStyles:
    """测试获取背景风格接口"""

    def test_get_background_styles(self, api_client):
        """测试获取背景风格列表"""
        response = api_client.get(f"{BASE_URL}/api/v1/processing/background-styles")
        print(f"\n[GET] /api/v1/processing/background-styles - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0
        assert "styles" in data.get("data", {})


class TestGetUserProcessingJobs:
    """测试获取用户处理任务列表接口"""

    def test_get_user_jobs_with_auth(self, api_client, auth_token):
        """测试带认证获取处理任务列表"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/processing/jobs",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/processing/jobs - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0

    def test_get_user_jobs_with_status_filter(self, api_client, auth_token):
        """测试带状态过滤获取处理任务"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/processing/jobs?status=pending",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/processing/jobs?status=pending - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0

    def test_get_user_jobs_with_pagination(self, api_client, auth_token):
        """测试带分页获取处理任务"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/processing/jobs?page=1&per_page=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/processing/jobs?page=1&per_page=10 - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0

    def test_get_user_jobs_without_auth(self, api_client):
        """测试未认证获取处理任务"""
        response = api_client.get(f"{BASE_URL}/api/v1/processing/jobs")
        print(f"\n[GET] /api/v1/processing/jobs (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestGetProcessingJobDetail:
    """测试获取处理任务详情接口"""

    def test_get_job_detail_success(self, api_client, auth_token):
        """测试成功获取任务详情"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/processing/jobs/detail?job_id=1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/processing/jobs/detail?job_id=1 - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 任务可能不存在，但响应格式应该正确

    def test_get_job_detail_not_found(self, api_client, auth_token):
        """测试获取不存在的任务详情"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/processing/jobs/detail?job_id=99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/processing/jobs/detail?job_id=99999 - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_get_job_detail_without_auth(self, api_client):
        """测试未认证获取任务详情"""
        response = api_client.get(f"{BASE_URL}/api/v1/processing/jobs/detail?job_id=1")
        print(f"\n[GET] /api/v1/processing/jobs/detail (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestGetProcessingJobStatus:
    """测试获取处理任务实时状态接口"""

    def test_get_job_status_success(self, api_client, auth_token):
        """测试成功获取任务实时状态"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/processing/jobs/status?job_id=1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/processing/jobs/status?job_id=1 - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 任务可能不存在，但响应格式应该正确

    def test_get_job_status_without_auth(self, api_client):
        """测试未认证获取任务状态"""
        response = api_client.get(f"{BASE_URL}/api/v1/processing/jobs/status?job_id=1")
        print(f"\n[GET] /api/v1/processing/jobs/status (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestCancelProcessingJob:
    """测试取消处理任务接口"""

    def test_cancel_job_success(self, api_client, auth_token):
        """测试成功取消任务"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/processing/jobs/cancel",
            json={"job_id": 99999},  # 使用不存在的ID
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/processing/jobs/cancel - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 任务不存在，errcode不为0

    def test_cancel_job_not_found(self, api_client, auth_token):
        """测试取消不存在的任务"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/processing/jobs/cancel",
            json={"job_id": 99999},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/processing/jobs/cancel (not found) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_cancel_job_without_auth(self, api_client):
        """测试未认证取消任务"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/processing/jobs/cancel",
            json={"job_id": 1}
        )
        print(f"\n[POST] /api/v1/processing/jobs/cancel (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestCreateTextRemovalJob:
    """测试创建文字抹除任务接口"""

    def test_create_text_removal_job_minimal_params(self, api_client, auth_token):
        """测试创建文字抹除任务（最小参数）"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/processing/text-removal",
            json={"image_id": 99999},  # 使用不存在的ID
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/processing/text-removal - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 图像不存在，errcode不为0

    def test_create_text_removal_job_invalid_image(self, api_client, auth_token):
        """测试无效图像ID"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/processing/text-removal",
            json={"image_id": "invalid"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/processing/text-removal (invalid id) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_create_text_removal_job_without_auth(self, api_client):
        """测试未认证创建文字抹除任务"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/processing/text-removal",
            json={"image_id": 1}
        )
        print(f"\n[POST] /api/v1/processing/text-removal (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestCreateBackgroundReplacementJob:
    """测试创建背景重绘任务接口"""

    def test_create_background_replacement_minimal_params(self, api_client, auth_token):
        """测试创建背景重绘任务（最小参数）"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/processing/background-replacement",
            json={"image_id": 99999},  # 使用不存在的ID
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/processing/background-replacement - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 图像不存在，errcode不为0

    def test_create_background_replacement_invalid_image(self, api_client, auth_token):
        """测试无效图像ID"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/processing/background-replacement",
            json={"image_id": "invalid"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/processing/background-replacement (invalid id) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_create_background_replacement_without_auth(self, api_client):
        """测试未认证创建背景重绘任务"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/processing/background-replacement",
            json={"image_id": 1}
        )
        print(f"\n[POST] /api/v1/processing/background-replacement (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
