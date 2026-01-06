"""
支付和订阅服务
集成Stripe实现订阅管理和支付处理
"""
import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import stripe
from stripe import StripeClient

logger = logging.getLogger(__name__)


class PaymentService:
    """支付和订阅服务"""

    # 订阅套餐配置
    PLANS = {
        "free": {
            "name": "免费版",
            "price_monthly": 0,
            "price_yearly": 0,
            "images_per_month": 3,
            "features": ["3张免费试用", "低分辨率", "基础功能"],
            "stripe_price_id": None,
        },
        "personal": {
            "name": "个人版",
            "price_monthly": 19,
            "price_yearly": 190,  # 2个月免费
            "images_per_month": -1,  # 无限
            "features": [
                "无限图像处理",
                "高清输出",
                "所有功能",
                "邮件支持",
            ],
            "stripe_price_id_monthly": "price_personal_monthly",
            "stripe_price_id_yearly": "price_personal_yearly",
        },
        "enterprise": {
            "name": "企业版",
            "price_monthly": 99,
            "price_yearly": 990,
            "images_per_month": -1,
            "features": [
                "无限图像处理",
                "4K超高清输出",
                "API访问",
                "团队协作",
                "专属客服",
            ],
            "stripe_price_id_monthly": "price_enterprise_monthly",
            "stripe_price_id_yearly": "price_enterprise_yearly",
        },
    }

    # 按需付费配置
    CREDIT_PACKAGES = [
        {"credits": 10, "price": 4.99, "name": "10张图片包"},
        {"credits": 50, "price": 19.99, "name": "50张图片包"},
        {"credits": 100, "price": 34.99, "name": "100张图片包"},
    ]

    def __init__(self):
        self.stripe: Optional[StripeClient] = None
        self.is_initialized = False
        self._model_lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """初始化支付服务"""
        if self.is_initialized:
            return True

        async with self._model_lock:
            if self.is_initialized:
                return True

            try:
                from app.core.config import settings

                if not settings.STRIPE_SECRET_KEY:
                    logger.warning("Stripe密钥未配置，使用模拟模式")
                    return False

                self.stripe = StripeClient(settings.STRIPE_SECRET_KEY)
                self.is_initialized = True
                logger.info("Payment服务初始化完成")
                return True

            except Exception as e:
                logger.error(f"Payment服务初始化失败: {e}")
                return False

    async def create_checkout_session(
        self,
        user_id: int,
        user_email: str,
        plan_id: str,
        mode: str = "subscription",
    ) -> Dict[str, Any]:
        """创建Stripe Checkout会话

        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            plan_id: 套餐ID
            mode: 模式 (subscription/one_time)

        Returns:
            包含会话URL的字典
        """
        if not self.is_initialized:
            return self._create_mock_checkout(user_id, plan_id, mode)

        try:
            plan = self.PLANS.get(plan_id)
            if not plan:
                return {"success": False, "error": "无效的套餐"}

            from app.core.config import settings

            price_id = (
                plan["stripe_price_id_monthly"]
                if mode == "subscription"
                else None
            )

            # 创建Checkout会话
            checkout_params = {
                "customer_email": user_email,
                "line_items": [
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                "mode": mode,
                "success_url": f"{settings.CDN_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{settings.CDN_URL}/payment/cancel",
                "metadata": {
                    "user_id": str(user_id),
                    "plan_id": plan_id,
                },
            }

            if mode == "one_time":
                checkout_params.pop("customer_email")

            session = await asyncio.to_thread(
                self.stripe.checkout.sessions.create, **checkout_params
            )

            return {
                "success": True,
                "session_id": session.id,
                "url": session.url,
            }

        except Exception as e:
            logger.error(f"创建Checkout会话失败: {e}")
            return {"success": False, "error": str(e)}

    async def create_credit_checkout(
        self,
        user_id: int,
        user_email: str,
        package_index: int = 0,
    ) -> Dict[str, Any]:
        """创建按需付费Checkout会话

        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            package_index: 套餐索引

        Returns:
            包含会话URL的字典
        """
        if not self.is_initialized:
            return self._create_mock_checkout(user_id, "credit", "one_time")

        try:
            package = self.CREDIT_PACKAGES[package_index]
            from app.core.config import settings

            session = await asyncio.to_thread(
                self.stripe.checkout.sessions.create,
                customer_email=user_email,
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": package["name"],
                                "description": f"{package['credits']}张图片处理额度",
                            },
                            "unit_amount": int(package["price"] * 100),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=f"{settings.CDN_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.CDN_URL}/payment/cancel",
                metadata={
                    "user_id": str(user_id),
                    "credits": package["credits"],
                    "type": "credit",
                },
            )

            return {
                "success": True,
                "session_id": session.id,
                "url": session.url,
            }

        except Exception as e:
            logger.error(f"创建额度Checkout会话失败: {e}")
            return {"success": False, "error": str(e)}

    async def handle_webhook(
        self, payload: bytes, signature: str
    ) -> Dict[str, Any]:
        """处理Stripe Webhook

        Args:
            payload: 请求体
            signature: Stripe签名

        Returns:
            处理结果
        """
        if not self.is_initialized:
            return {"success": True, "mock": True}

        try:
            from app.core.config import settings

            event = self.stripe.webhooks.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET,
            )

            logger.info(f"收到Stripe webhook: {event['type']}")

            # 处理不同类型的事件
            if event["type"] == "checkout.session.completed":
                await self._handle_checkout_complete(event["data"]["object"])
            elif event["type"] == "customer.subscription.created":
                await self._handle_subscription_created(event["data"]["object"])
            elif event["type"] == "customer.subscription.updated":
                await self._handle_subscription_updated(event["data"]["object"])
            elif event["type"] == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event["data"]["object"])
            elif event["type"] == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(event["data"]["object"])
            elif event["type"] == "invoice.payment_failed":
                await self._handle_payment_failed(event["data"]["object"])

            return {"success": True, "event_type": event["type"]}

        except Exception as e:
            logger.error(f"处理Webhook失败: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_checkout_complete(
        self, session: Dict[str, Any]
    ) -> None:
        """处理Checkout完成"""
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id")

        if plan_id == "credit":
            credits = int(metadata.get("credits", 0))
            logger.info(f"用户{user_id}购买{credits}额度")
            # TODO: 更新用户额度

    async def _handle_subscription_created(
        self, subscription: Dict[str, Any]
    ) -> None:
        """处理订阅创建"""
        metadata = subscription.get("metadata", {})
        user_id = metadata.get("user_id")
        logger.info(f"用户{user_id}创建订阅")

    async def _handle_subscription_updated(
        self, subscription: Dict[str, Any]
    ) -> None:
        """处理订阅更新"""
        logger.info(f"订阅更新: {subscription['id']}")

    async def _handle_subscription_deleted(
        self, subscription: Dict[str, Any]
    ) -> None:
        """处理订阅删除"""
        logger.info(f"订阅取消: {subscription['id']}")

    async def _handle_payment_succeeded(
        self, invoice: Dict[str, Any]
    ) -> None:
        """处理支付成功"""
        logger.info(f"支付成功: {invoice['id']}")

    async def _handle_payment_failed(
        self, invoice: Dict[str, Any]
    ) -> None:
        """处理支付失败"""
        logger.warning(f"支付失败: {invoice['id']}")
        # TODO: 发送支付失败通知

    def _create_mock_checkout(
        self, user_id: int, plan_id: str, mode: str
    ) -> Dict[str, Any]:
        """创建模拟Checkout会话（用于测试）"""
        return {
            "success": True,
            "session_id": f"mock_session_{uuid4()}",
            "url": f"/payment/mock-success?plan={plan_id}&user={user_id}",
            "mock": True,
        }

    async def get_plans(self) -> List[Dict[str, Any]]:
        """获取所有套餐信息"""
        plans = []
        for plan_id, plan in self.PLANS.items():
            plans.append(
                {
                    "id": plan_id,
                    "name": plan["name"],
                    "price_monthly": plan["price_monthly"],
                    "price_yearly": plan["price_yearly"],
                    "images_per_month": "无限" if plan["images_per_month"] == -1 else plan["images_per_month"],
                    "features": plan["features"],
                }
            )
        return plans

    async def get_credit_packages(self) -> List[Dict[str, Any]]:
        """获取按需付费套餐"""
        return self.CREDIT_PACKAGES

    async def check_subscription_status(
        self, user_id: int
    ) -> Dict[str, Any]:
        """检查用户订阅状态

        Args:
            user_id: 用户ID

        Returns:
            订阅状态信息
        """
        # TODO: 从数据库查询用户订阅状态
        return {
            "user_id": user_id,
            "plan": "free",
            "status": "active",
            "images_used": 0,
            "images_limit": 3,
            "credits_remaining": 0,
            "subscription_end": None,
        }

    async def cancel_subscription(self, user_id: int) -> Dict[str, Any]:
        """取消订阅

        Args:
            user_id: 用户ID

        Returns:
            取消结果
        """
        # TODO: 调用Stripe API取消订阅
        return {
            "success": True,
            "message": "订阅已取消，到期后将降级为免费版",
        }


