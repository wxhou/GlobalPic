"""
订阅和支付相关数据库模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class SubscriptionStatus(enum.Enum):
    """订阅状态"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIAL = "trial"
    NONE = "none"


class PaymentStatus(enum.Enum):
    """支付状态"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class Subscription(Base):
    """用户订阅模型"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # 订阅计划
    plan_id = Column(String(50), nullable=True)  # free, personal, enterprise
    plan_name = Column(String(100), nullable=True)

    # Stripe信息
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)

    # 状态
    status = Column(String(50), default=SubscriptionStatus.NONE.value)

    # 使用额度
    images_per_month = Column(Integer, default=10)  # 每月可用图片数
    images_used = Column(Integer, default=0)  # 本月已使用
    credits = Column(Integer, default=0)  # 额外额度包

    # 付费周期
    billing_cycle = Column(String(20), nullable=True)  # monthly, yearly
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription")
    api_keys = relationship("APIKey", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, plan={self.plan_id}, status={self.status})>"

    @property
    def images_remaining(self) -> int:
        """剩余图片处理次数"""
        total = self.images_per_month + self.credits
        remaining = total - self.images_used
        return max(0, remaining)

    def can_process_image(self) -> bool:
        """检查是否还可以处理图片"""
        return self.images_remaining > 0

    def record_usage(self, count: int = 1):
        """记录使用"""
        self.images_used += count


class Payment(Base):
    """支付记录模型"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    # Stripe信息
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_charge_id = Column(String(255), nullable=True)

    # 支付信息
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="usd")
    status = Column(String(50), default=PaymentStatus.PENDING.value)

    # 支付类型
    payment_type = Column(String(50), nullable=True)  # subscription, credit_package

    # 描述
    description = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User")
    subscription = relationship("Subscription", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"


class APIKey(Base):
    """API密钥模型"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    # 密钥信息
    key_name = Column(String(100), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(10), nullable=False)  # 前缀，用于显示

    # 速率限制
    rate_limit = Column(Integer, default=100)  # 每分钟请求数
    usage_count = Column(Integer, default=0)

    # 最后使用
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # 状态
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # IP白名单
    ip_whitelist = Column(Text, nullable=True)  # JSON数组

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User")
    subscription = relationship("Subscription", back_populates="api_keys")
    usage_records = relationship("APIUsageRecord", back_populates="api_key")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.key_name}', prefix={self.key_prefix})>"

    def is_valid(self) -> bool:
        """检查密钥是否有效"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True


class APIUsageRecord(Base):
    """API使用记录模型"""
    __tablename__ = "api_usage_records"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)

    # 请求信息
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    ip_address = Column(String(50), nullable=True)

    # 响应信息
    status_code = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)  # 毫秒

    # 配额消耗
    credits_used = Column(Float, default=0)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    api_key = relationship("APIKey", back_populates="usage_records")

    def __repr__(self):
        return f"<APIUsageRecord(id={self.id}, api_key_id={self.api_key_id}, endpoint='{self.endpoint}')>"


class UsageRecord(Base):
    """用户使用记录模型"""
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 使用类型
    usage_type = Column(String(50), nullable=False)  # image_processing, batch_processing, api_call

    # 详细信息
    operation_type = Column(String(100), nullable=True)
    image_id = Column(Integer, nullable=True)
    count = Column(Integer, default=1)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User")

    def __repr__(self):
        return f"<UsageRecord(id={self.id}, user_id={self.user_id}, type={self.usage_type})>"
