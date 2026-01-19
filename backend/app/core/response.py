"""
统一响应管理模块

提供所有API接口的统一返回格式:
{"errcode": 0, "errmsg": "success", "data": {...}}

错误码定义:
- 0: 成功
- 1xxx: 通用错误
- 2xxx: 认证错误
- 3xxx: 业务错误
- 4xxx: 系统错误
"""

from typing import Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrCode(Enum):
    """
    错误码枚举
    
    错误码规范:
    - 0: 成功
    - 1000-1999: 通用错误
    - 2000-2999: 认证错误
    - 3000-3999: 业务错误
    - 4000-4999: 系统错误
    """
    
    # 成功
    SUCCESS = (0, "success", "操作成功")
    
    # 通用错误 1xxx
    INVALID_REQUEST = (1001, "invalid_request", "请求参数错误")
    NOT_FOUND = (1002, "not_found", "资源不存在")
    PERMISSION_DENIED = (1003, "permission_denied", "没有权限")
    RATE_LIMITED = (1004, "rate_limited", "请求过于频繁")
    VALIDATION_ERROR = (1005, "validation_error", "数据验证失败")
    
    # 认证错误 2xxx
    UNAUTHORIZED = (2001, "unauthorized", "未登录或登录已过期")
    TOKEN_INVALID = (2002, "token_invalid", "Token无效")
    TOKEN_EXPIRED = (2003, "token_expired", "Token已过期")
    USER_NOT_VERIFIED = (2004, "user_not_verified", "用户未验证")
    INCORRECT_PASSWORD = (2005, "incorrect_password", "密码错误")
    EMAIL_NOT_REGISTERED = (2006, "email_not_registered", "邮箱未注册")
    EMAIL_ALREADY_EXISTS = (2007, "email_already_exists", "邮箱已注册")
    
    # 业务错误 3xxx
    FILE_TOO_LARGE = (3001, "file_too_large", "文件过大")
    INVALID_FILE_FORMAT = (3002, "invalid_file_format", "不支持的文件格式")
    IMAGE_NOT_FOUND = (3003, "image_not_found", "图像不存在")
    PROCESSING_FAILED = (3004, "processing_failed", "处理失败")
    INSUFFICIENT_CREDITS = (3005, "insufficient_credits", "积分不足")
    BATCH_LIMIT_EXCEEDED = (3006, "batch_limit_exceeded", "超过批量处理限制")
    OPERATION_NOT_ALLOWED = (3007, "operation_not_allowed", "不允许的操作")
    
    # 系统错误 4xxx
    INTERNAL_ERROR = (4001, "internal_error", "服务器内部错误")
    DATABASE_ERROR = (4002, "database_error", "数据库错误")
    EXTERNAL_SERVICE_ERROR = (4003, "external_service_error", "外部服务错误")
    SERVICE_UNAVAILABLE = (4004, "service_unavailable", "服务不可用")
    
    def __init__(self, code: int, msg_key: str, default_message: str):
        self._code = code
        self._msg_key = msg_key
        self._default_message = default_message
    
    @property
    def code(self) -> int:
        """获取错误码"""
        return self._code
    
    @property
    def msg_key(self) -> str:
        """获取消息键名"""
        return self._msg_key
    
    @property
    def default_message(self) -> str:
        """获取默认消息"""
        return self._default_message


class ResponseData(BaseModel):
    """统一响应数据结构"""
    errcode: int = Field(..., description="错误码，0表示成功")
    errmsg: str = Field(..., description="错误消息")
    data: Optional[Any] = Field(None, description="响应数据")


class UnifiedResponse(BaseModel):
    """统一响应模型"""
    errcode: int
    errmsg: str
    data: Optional[Any] = None
    
    def model_dump(self, *args, **kwargs):
        """重写 model_dump 以排除 None 值"""
        result = super().model_dump(*args, **kwargs)
        # 移除 None 值
        return {k: v for k, v in result.items() if v is not None}
    
    @classmethod
    def success(cls, data: Any = None) -> "UnifiedResponse":
        """创建成功响应"""
        return cls(
            errcode=ErrCode.SUCCESS.code,
            errmsg=ErrCode.SUCCESS.default_message,
            data=data
        )
    
    @classmethod
    def error(cls, errcode: ErrCode, data: Any = None, custom_message: str = None) -> "UnifiedResponse":
        """创建错误响应"""
        message = custom_message or errcode.default_message
        return cls(
            errcode=errcode.code,
            errmsg=message,
            data=data
        )
    
    @classmethod
    def from_dict(cls, errcode: int, errmsg: str, data: Any = None) -> "UnifiedResponse":
        """从字典创建响应"""
        return cls(
            errcode=errcode,
            errmsg=errmsg,
            data=data
        )