class APIKeyService:
    """API密钥服务"""

    def __init__(self):
        self.is_initialized = True

    async def create_api_key(
        self,
        user_id: int,
        name: str,
        ip_whitelist: Optional[List[str]] = None,
        rate_limit: int = 100,
    ) -> Dict[str, Any]:
        """创建API密钥

        Args:
            user_id: 用户ID
            name: 密钥名称
            ip_whitelist: IP白名单
            rate_limit: 频率限制（次/分钟）

        Returns:
            包含密钥信息的字典
        """
        import secrets

        # 生成密钥
        key_id = secrets.token_urlsafe(8)
        key_secret = secrets.token_urlsafe(24)
        api_key = f"gp_{key_id}_{key_secret}"

        # 哈希存储
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # TODO: 存储到数据库

        return {
            "success": True,
            "api_key": api_key,
            "key_id": key_id,
            "name": name,
            "rate_limit": rate_limit,
            "ip_whitelist": ip_whitelist or [],
        }

    async def validate_api_key(
        self, api_key: str, client_ip: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """验证API密钥

        Args:
            api_key: API密钥
            client_ip: 客户端IP

        Returns:
            (是否有效, 用户信息)
        """
        if not api_key:
            return False, None

        # 检查格式
        if not api_key.startswith("gp_"):
            return False, None

        # TODO: 从数据库查询并验证
        # 临时返回模拟结果
        return True, {
            "user_id": 1,
            "plan": "enterprise",
            "credits_remaining": 1000,
            "rate_limit": 100,
        }

    async def revoke_api_key(self, key_id: str, user_id: int) -> bool:
        """撤销API密钥"""
        # TODO: 从数据库删除
        return True

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {"is_initialized": self.is_initialized}


# 全局服务实例
payment_service = PaymentService()
api_key_service = APIKeyService()
