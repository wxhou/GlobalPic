from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from datetime import datetime

# 使用共享的Base
from app.core.database import Base

class Subscription(Base):
    """用户订阅记录"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # 订阅计划
    plan_id = Column(String(50), default="free")  # free, personal, enterprise
    plan_name = Column(String(100), default="免费版")
    
    # 订阅状态
    status = Column(String(50), default="active")  # active, canceled, expired, past_due
    
    # 订阅期限
    started_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    
    # 支付信息
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    
    # 使用量追踪
    images_used_this_month = Column(Integer, default=0)
    last_reset_at = Column(DateTime(timezone=True), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, plan='{self.plan_id}', status='{self.status}')>"


class CreditTransaction(Base):
    """用户积分交易记录"""
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 交易类型
    transaction_type = Column(String(50), nullable=False)  # purchase, usage, refund, bonus
    
    # 积分变化
    credits_before = Column(Integer, default=0)
    credits_change = Column(Integer, default=0)
    credits_after = Column(Integer, default=0)
    
    # 交易详情
    description = Column(Text, nullable=True)
    related_id = Column(String(255), nullable=True)  # 关联的订单/任务ID
    
    # 过期时间（如果有）
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CreditTransaction(id={self.id}, user_id={self.user_id}, type='{self.transaction_type}', change={self.credits_change})>"


class APIKey(Base):
    """用户API密钥"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 密钥信息
    key_id = Column(String(50), unique=True, index=True, nullable=False)
    api_key_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    
    # 权限和限制
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)  # 每分钟请求数
    ip_whitelist = Column(Text, nullable=True)  # JSON数组，IP白名单
    
    # 使用统计
    total_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # 过期时间
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', active={self.is_active})>"
