from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from app.core.database import get_db
from app.core.config import settings
from app.schemas.user import (
    UserCreate, UserLogin, User, UserResponse, Token, 
    EmailVerification, PasswordReset, PasswordResetConfirm,
    MessageResponse
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
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    
    return user

@router.post("/register", response_model=MessageResponse)
async def register(user_data: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    auth_service = AuthService(db)
    
    try:
        await auth_service.create_user(user_data)
        
        # TODO: 发送邮箱验证邮件（后台任务）
        # background_tasks.add_task(send_verification_email, user.email, user.verification_token)
        
        return MessageResponse(
            message="注册成功，请检查邮箱并验证账户"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate_user(
        user_credentials.email, 
        user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先验证邮箱"
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user.email}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )

@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(verification_data: EmailVerification, db: AsyncSession = Depends(get_db)):
    """邮箱验证"""
    auth_service = AuthService(db)
    
    success = await auth_service.verify_email(verification_data.token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证链接无效或已过期"
        )
    
    return MessageResponse(message="邮箱验证成功")

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(password_reset: PasswordReset, db: AsyncSession = Depends(get_db)):
    """忘记密码"""
    auth_service = AuthService(db)
    
    try:
        await auth_service.generate_password_reset_token(password_reset.email)
        
        # TODO: 发送密码重置邮件
        
        return MessageResponse(
            message="密码重置链接已发送到您的邮箱"
        )
    except ValueError:
        # 出于安全考虑，即使邮箱不存在也返回成功消息
        return MessageResponse(
            message="密码重置链接已发送到您的邮箱"
        )

@router.post("/reset-password", response_model=MessageResponse)
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重置链接无效或已过期"
        )
    
    return MessageResponse(message="密码重置成功")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)

@router.get("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """验证token是否有效"""
    return {"valid": True, "user_id": current_user.id, "email": current_user.email}
