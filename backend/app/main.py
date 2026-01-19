from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import os
from loguru import logger

from app.core.config import settings
from app.core.database import async_engine, Base, init_db, close_db
from app.api.v1.api import api_router
from app.core.logging import setup_logging
from app.core.security import setup_security
from app.core.response import handle_exception, BusinessException, ErrCode, error_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("正在初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成")
    
    yield
    
    # 关闭时清理数据库连接
    logger.info("正在关闭数据库连接...")
    await close_db()
    logger.info("数据库连接已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="跨境电商视觉本地化AI平台",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,  # 使用lifespan管理生命周期
)

# 设置日志
setup_logging()

# 设置安全
setup_security(app)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.globalpic.ai"]
    )

# 全局异常处理 - 使用统一响应格式
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    logger.warning(f"业务异常: {exc.errcode.code} - {exc.message}")
    response_data = error_response(
        errcode=exc.errcode,
        custom_message=exc.message,
        data=exc.data
    )
    return JSONResponse(status_code=200, content=response_data)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器 - 转换为统一响应格式"""
    # 401 认证异常转换为业务错误码
    errcode = ErrCode.INVALID_REQUEST
    if exc.status_code == 401:
        errcode = ErrCode.UNAUTHORIZED
        # 认证异常按业务错误处理，不记录警告级别日志
        if settings.DEBUG:
            logger.debug(f"认证异常（已转换）: {exc.status_code}")
    elif exc.status_code == 403:
        errcode = ErrCode.PERMISSION_DENIED
        logger.warning(f"权限不足: {exc.detail}")
    elif exc.status_code == 404:
        errcode = ErrCode.NOT_FOUND
        logger.debug(f"资源不存在: {exc.detail}")
    else:
        logger.debug(f"HTTP异常（已转换）: {exc.status_code} - {exc.detail}")
    
    # 处理英文异常消息，转换为中文
    detail = str(exc.detail) if exc.detail else ""
    english_messages = [
        "Not authenticated",
        "not authenticated",
        "Token invalid",
        "token invalid",
        "Token expired",
        "token expired",
    ]
    if any(msg in detail for msg in english_messages):
        # 如果是英文消息，使用默认的中文消息
        custom_message = errcode.default_message
    else:
        custom_message = detail if detail else errcode.default_message
    
    response_data = error_response(
        errcode=errcode,
        custom_message=custom_message
    )
    return JSONResponse(status_code=200, content=response_data)


def _translate_validation_message(msg: str, error_type: str) -> str:
    """将Pydantic验证错误消息转换为中文"""
    # 常见验证错误类型映射
    message_map = {
        # int_parsing
        "int_parsing": "应该是一个有效的整数",
        # string_type
        "string_type": "应该是一个字符串",
        "string_too_short": "字符串太短",
        "string_too_long": "字符串太长",
        "string_pattern_mismatch": "字符串格式不匹配",
        # bool_parsing
        "bool_parsing": "应该是一个有效的布尔值",
        # float_parsing
        "float_parsing": "应该是一个有效的数字",
        # list_type
        "list_type": "应该是一个列表",
        # dict_type
        "dict_type": "应该是一个字典",
        # value_error
        "value_error": "值验证失败",
        # missing
        "missing": "缺少必填字段",
        # frozen
        "frozen": "字段不可修改",
        # extra_forbidden
        "extra_forbidden": "不允许的额外字段",
    }
    
    # 按类型返回中文消息
    if error_type in message_map:
        return message_map[error_type]
    
    # 常见关键词替换
    translations = {
        "Input should be a valid integer": "应该是一个有效的整数",
        "Input should be a valid string": "应该是一个有效的字符串",
        "Input should be a valid boolean": "应该是一个有效的布尔值",
        "Input should be a valid float": "应该是一个有效的数字",
        "String should have at least": "字符串至少需要",
        "String should have at most": "字符串最多",
        "characters": "个字符",
        "Expected": "期望",
        "received": "收到",
        "field required": "字段为必填项",
        "None is not allowed": "不允许为空",
        "ensure this value is greater than or equal to": "值必须大于或等于",
        "ensure this value is less than or equal to": "值必须小于或等于",
    }
    
    for en, cn in translations.items():
        if en in msg:
            return msg.replace(en, cn)
    
    return msg


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    logger.warning(f"验证异常: {exc.errors()}")
    errors = []
    for error in exc.errors():
        original_msg = error["msg"]
        error_type = error["type"]
        # 将英文消息转换为中文
        chinese_msg = _translate_validation_message(original_msg, error_type)
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": chinese_msg,
            "type": error_type
        })
    response_data = error_response(
        errcode=ErrCode.VALIDATION_ERROR,
        data={"validation_errors": errors}
    )
    return JSONResponse(status_code=200, content=response_data)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    import traceback
    error_msg = f"全局异常: {exc}\n{traceback.format_exc()}"
    logger.error(error_msg)
    
    response_data = error_response(
        errcode=ErrCode.INTERNAL_ERROR,
        custom_message=ErrCode.INTERNAL_ERROR.default_message
    )
    return JSONResponse(status_code=200, content=response_data)


# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

# API路由
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
