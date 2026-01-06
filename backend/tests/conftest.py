"""
Pytest配置
"""
import pytest
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_collection_modifyitems(config, items):
    """修改测试项目"""
    for item in items:
        # 跳过需要实际模型初始化的测试
        if "mock" not in item.name.lower() and "init" in item.name.lower():
            item.add_marker(pytest.mark.skip(reason="需要实际模型初始化"))
