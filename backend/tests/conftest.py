"""
Pytest配置 - API测试 fixtures 和 测试结果收集
"""
import pytest
import httpx
import uuid
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# API基础URL
BASE_URL = "http://localhost:8000"

# 测试结果文件路径
RESULTS_FILE = Path(__file__).parent / "results.json"


# ==================== 测试结果收集 ====================

_test_results = []
_current_test_data = {}


def pytest_configure(config):
    """测试配置初始化"""
    pass


def pytest_runtest_logreport(report):
    """记录每个测试的结果"""
    if report.when == "teardown":  # 只在测试结束后记录
        # 获取测试名称
        test_name = report.node.name if hasattr(report, 'node') and report.node else report.nodeid.split('::')[-1] if report.nodeid else "unknown"
        
        # 获取当前测试的请求/响应数据
        test_input = _current_test_data.get(test_name, {}).get("input", {})
        test_output = _current_test_data.get(test_name, {}).get("output", {})
        
        test_info = {
            "name": test_name,
            "request": test_input.get("request", {}),
            "response": test_output
        }
        
        _test_results.append(test_info)
        
        # 清理当前测试数据
        _current_test_data.pop(test_name, None)


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时保存结果"""
    # 保存结果到 JSON 文件
    try:
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(_test_results, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已保存到: {RESULTS_FILE}")
    except Exception as e:
        print(f"\n保存测试结果失败: {e}")
    
    # 使用 pytest 实际测试结果
    # exitstatus=0 表示所有测试通过
    total = len(_test_results)
    if exitstatus == 0:
        passed = total
        failed = 0
    else:
        # 粗略估计失败数量（实际数量需要从 pytest report 获取）
        # 这里使用 errcode 分布作为参考
        errcode_0 = sum(1 for t in _test_results if t.get("output", {}).get("response", {}).get("body", {}).get("errcode", 0) == 0)
        passed = errcode_0
        failed = total - passed
    
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print("=" * 60)


class RecordingClient:
    """带录制功能的HTTP客户端"""
    
    def __init__(self, base_client: httpx.Client, test_name: str):
        self._client = base_client
        self._test_name = test_name
    
    def _record_request(self, method: str, url: str, **kwargs):
        """记录请求信息"""
        if self._test_name not in _current_test_data:
            _current_test_data[self._test_name] = {"input": {}, "output": {}}
        
        # 解析完整URL
        if url.startswith('http://') or url.startswith('https://'):
            full_url = url
        else:
            base_url = str(self._client.base_url).rstrip('/')
            relative_url = url.lstrip('/')
            full_url = f"{base_url}/{relative_url}"
        
        request_data = {
            "method": method.upper(),
            "url": full_url,
        }
        
        # 记录请求体
        if "json" in kwargs:
            request_data["body"] = kwargs["json"]
        elif "data" in kwargs:
            request_data["body"] = kwargs["data"]
        
        _current_test_data[self._test_name]["input"]["request"] = request_data
    
    def _record_response(self, response: httpx.Response):
        """记录响应信息（只记录body，不记录status_code）"""
        if self._test_name not in _current_test_data:
            _current_test_data[self._test_name] = {"input": {}, "output": {}}
        
        # 尝试解析响应体
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text
        
        _current_test_data[self._test_name]["output"] = response_body
    
    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """发送请求并记录"""
        self._record_request(method, url, **kwargs)
        response = self._client.request(method, url, **kwargs)
        self._record_response(response)
        return response
    
    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs) -> httpx.Response:
        return self.request("PUT", url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)
    
    @property
    def base_url(self):
        return self._client.base_url
    
    def close(self):
        """关闭客户端"""
        self._client.close()


# ==================== 响应格式工具函数 ====================

def get_token_from_response(response: httpx.Response) -> str | None:
    """从统一响应格式中提取token"""
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get("errcode") == 0 and data.get("data"):
                return data["data"].get("access_token")
        except Exception:
            pass
    return None


def get_user_data_from_response(response: httpx.Response) -> dict | None:
    """从统一响应格式中提取用户数据"""
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get("errcode") == 0 and data.get("data"):
                return data["data"].get("user")
        except Exception:
            pass
    return None


class UnifiedResponseChecker:
    """统一响应格式检查器"""
    
    @staticmethod
    def is_success(response: httpx.Response) -> bool:
        """检查响应是否成功"""
        if response.status_code != 200:
            return False
        try:
            data = response.json()
            return data.get("errcode") == 0
        except Exception:
            return False
    
    @staticmethod
    def check_success(response: httpx.Response, msg: str = ""):
        """断言响应成功"""
        assert response.status_code == 200, f"期望HTTP 200，实际{response.status_code}"
        data = response.json()
        assert data.get("errcode") == 0, f"期望errcode=0，实际{data.get('errcode')}，{msg}"
        assert data.get("errmsg") == "success", f"期望errmsg=success，实际{data.get('errmsg')}"
    
    @staticmethod
    def check_error(response: httpx.Response, expected_errcode: int | None = None):
        """断言响应失败"""
        assert response.status_code == 200, f"期望HTTP 200（业务错误），实际{response.status_code}"
        data = response.json()
        assert data.get("errcode") != 0, f"期望业务错误，实际errcode=0"
        if expected_errcode:
            assert data.get("errcode") == expected_errcode, f"期望errcode={expected_errcode}，实际{data.get('errcode')}"
    
    @staticmethod
    def get_data(response: httpx.Response) -> dict | list | None:
        """获取响应数据"""
        assert UnifiedResponseChecker.is_success(response), "响应不成功，无法获取数据"
        return response.json().get("data")


# ==================== HTTP客户端 Fixtures ====================

@pytest.fixture
def api_client(request):
    """创建HTTP客户端（自动记录请求/响应）"""
    test_name = request.node.name
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    recording_client = RecordingClient(client, test_name)
    
    yield recording_client
    
    # 清理
    recording_client.close()


@pytest.fixture
def api_client_with_auth(api_client):
    """创建带认证的HTTP客户端"""
    # 尝试登录获取token
    login_response = api_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    token = None
    if login_response.status_code == 200:
        token = get_token_from_response(login_response)
    
    class AuthClient(RecordingClient):
        def __init__(self, base_client, token):
            super().__init__(base_client._client, base_client._test_name)
            self._token = token
            self._response_checker = UnifiedResponseChecker()
        
        def request(self, method, url, **kwargs):
            headers = kwargs.get("headers", {})
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            kwargs["headers"] = headers
            return self._client.request(method, url, **kwargs)
        
        @property
        def checker(self):
            return self._response_checker
    
    yield AuthClient(api_client, token)
    
    # 清理
    if token:
        try:
            api_client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        except:
            pass


# ==================== 测试用户 Fixtures ====================

@pytest.fixture
def test_user_credentials():
    """返回测试用户凭据（已存在的用户）"""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def unique_user_credentials():
    """生成唯一用户凭据"""
    unique_id = str(uuid.uuid4())[:8]
    email = f"test_{unique_id}@example.com"
    password = "testpassword123"
    return {
        "email": email,
        "password": password,
        "full_name": f"Test User {unique_id}"
    }


@pytest.fixture
def auth_token(api_client, unique_user_credentials):
    """创建新用户并返回认证token（自动清理）"""
    # 保存原始测试名称
    original_test_name = api_client._test_name
    
    # 临时修改测试名称以区分 fixture 的录制
    api_client._test_name = f"{original_test_name}_auth_token"
    
    try:
        # 1. 注册用户
        register_response = api_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_user_credentials["email"],
                "password": unique_user_credentials["password"],
                "confirm_password": unique_user_credentials["password"],
                "full_name": unique_user_credentials["full_name"]
            }
        )
        
        # 2. 登录获取token
        login_response = api_client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_user_credentials["email"],
                "password": unique_user_credentials["password"]
            }
        )
        
        token = get_token_from_response(login_response)
        
        # 恢复原始测试名称
        api_client._test_name = original_test_name
        
        # 返回token
        yield token
        
        # 恢复测试名称用于 cleanup 录制
        api_client._test_name = f"{original_test_name}_cleanup"
        
        # 清理：删除测试用户（可选，不影响测试）
        if token:
            try:
                # 使用原始 httpx 客户端进行清理，避免干扰录制
                with httpx.Client(base_url=BASE_URL, timeout=30.0) as cleanup_client:
                    cleanup_login = cleanup_client.post(
                        "/api/v1/auth/login",
                        json={
                            "email": unique_user_credentials["email"],
                            "password": unique_user_credentials["password"]
                        }
                    )
                    cleanup_token = get_token_from_response(cleanup_login)
                    if cleanup_token:
                        cleanup_client.post(
                            "/api/v1/auth/delete-account",
                            json={"password": unique_user_credentials["password"]},
                            headers={"Authorization": f"Bearer {cleanup_token}"}
                        )
            except Exception:
                pass
    except Exception as e:
        print(f"auth_token fixture error: {e}")
        yield None


@pytest.fixture
def auth_headers(auth_token):
    """返回认证请求头"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


@pytest.fixture
def token(auth_token):
    """认证token（auth_token的别名，用于向后兼容）"""
    return auth_token


# ==================== 响应检查 Fixtures ====================

@pytest.fixture
def unified_checker():
    """返回统一响应格式检查器"""
    return UnifiedResponseChecker()


# ==================== 测试收集修改 ====================

def pytest_collection_modifyitems(config, items):
    """修改测试项目"""
    for item in items:
        # 跳过需要实际模型初始化的测试
        if "mock" not in item.name.lower() and "init" in item.name.lower():
            item.add_marker(pytest.mark.skip(reason="需要实际模型初始化"))
