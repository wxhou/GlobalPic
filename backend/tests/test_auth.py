"""
认证模块测试用例
使用api_client测试运行中的后端API
"""
import pytest
import uuid
import time

BASE_URL = "http://localhost:8000"


class TestHealthEndpoint:
    """测试健康检查接口"""

    def test_health_check(self, api_client):
        """测试健康检查"""
        response = api_client.get(f"{BASE_URL}/health")
        print(f"\n[GET] /health - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestUserRegistration:
    """测试用户注册"""

    @pytest.fixture
    def unique_email(self):
        """生成唯一邮箱"""
        return f"test_{uuid.uuid4().hex[:8]}@example.com"

    def test_register_success(self, api_client, unique_email):
        """测试成功注册"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "testpassword123",
                "confirm_password": "testpassword123",
                "full_name": "Test User"
            }
        )
        print(f"\n[POST] /api/v1/auth/register - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0
        assert data.get("errmsg") == "操作成功"
        assert data.get("data") is not None
        assert "message" in data.get("data", {})
        assert data.get("data", {}).get("email") == unique_email

    def test_register_missing_email(self, api_client):
        """测试缺少邮箱"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={"password": "test123", "confirm_password": "test123"}
        )
        print(f"\n[POST] /api/v1/auth/register (no email) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"
        validation_errors = data.get("data", {}).get("validation_errors", [])
        assert len(validation_errors) > 0
        assert any("email" in err.get("field", "") for err in validation_errors)

    def test_register_missing_password(self, api_client):
        """测试缺少密码"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={"email": "test@example.com", "confirm_password": "test123"}
        )
        print(f"\n[POST] /api/v1/auth/register (no password) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_register_password_mismatch(self, api_client):
        """测试密码不匹配"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "test123",
                "confirm_password": "test456"
            }
        )
        print(f"\n[POST] /api/v1/auth/register (password mismatch) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_register_invalid_email(self, api_client):
        """测试无效邮箱"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "test123456",
                "confirm_password": "test123456"
            }
        )
        print(f"\n[POST] /api/v1/auth/register (invalid email) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"
        validation_errors = data.get("data", {}).get("validation_errors", [])
        assert any("email" in err.get("field", "") for err in validation_errors)

    def test_register_empty_password(self, api_client):
        """测试空密码"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "",
                "confirm_password": ""
            }
        )
        print(f"\n[POST] /api/v1/auth/register (empty password) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_register_password_too_short(self, api_client):
        """测试密码太短"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "123",
                "confirm_password": "123"
            }
        )
        print(f"\n[POST] /api/v1/auth/register (password too short) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005


class TestUserLogin:
    """测试用户登录"""

    @pytest.fixture
    def test_user(self, api_client):
        """创建测试用户并返回凭据和客户端"""
        email = f"login_test_{uuid.uuid4().hex[:8]}@example.com"
        password = "testpassword123"
        
        # 先注册用户
        api_client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "confirm_password": password
            }
        )
        
        # 等待一下
        time.sleep(0.5)
        
        return {"email": email, "password": password, "api_client": api_client}

    def test_login_success(self, test_user):
        """测试成功登录"""
        response = test_user["api_client"].post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        print(f"\n[POST] /api/v1/auth/login - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0
        assert data.get("errmsg") == "操作成功"
        assert data.get("data", {}).get("access_token") is not None
        assert data.get("data", {}).get("token_type") == "bearer"
        assert data.get("data", {}).get("expires_in") > 0
        assert "user" in data.get("data", {})
        assert "id" in data.get("data", {}).get("user", {})

    def test_login_missing_email(self, api_client):
        """测试缺少邮箱"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"password": "test123"}
        )
        print(f"\n[POST] /api/v1/auth/login (no email) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_login_missing_password(self, api_client):
        """测试缺少密码"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "test@example.com"}
        )
        print(f"\n[POST] /api/v1/auth/login (no password) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_login_invalid_email_format(self, api_client):
        """测试无效邮箱格式"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "invalid-email", "password": "test123"}
        )
        print(f"\n[POST] /api/v1/auth/login (invalid email format) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_login_invalid_credentials(self, api_client):
        """测试无效凭据（用户不存在或密码错误）"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrongpassword"}
        )
        print(f"\n[POST] /api/v1/auth/login (invalid credentials) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 2005
        assert data.get("errmsg") == "用户名或密码错误"

    def test_login_empty_body(self, api_client):
        """测试空请求体"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={}
        )
        print(f"\n[POST] /api/v1/auth/login (empty body) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"
        validation_errors = data.get("data", {}).get("validation_errors", [])
        assert len(validation_errors) == 2  # email and password both required


class TestForgotPassword:
    """测试忘记密码"""

    def test_forgot_password_any_email(self, api_client):
        """测试任意邮箱的密码重置请求（安全考虑，返回成功）"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/forgot-password",
            json={"email": "any@example.com"}
        )
        print(f"\n[POST] /api/v1/auth/forgot-password - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        # 即使邮箱不存在也返回200（安全考虑）
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 0
        assert data.get("errmsg") == "操作成功"
        assert "message" in data.get("data", {})

    def test_forgot_password_missing_email(self, api_client):
        """测试缺少邮箱"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/forgot-password",
            json={}
        )
        print(f"\n[POST] /api/v1/auth/forgot-password (no email) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_forgot_password_invalid_email(self, api_client):
        """测试无效邮箱"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/forgot-password",
            json={"email": "invalid-email"}
        )
        print(f"\n[POST] /api/v1/auth/forgot-password (invalid email) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"


class TestResetPassword:
    """测试重置密码"""

    def test_reset_password_missing_token(self, api_client):
        """测试缺少token"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/reset-password",
            json={"new_password": "test123", "confirm_password": "test123"}
        )
        print(f"\n[POST] /api/v1/auth/reset-password (no token) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_reset_password_missing_password(self, api_client):
        """测试缺少密码"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/reset-password",
            json={"token": "some_token"}
        )
        print(f"\n[POST] /api/v1/auth/reset-password (no password) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_reset_password_password_mismatch(self, api_client):
        """测试密码不匹配"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/reset-password",
            json={
                "token": "some_token",
                "new_password": "test123",
                "confirm_password": "test456"
            }
        )
        print(f"\n[POST] /api/v1/auth/reset-password (password mismatch) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1005
        assert data.get("errmsg") == "数据验证失败"

    def test_reset_password_invalid_token(self, api_client):
        """测试无效token"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/auth/reset-password",
            json={
                "token": "invalid_token",
                "new_password": "test123456",
                "confirm_password": "test123456"
            }
        )
        print(f"\n[POST] /api/v1/auth/reset-password (invalid token) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 1001
        assert data.get("errmsg") == "重置链接无效或已过期"


class TestGetCurrentUser:
    """测试获取当前用户"""

    def test_get_current_user_without_auth(self, api_client):
        """测试未认证获取用户"""
        response = api_client.get(f"{BASE_URL}/api/v1/auth/me")
        print(f"\n[GET] /api/v1/auth/me (no auth) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001
        assert data.get("errmsg") == "未登录或登录已过期"

    def test_get_current_user_invalid_token(self, api_client):
        """测试无效token"""
        response = api_client.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        print(f"\n[GET] /api/v1/auth/me (invalid token) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2002
        assert data.get("errmsg") == "Token无效"


class TestVerifyToken:
    """测试验证token"""

    def test_verify_token_invalid(self, api_client):
        """测试验证无效token"""
        response = api_client.get(
            f"{BASE_URL}/api/v1/auth/verify-token",
            headers={"Authorization": "Bearer invalid_token"}
        )
        print(f"\n[GET] /api/v1/auth/verify-token (invalid) - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") != 0
        assert data.get("errcode") == 2002
        assert data.get("errmsg") == "Token无效"

    def test_verify_token_missing(self, api_client):
        """测试缺少token"""
        response = api_client.get(f"{BASE_URL}/api/v1/auth/verify-token")
        print(f"\n[GET] /api/v1/auth/verify-token (missing) - Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("errcode") == 2001
        assert data.get("errmsg") == "未登录或登录已过期"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
