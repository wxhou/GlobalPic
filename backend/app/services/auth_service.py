from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
import string
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserLogin
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def generate_verification_token(self) -> str:
        """生成邮箱验证token"""
        return secrets.token_urlsafe(32)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """创建新用户"""
        # 检查邮箱是否已存在
        result = await self.db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ValueError("邮箱已被注册")
        
        # 创建用户
        hashed_password = self.get_password_hash(user_data.password)
        verification_token = self.generate_verification_token()
        
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            verification_token=verification_token,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """验证用户凭据"""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    async def verify_email(self, token: str) -> bool:
        """验证邮箱"""
        result = await self.db.execute(select(User).where(User.verification_token == token))
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        user.is_verified = True
        user.verification_token = None
        await self.db.commit()
        return True
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def generate_password_reset_token(self, email: str) -> str:
        """生成密码重置token"""
        user = await self.get_user_by_email(email)
        if not user:
            raise ValueError("用户不存在")
        
        reset_token = self.generate_verification_token()
        user.verification_token = reset_token
        await self.db.commit()
        
        return reset_token
    
    async def verify_password_reset_token(self, token: str, new_password: str) -> bool:
        """验证密码重置token并设置新密码"""
        result = await self.db.execute(select(User).where(User.verification_token == token))
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        user.hashed_password = self.get_password_hash(new_password)
        user.verification_token = None
        await self.db.commit()
        return True
    
    async def deactivate_user(self, user_id: int) -> bool:
        """停用用户账户"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        await self.db.commit()
        return True
