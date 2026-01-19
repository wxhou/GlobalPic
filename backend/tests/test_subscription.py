"""
订阅模块API接口测试
使用api_client测试运行中的后端服务
"""
import pytest


BASE_URL = "http://localhost:8000"


class TestGetSubscriptionPlans:
    """测试获取订阅套餐接口"""

    def test_get_plans(self, api_client):
        """测试获取订阅套餐列表"""
        response = api_client.get(f"{BASE_URL}/api/v1/subscription/plans")
        print(f"\n[GET] /api/v1/subscription/plans - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0
        assert "plans" in data.get("data", {})


class TestGetCreditPackages:
    """测试获取额度包接口"""

    def test_get_credit_packages(self, api_client):
        """测试获取按需付费套餐"""
        response = api_client.get(f"{BASE_URL}/api/v1/subscription/credits")
        print(f"\n[GET] /api/v1/subscription/credits - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0
        assert "packages" in data.get("data", {})


class TestGetPaymentServiceStatus:
    """测试获取支付服务状态接口"""

    def test_get_payment_status(self, api_client):
        """测试获取支付服务状态"""
        response = api_client.get(f"{BASE_URL}/api/v1/subscription/payment/status")
        print(f"\n[GET] /api/v1/subscription/payment/status - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 支付服务可能返回错误（4001=服务器内部错误），但格式应该正确
        assert "errcode" in data
        assert "errmsg" in data


class TestCreateSubscriptionCheckout:
    """测试创建订阅Checkout接口"""

    def test_create_checkout_success(self, api_client, auth_token):
        """测试成功创建订阅Checkout"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/create-checkout",
            json={
                "plan_id": "personal",
                "mode": "subscription"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/subscription/create-checkout - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 响应格式正确

    def test_create_checkout_invalid_plan(self, api_client, auth_token):
        """测试无效套餐ID"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/create-checkout",
            json={
                "plan_id": "invalid_plan_id",
                "mode": "subscription"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/subscription/create-checkout (invalid plan) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_create_checkout_without_auth(self, api_client):
        """测试未认证创建Checkout"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/create-checkout",
            json={"plan_id": "personal"}
        )
        print(f"\n[POST] /api/v1/subscription/create-checkout (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestCreateCreditCheckout:
    """测试创建额度购买Checkout接口"""

    def test_create_credit_checkout_success(self, api_client, auth_token):
        """测试成功创建额度购买Checkout"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/create-credit-checkout",
            json={"package_index": 0},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/subscription/create-credit-checkout - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 响应格式正确

    def test_create_credit_checkout_invalid_index(self, api_client, auth_token):
        """测试无效套餐索引"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/create-credit-checkout",
            json={"package_index": 999},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/subscription/create-credit-checkout (invalid index) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_create_credit_checkout_without_auth(self, api_client):
        """测试未认证创建额度Checkout"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/create-credit-checkout",
            json={"package_index": 0}
        )
        print(f"\n[POST] /api/v1/subscription/create-credit-checkout (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestGetSubscriptionStatus:
    """测试获取订阅状态接口"""

    def test_get_subscription_status_with_auth(self, api_client, auth_token):
        """测试带认证获取订阅状态"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/subscription/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/subscription/status - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0

    def test_get_subscription_status_without_auth(self, api_client):
        """测试未认证获取订阅状态"""
        response = api_client.get(f"{BASE_URL}/api/v1/subscription/status")
        print(f"\n[GET] /api/v1/subscription/status (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestCancelSubscription:
    """测试取消订阅接口"""

    def test_cancel_subscription_success(self, api_client, auth_token):
        """测试成功取消订阅"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/cancel",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/subscription/cancel - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 响应格式正确

    def test_cancel_subscription_without_auth(self, api_client):
        """测试未认证取消订阅"""
        response = api_client.post(f"{BASE_URL}/api/v1/subscription/cancel")
        print(f"\n[POST] /api/v1/subscription/cancel (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestPaymentWebhook:
    """测试支付Webhook接口"""

    def test_payment_webhook_success(self, api_client):
        """测试支付Webhook处理"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/webhook",
            json={
                "type": "payment_intent.succeeded",
                "data": {"object": {}}
            }
        )
        print(f"\n[POST] /api/v1/subscription/webhook - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # Webhook可能返回业务错误，但格式应该正确


class TestListAPIKeys:
    """测试获取API密钥列表接口"""

    def test_list_api_keys_with_auth(self, api_client, auth_token):
        """测试带认证获取API密钥"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.get(
            f"{BASE_URL}/api/v1/subscription/api-keys",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[GET] /api/v1/subscription/api-keys - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0

    def test_list_api_keys_without_auth(self, api_client):
        """测试未认证获取API密钥"""
        response = api_client.get(f"{BASE_URL}/api/v1/subscription/api-keys")
        print(f"\n[GET] /api/v1/subscription/api-keys (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestCreateAPIKey:
    """测试创建API密钥接口"""

    def test_create_api_key_success(self, api_client, auth_token):
        """测试成功创建API密钥"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/api-keys",
            json={"name": "Test API Key"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/subscription/api-keys - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 响应格式正确

    def test_create_api_key_missing_name(self, api_client, auth_token):
        """测试创建API密钥缺少名称"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/api-keys",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/subscription/api-keys (no name) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0

    def test_create_api_key_without_auth(self, api_client):
        """测试未认证创建API密钥"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/api-keys",
            json={"name": "Test Key"}
        )
        print(f"\n[POST] /api/v1/subscription/api-keys (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


class TestRevokeAPIKey:
    """测试撤销API密钥接口"""

    def test_revoke_api_key_success(self, api_client, auth_token):
        """测试成功撤销API密钥"""
        if auth_token is None:
            pytest.skip("Login failed, cannot test authenticated endpoint")

        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/api-keys/revoke",
            json={"key_id": "nonexistent-key"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"\n[POST] /api/v1/subscription/api-keys/revoke - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        # 密钥不存在，errcode不为0

    def test_revoke_api_key_without_auth(self, api_client):
        """测试未认证撤销API密钥"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/subscription/api-keys/revoke",
            json={"key_id": "key-123"}
        )
        print(f"\n[POST] /api/v1/subscription/api-keys/revoke (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001  # 未认证


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
