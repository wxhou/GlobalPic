from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from app.core.database import get_db
from app.core.config import settings
from app.core.response import ErrCode, error_response, success_response, BusinessException
from app.schemas.user import (
    UserCreate, UserLogin, User, UserResponse, Token, 
    PasswordReset, PasswordResetConfirm
)
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（需要认证）"""
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise BusinessException(ErrCode.TOKEN_INVALID)
    except (InvalidTokenError, ExpiredSignatureError):
        raise BusinessException(ErrCode.TOKEN_INVALID)
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise BusinessException(ErrCode.UNAUTHORIZED)
    
    return user

@router.post("/register")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    auth_service = AuthService(db)
    
    try:
        await auth_service.create_user(user_data)
        
        return success_response({
            "message": "注册成功",
            "email": user_data.email
        })
    except ValueError as e:
        # 邮箱已存在
        return error_response(ErrCode.EMAIL_ALREADY_EXISTS)
    except Exception as e:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message="注册失败，请稍后重试")

@router.post("/login")
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate_user(
        user_credentials.email, 
        user_credentials.password
    )
    
    if not user:
        return error_response(ErrCode.INCORRECT_PASSWORD, custom_message="用户名或密码错误")
    
    access_token = auth_service.create_access_token(
        data={"sub": user.email}
    )
    
    return success_response({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
        "user": UserResponse.model_validate(user).model_dump()
    })

@router.post("/forgot-password")
async def forgot_password(password_reset: PasswordReset, db: AsyncSession = Depends(get_db)):
    """忘记密码"""
    auth_service = AuthService(db)
    
    try:
        await auth_service.generate_password_reset_token(password_reset.email)
        
        # TODO: 发送密码重置邮件
        
        return success_response({"message": "密码重置链接已发送到您的邮箱"})
    except ValueError:
        # 出于安全考虑，即使邮箱不存在也返回成功消息
        return success_response({"message": "密码重置链接已发送到您的邮箱"})

@router.post("/reset-password")
async def reset_password(
    password_reset_data: PasswordResetConfirm, 
    db: AsyncSession = Depends(get_db)
):
    """重置密码"""
    auth_service = AuthService(db)
    
    success = await auth_service.verify_password_reset_token(
        password_reset_data.token, 
        password_reset_data.new_password
    )
    
    if not success:
        return error_response(ErrCode.INVALID_REQUEST, custom_message="重置链接无效或已过期")
    
    return success_response({"message": "密码重置成功"})

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return success_response(UserResponse.model_validate(current_user).model_dump())

@router.get("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """验证token是否有效"""
    return success_response({
        "valid": True, 
        "user_id": current_user.id, 
        "email": current_user.email
    })