def success_response(data: Any = None) -> dict:
    """
    创建成功响应字典
    
    Args:
        data: 响应数据
        
    Returns:
        统一格式的成功响应字典
    """
    response = {
        "errcode": ErrCode.SUCCESS.code,
        "errmsg": ErrCode.SUCCESS.default_message,
    }
    if data is not None:
        response["data"] = data
    return response


def error_response(
    errcode: ErrCode, 
    data: Any = None, 
    custom_message: str = None
) -> dict:
    """
    创建错误响应字典
    
    Args:
        errcode: 错误码枚举
        data: 额外数据
        custom_message: 自定义消息（覆盖默认消息）
        
    Returns:
        统一格式的错误响应字典
    """
    message = custom_message or errcode.default_message
    response = {
        "errcode": errcode.code,
        "errmsg": message,
    }
    if data is not None:
        response["data"] = data
    return response


class BusinessException(Exception):
    """业务异常"""
    
    def __init__(
        self, 
        errcode: ErrCode, 
        message: str = None,
        data: Any = None
    ):
        self.errcode = errcode
        self.message = message or errcode.default_message
        self.data = data
        super().__init__(self.message)


class AuthenticationException(BusinessException):
    """认证异常"""
    pass


class ValidationException(BusinessException):
    """验证异常"""
    pass


def create_exception_response(exception: Exception) -> dict:
    """
    从异常创建错误响应
    
    Args:
        exception: 异常对象
        
    Returns:
        统一格式的错误响应字典
    """
    if isinstance(exception, BusinessException):
        return error_response(
            errcode=exception.errcode,
            custom_message=exception.message,
            data=exception.data
        )
    
    # 未知异常
    return error_response(
        errcode=ErrCode.INTERNAL_ERROR,
        custom_message=str(exception) if str(exception) else ErrCode.INTERNAL_ERROR.default_message
    )


def get_error_code_from_status(status_code: int) -> ErrCode:
    """
    根据HTTP状态码获取对应的错误码
    
    Args:
        status_code: HTTP状态码
        
    Returns:
        对应的错误码枚举
    """
    status_map = {
        400: ErrCode.INVALID_REQUEST,
        401: ErrCode.UNAUTHORIZED,
        403: ErrCode.PERMISSION_DENIED,
        404: ErrCode.NOT_FOUND,
        422: ErrCode.VALIDATION_ERROR,
        429: ErrCode.RATE_LIMITED,
        500: ErrCode.INTERNAL_ERROR,
        502: ErrCode.EXTERNAL_SERVICE_ERROR,
        503: ErrCode.EXTERNAL_SERVICE_ERROR,
    }
    return status_map.get(status_code, ErrCode.INTERNAL_ERROR)


class ResponseHandler:
    """响应处理器"""
    
    @staticmethod
    def ok(data: Any = None) -> dict:
        """成功响应"""
        return success_response(data)
    
    @staticmethod
    def fail(errcode: ErrCode, message: str = None, data: Any = None) -> dict:
        """失败响应"""
        return error_response(errcode, data, message)
    
    @staticmethod
    def created(data: Any = None) -> dict:
        """创建成功响应"""
        return success_response(data)
    
    @staticmethod
    def no_content() -> dict:
        """无内容响应"""
        return success_response(None)
    
    @staticmethod
    def paginated(
        items: list, 
        total: int, 
        page: int, 
        per_page: int
    ) -> dict:
        """分页响应"""
        return success_response({
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": page * per_page < total,
            "has_prev": page > 1
        })


# 全局响应处理器实例
response_handler = ResponseHandler()


async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器
    
    Args:
        request: FastAPI请求对象
        exc: 异常对象
        
    Returns:
        JSONResponse
    """
    if isinstance(exc, BusinessException):
        response_data = error_response(
            errcode=exc.errcode,
            custom_message=exc.message,
            data=exc.data
        )
        return JSONResponse(
            status_code=200,  # 始终返回200
            content=response_data
        )
    
    if isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
        errcode = get_error_code_from_status(status_code)
        
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
        return JSONResponse(
            status_code=200,  # 始终返回200
            content=response_data
        )
    
    if isinstance(exc, RequestValidationError):
        status_code = 422
        errcode = ErrCode.VALIDATION_ERROR
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        response_data = error_response(
            errcode=errcode,
            data={"validation_errors": errors}
        )
        return JSONResponse(
            status_code=200,  # 始终返回200
            content=response_data
        )
    
    # 其他未知异常
    response_data = error_response(
        errcode=ErrCode.INTERNAL_ERROR,
        custom_message=ErrCode.INTERNAL_ERROR.default_message
    )

    # 记录未处理的异常日志
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=200,  # 始终返回200
        content=response_data
    )
