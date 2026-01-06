# Payment & Subscription Specification

## ADDED Requirements

### Requirement: 订阅套餐管理
系统 MUST 支持三种订阅套餐

#### Scenario: 套餐定义
**Given** 系统初始化
**When** 加载订阅配置
**Then** 定义三种套餐:
- 免费版: 3张图片试用
- 个人版: $19/月无限量
- 企业版: $99/月 + API访问

#### Scenario: 套餐切换
**Given** 用户升级订阅
**When** 完成支付
**Then** 更新用户套餐类型
**And** 设置续费日期
**And** 发送确认邮件

### Requirement: 支付集成
系统 MUST 集成Stripe处理支付

#### Scenario: 订阅购买
**Given** 用户选择个人版 ($19/月)
**When** 创建订阅checkout
**Then** 跳转Stripe支付页面
**And** 支付成功后创建订阅
**And** 设置每月自动续费

#### Scenario: 按需购买
**Given** 用户选择10张图片包
**When** 创建一次性支付
**Then** 跳转Stripe支付
**And** 支付成功后增加额度
**And** 额度永不过期

#### Scenario: Webhook处理
**Given** Stripe发送webhook
**When** 收到支付事件
**Then** 验证签名
**And** 更新订阅状态
**And** 记录交易日志

### Requirement: 用量追踪
系统 MUST 准确追踪用户用量

#### Scenario: 处理次数扣减
**Given** 用户提交处理请求
**When** 检查用户配额
**Then** 订阅用户: 无限制
**And** 按需用户: 扣减配额
**And** 免费用户: 检查试用次数

#### Scenario: 用量查询
**Given** 用户查看账户信息
**When** 调用用量查询API
**Then** 返回已使用次数
**And** 返回剩余配额
**And** 返回账单周期

### Requirement: 企业版API访问
企业版用户 MUST 可以通过API Key访问服务

#### Scenario: API Key生成
**Given** 企业版用户请求API Key
**When** 创建新的API Key
**Then** 生成唯一密钥
**And** 设置使用限制
**And** 返回密钥(只显示一次)

#### Scenario: API认证
**Given** 用户使用API Key调用
**When** 验证密钥有效性
**Then** 检查IP白名单
**And** 检查调用频率
**And** 扣减对应配额

#### Scenario: API管理
**Given** 企业用户管理API Keys
**When** 查看/删除/更新密钥
**Then** 支持多个密钥
**And** 支持设置过期时间
**And** 支持设置IP白名单

## MODIFIED Requirements

### Requirement: user-authentication: 订阅管理
用户认证系统 MUST 支持订阅状态和配额管理

#### ADDED: Subscription Models
```python
class Subscription(BaseModel):
    """用户订阅模型"""
    id: int
    user_id: int
    plan: str  # free, personal, enterprise
    status: str  # active, canceled, past_due
    current_period_start: datetime
    current_period_end: datetime
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    api_quota: int  # 企业版API配额
    api_quota_used: int

class UsageRecord(BaseModel):
    """用量记录模型"""
    id: int
    user_id: int
    operation_type: str
    image_count: int
    quota_used: int
    created_at: datetime
```

#### ADDED: Payment Service
```python
class PaymentService:
    """支付服务"""

    def __init__(self, db: Database):
        self.db = db
        self.stripe = StripeClient(settings.STRIPE_SECRET_KEY)

    async def create_checkout_session(
        self,
        user_id: int,
        price_id: str,
        mode: str = "subscription"
    ) -> str:
        """创建Stripe checkout会话"""
        user = await self.db.get_user(user_id)
        session = self.stripe.checkout.sessions.create(
            customer_email=user.email,
            line_items=[{"price": price_id, "quantity": 1}],
            mode=mode,
            success_url=f"{settings.DOMAIN}/payment/success",
            cancel_url=f"{settings.DOMAIN}/payment/cancel",
            metadata={"user_id": str(user_id)}
        )
        return session.url

    async def handle_webhook(self, payload: bytes, signature: str):
        """处理Stripe webhook"""
        event = self.stripe.webhooks.construct_event(
            payload, signature, settings.STRIPE_WEBHOOK_SECRET
        )

        if event["type"] == "checkout.session.completed":
            await self._handle_checkout_complete(event["data"]["object"])
        elif event["type"] == "customer.subscription.updated":
            await self._handle_subscription_update(event["data"]["object"])
        # ... 其他事件处理
```

#### ADDED: API Key Service
```python
class APIKeyService:
    """API密钥服务"""

    async def create_api_key(
        self,
        user_id: int,
        name: str,
        ip_whitelist: List[str] = None,
        rate_limit: int = 100
    ) -> APIKey:
        """创建API密钥"""
        key = APIKey(
            key=self._generate_key(),
            user_id=user_id,
            name=name,
            ip_whitelist=ip_whitelist,
            rate_limit=rate_limit,
            is_active=True
        )
        await self.db.create(key)
        return key

    async def validate_key(
        self,
        api_key: str,
        client_ip: str
    ) -> Tuple[bool, Optional[User]]:
        """验证API密钥"""
        key = await self.db.get_api_key(api_key)
        if not key or not key.is_active:
            return False, None
        if key.ip_whitelist and client_ip not in key.ip_whitelist:
            return False, None
        return True, key.user
```

#### MODIFIED: User Schema
- 新增: subscription_plan 字段
- 新增: subscription_status 字段
- 新增: credit_balance 字段
- 新增: api_keys 关联
