from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.core.response import ErrCode, error_response, success_response
from app.models.user import User
from app.services.payment_service import payment_service, api_key_service

router = APIRouter()


class PlanResponse(BaseModel):
    """套餐响应"""
    id: str
    name: str
    price_monthly: int
    price_yearly: int
    images_per_month: str
    features: List[str]


class CreditPackageResponse(BaseModel):
    """额度包响应"""
    credits: int
    price: float
    name: str


class CheckoutRequest(BaseModel):
    """Checkout请求"""
    plan_id: str
    mode: str = "subscription"


class CreditCheckoutRequest(BaseModel):
    """额度Checkout请求"""
    package_index: int = 0


class SubscriptionStatusResponse(BaseModel):
    """订阅状态响应"""
    user_id: int
    plan: str
    status: str
    images_used: int
    images_limit: str
    credits_remaining: int
    subscription_end: Optional[str] = None


class APIKeyCreateRequest(BaseModel):
    """API密钥创建请求"""
    name: str
    ip_whitelist: Optional[List[str]] = None
    rate_limit: int = 100


class KeyIdRequest(BaseModel):
    """密钥ID请求"""
    key_id: str


@router.get("/subscription/plans")
async def get_subscription_plans():
    """获取订阅套餐列表"""
    plans = await payment_service.get_plans()
    return success_response({"plans": plans})


@router.get("/subscription/credits")
async def get_credit_packages():
    """获取按需付费套餐"""
    packages = await payment_service.get_credit_packages()
    return success_response({"packages": packages})


@router.post("/subscription/create-checkout")
async def create_subscription_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user)
):
    """创建订阅Checkout会话"""
    if request.plan_id not in ["personal", "enterprise"]:
        return error_response(ErrCode.INVALID_REQUEST, custom_message="无效的套餐ID")

    result = await payment_service.create_checkout_session(
        user_id=current_user.id,
        user_email=current_user.email,
        plan_id=request.plan_id,
        mode=request.mode,
    )

    if result["success"]:
        return success_response(result)
    else:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=result.get("error", "创建Checkout失败"))


@router.post("/subscription/create-credit-checkout")
async def create_credit_checkout(
    request: CreditCheckoutRequest,
    current_user: User = Depends(get_current_user)
):
    """创建额度购买Checkout会话"""
    if request.package_index < 0 or request.package_index > 2:
        return error_response(ErrCode.INVALID_REQUEST, custom_message="无效的套餐索引")

    result = await payment_service.create_credit_checkout(
        user_id=current_user.id,
        user_email=current_user.email,
        package_index=request.package_index,
    )

    if result["success"]:
        return success_response(result)
    else:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message=result.get("error", "创建Checkout失败"))


@router.get("/subscription/status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user)
):
    """获取当前订阅状态"""
    status_info = await payment_service.check_subscription_status(current_user.id)
    return success_response(status_info)


@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user)
):
    """取消订阅"""
    result = await payment_service.cancel_subscription(current_user.id)
    return success_response(result)


@router.post("/subscription/webhook")
async def handle_payment_webhook(request: Request):
    """处理支付Webhook"""
    signature = request.headers.get("stripe-signature")
    if not signature:
        return error_response(ErrCode.INVALID_REQUEST, custom_message="缺少stripe-signature头")

    payload = await request.body()
    result = await payment_service.handle_webhook(payload, signature)

    return success_response(result)


# API密钥管理
@router.post("/subscription/api-keys")
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """创建API密钥"""
    result = await api_key_service.create_api_key(
        user_id=current_user.id,
        name=request.name,
        ip_whitelist=request.ip_whitelist,
        rate_limit=request.rate_limit,
    )

    if result["success"]:
        return success_response({
            "api_key": result.get("api_key"),
            "key_id": result.get("key_id"),
            "name": result.get("name"),
            "rate_limit": result.get("rate_limit"),
            "ip_whitelist": result.get("ip_whitelist", [])
        })
    else:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message="创建API密钥失败")


@router.get("/subscription/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的API密钥列表"""
    # TODO: 从数据库获取密钥列表
    return success_response({"keys": [], "message": "请前往设置页面管理API密钥"})


@router.post("/subscription/api-keys/revoke")
async def revoke_api_key(
    request: KeyIdRequest,
    current_user: User = Depends(get_current_user)
):
    """撤销API密钥"""
    success = await api_key_service.revoke_api_key(request.key_id, current_user.id)
    if success:
        return success_response({"success": True, "message": "API密钥已撤销"})
    else:
        return error_response(ErrCode.INTERNAL_ERROR, custom_message="撤销API密钥失败")


@router.get("/subscription/payment/status")
async def get_payment_service_status():
    """获取支付服务状态"""
    return success_response({
        "payment_service": payment_service.get_status(),
        "api_key_service": api_key_service.get_status(),
    })
