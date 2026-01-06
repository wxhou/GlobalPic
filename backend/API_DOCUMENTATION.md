# GlobalPic API Documentation

## Overview

GlobalPic 提供了一套完整的 AI 图像处理 API，支持图像生成、文字抹除、背景替换、文案生成等功能。

## Base URL

```
Production: https://api.globalpic.io/v1
Development: http://localhost:8000/api/v1
```

## Authentication

### Bearer Token Authentication

所有 API 需要在请求头中携带 JWT token：

```http
Authorization: Bearer <your_access_token>
```

### Getting Started

1. 注册账户获取 API Key（可选，用于 API 访问）
2. 使用邮箱密码获取 access_token
3. 在请求头中携带 token

## API Endpoints

### Authentication

#### POST /api/v1/auth/login

用户登录

**Request:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### POST /api/v1/auth/register

用户注册

**Request:**
```json
{
  "email": "user@example.com",
  "password": "your_password",
  "full_name": "Your Name"
}
```

#### GET /api/v1/auth/me

获取当前用户信息

---

### Image Processing

#### POST /api/v1/images/process

处理图像

**Request:**
```json
{
  "image_id": 123,
  "operation_type": "text_removal",
  "parameters": {}
}
```

**Response:**
```json
{
  "success": true,
  "processing_time": 15.5,
  "result": {
    "output_urls": [
      "https://storage.globalpic.io/results/xxx_1.jpg"
    ],
    "quality_score": 0.95,
    "text_regions_found": 3
  }
}
```

#### GET /api/v1/images/processing/status

获取 AI 模型状态

**Response:**
```json
{
  "models_loaded": true,
  "model_status": {
    "zimage_turbo": true,
    "sam": true,
    "easyocr": true
  },
  "supported_operations": ["text_removal", "background_replacement"]
}
```

---

### Resize API

#### GET /api/v1/resize/presets

获取平台尺寸预设列表

**Query Parameters:**
- `category` (optional): 筛选特定分类

**Response:**
```json
[
  {
    "id": "amazon_primary",
    "name": "亚马逊主图",
    "width": 1000,
    "height": 1000,
    "description": "亚马逊主图标准尺寸"
  }
]
```

#### POST /api/v1/images/{image_id}/resize

调整图片尺寸

**Request:**
```json
{
  "width": 800,
  "height": 800,
  "maintain_aspect_ratio": true,
  "resample_method": "lanczos",
  "fit_mode": "contain",
  "background_color": "#FFFFFF"
}
```

---

### Copywriting API

#### POST /api/v1/copywriting/generate

生成营销文案

**Request:**
```json
{
  "image_id": 123,
  "product_description": "A red dress made of silk",
  "platform": "amazon",
  "count": 3,
  "keywords": ["elegant", "formal"],
  "tone": "professional"
}
```

**Response:**
```json
{
  "success": true,
  "copywrites": [
    {
      "id": "1",
      "content": "Elegant silk dress for formal occasions...",
      "platform": "amazon",
      "keywords": ["elegant", "silk", "formal"],
      "character_count": 150
    }
  ],
  "usage_tips": [
    "Include product dimensions in description",
    "Add care instructions"
  ]
}
```

#### GET /api/v1/copywriting/platforms

获取支持的平台列表

---

### Batch Processing API

#### POST /api/v1/batch/create

创建批量处理任务

**Request:**
```json
{
  "image_ids": [1, 2, 3, 4, 5],
  "operations": ["text_removal", "background_replacement"],
  "style_id": "minimal_white"
}
```

**Response:**
```json
{
  "task_id": "batch_abc123",
  "status": "pending",
  "estimated_time": 120
}
```

#### GET /api/v1/batch/{task_id}/status

获取任务状态

**Response:**
```json
{
  "task_id": "batch_abc123",
  "status": "processing",
  "progress": 45,
  "total_images": 5,
  "processed_images": 2,
  "failed_images": 0
}
```

#### GET /api/v1/batch/{task_id}/download

下载处理结果（ZIP包）

---

### Subscription API

#### GET /api/v1/subscription/plans

获取订阅套餐列表

**Response:**
```json
[
  {
    "id": "personal",
    "name": "Personal",
    "price_monthly": 19.99,
    "price_yearly": 199.99,
    "features": ["Unlimited processing", "Priority support"],
    "limits": {
      "images_per_month": 500,
      "batch_size": 20,
      "api_access": true
    }
  }
]
```

#### POST /api/v1/subscription/create-checkout

创建订阅 Checkout Session

**Request:**
```json
{
  "plan_id": "personal",
  "billing_cycle": "monthly"
}
```

#### GET /api/v1/subscription/status

获取当前订阅状态

**Response:**
```json
{
  "plan_id": "personal",
  "plan_name": "Personal",
  "status": "active",
  "images_used": 120,
  "images_limit": 500,
  "credits_remaining": 0,
  "renewal_date": "2025-02-01"
}
```

#### POST /api/v1/subscription/api-keys

创建 API Key

**Request:**
```json
{
  "name": "My API Key"
}
```

**Response:**
```json
{
  "key": "gp_live_abc123xyz...",
  "api_key": {
    "id": "1",
    "name": "My API Key",
    "key_prefix": "gp_live_",
    "rate_limit": 100
  }
}
```

**注意:** API Key 只显示一次，请妥善保管

---

## Rate Limiting

| Plan | Requests/minute |
|------|-----------------|
| Free | 10 |
| Personal | 100 |
| Enterprise | 1000 |

## Error Handling

### Error Response Format

```json
{
  "detail": "Error description",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| AUTH_REQUIRED | 401 | Authentication required |
| INVALID_TOKEN | 401 | Invalid or expired token |
| QUOTA_EXCEEDED | 403 | Monthly quota exceeded |
| RATE_LIMITED | 429 | Too many requests |
| MODEL_NOT_LOADED | 503 | AI model not ready |

## SDKs

### Python

```python
pip install globalpic-sdk
```

```python
from globalpic import GlobalPic

client = GlobalPic(api_key="your_api_key")

# 处理图片
result = client.images.process(
    image_id=123,
    operation_type="text_removal"
)

# 生成文案
copywrites = client.copywriting.generate(
    product_description="A red dress",
    platform="amazon",
    count=3
)
```

### JavaScript/TypeScript

```bash
npm install @globalpic/sdk
```

```typescript
import { GlobalPic } from '@globalpic/sdk'

const client = new GlobalPic({ apiKey: 'your_api_key' })

// 处理图片
const result = await client.images.process({
  imageId: 123,
  operationType: 'text_removal'
})
```

## Webhooks

### Stripe Webhook

Endpoint: POST /api/v1/subscription/webhook

Events:
- `checkout.session.completed`
- `invoice.paid`
- `invoice.payment_failed`
- `customer.subscription.updated`
- `customer.subscription.deleted`

## Support

- Email: support@globalpic.io
- Documentation: https://docs.globalpic.io
