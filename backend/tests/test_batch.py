"""
批量处理模块API接口测试
使用api_client测试运行中的后端服务
"""
import pytest
import base64


BASE_URL = "http://localhost:8000"


class TestBatchProcessorStatus:
    """测试批量处理器状态接口"""

    def test_get_processor_status(self, api_client):
        """测试获取批量处理器状态"""
        response = api_client.get(f"{BASE_URL}/api/v1/batch/processor-status")
        print(f"\n[GET] /api/v1/batch/processor-status - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0


class TestCreateBatchTask:
    """测试创建批量任务接口"""

    def test_create_batch_task_minimal(self, api_client, auth_token):
        """测试创建批量任务（最小参数）"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        request_data = {
            "images": [
                {"image": base64.b64encode(b"fake_image_data").decode("utf-8")}
            ]
        }

        response = api_client.post(
            f"{BASE_URL}/api/v1/batch/create",
            json=request_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/batch/create - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 响应格式正确

    def test_create_batch_task_empty_images(self, api_client, auth_token):
        """测试创建空图像列表任务"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        request_data = {
            "images": [],
            "operations": ["text_removal"]
        }

        response = api_client.post(
            f"{BASE_URL}/api/v1/batch/create",
            json=request_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/batch/create (empty images) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_create_batch_task_too_many_images(self, api_client, auth_token):
        """测试创建超过限制的批量任务"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        images = [
            {"image": base64.b64encode(b"fake_image_data").decode("utf-8")}
            for _ in range(51)
        ]

        request_data = {
            "images": images,
            "operations": ["text_removal"]
        }

        response = api_client.post(
            f"{BASE_URL}/api/v1/batch/create",
            json=request_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/batch/create (too many) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_create_batch_task_invalid_operation(self, api_client, auth_token):
        """测试无效操作类型"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        request_data = {
            "images": [
                {"image": base64.b64encode(b"fake_image_data").decode("utf-8")}
            ],
            "operations": ["invalid_operation"]
        }

        response = api_client.post(
            f"{BASE_URL}/api/v1/batch/create",
            json=request_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/batch/create (invalid operation) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_create_batch_task_without_auth(self, api_client):
        """测试未认证创建批量任务"""
        request_data = {
            "images": [
                {"image": base64.b64encode(b"fake_image_data").decode("utf-8")}
            ]
        }

        response = api_client.post(
            f"{BASE_URL}/api/v1/batch/create",
            json=request_data
        )
        print(f"\n[POST] /api/v1/batch/create (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestGetBatchStatus:
    """测试获取批量任务状态接口"""

    def test_get_batch_status_success(self, api_client, auth_token):
        """测试成功获取批量任务状态"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/batch/status?task_id=nonexistent-task",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/batch/status?task_id=nonexistent-task - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 任务不存在，errcode不为0

    def test_get_batch_status_without_auth(self, api_client):
        """测试未认证获取批量任务状态"""
        response = api_client.get(f"{BASE_URL}/api/v1/batch/status?task_id=test-task")
        print(f"\n[GET] /api/v1/batch/status (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestGetBatchResults:
    """测试获取批量任务结果接口"""

    def test_get_batch_results_success(self, api_client, auth_token):
        """测试成功获取批量任务结果"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/batch/results?task_id=nonexistent-task",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/batch/results?task_id=nonexistent-task - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 任务不存在，errcode不为0

    def test_get_batch_results_without_auth(self, api_client):
        """测试未认证获取批量任务结果"""
        response = api_client.get(f"{BASE_URL}/api/v1/batch/results?task_id=test-task")
        print(f"\n[GET] /api/v1/batch/results (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestDownloadBatchResults:
    """测试下载批量任务结果接口"""

    def test_download_batch_results_success(self, api_client, auth_token):
        """测试成功下载批量任务结果"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/batch/download?task_id=nonexistent-task",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/batch/download?task_id=nonexistent-task - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 任务不存在，errcode不为0

    def test_download_batch_results_without_auth(self, api_client):
        """测试未认证下载批量任务结果"""
        response = api_client.get(f"{BASE_URL}/api/v1/batch/download?task_id=test-task")
        print(f"\n[GET] /api/v1/batch/download (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # 任务不存在，返回错误
        assert data.get("errcode") != 0  # 任务不存在


class TestCancelBatchTask:
    """测试取消批量任务接口"""

    def test_cancel_batch_task_success(self, api_client, auth_token):
        """测试成功取消批量任务"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/batch/cancel",
            json={"task_id": "nonexistent-task"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/batch/cancel - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 任务不存在，errcode不为0

    def test_cancel_batch_task_not_found(self, api_client, auth_token):
        """测试取消不存在的任务"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/batch/cancel",
            json={"task_id": "nonexistent-task"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/batch/cancel (not found) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_cancel_batch_task_without_auth(self, api_client):
        """测试未认证取消批量任务"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/batch/cancel",
            json={"task_id": "test-task"}
        )
        print(f"\n[POST] /api/v1/batch/cancel (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
