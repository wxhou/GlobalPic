// API类型定义

// ============ 统一响应格式 ============

/**
 * 统一API响应格式
 * 所有接口都返回此格式：
 * {"errcode": 0, "errmsg": "success", "data": {...}}
 */
export interface UnifiedResponse<T = unknown> {
  errcode: number  // 0表示成功，非0表示错误
  errmsg: string  // 错误消息，成功时为"success"
  data?: T        // 响应数据
}

// ============ 错误码定义 ============

export enum ErrCode {
  SUCCESS = 0,
  
  // 通用错误 1xxx
  INVALID_REQUEST = 1001,
  NOT_FOUND = 1002,
  PERMISSION_DENIED = 1003,
  RATE_LIMITED = 1004,
  VALIDATION_ERROR = 1005,
  
  // 认证错误 2xxx
  UNAUTHORIZED = 2001,
  TOKEN_INVALID = 2002,
  TOKEN_EXPIRED = 2003,
  USER_NOT_VERIFIED = 2004,
  INCORRECT_PASSWORD = 2005,
  EMAIL_NOT_REGISTERED = 2006,
  EMAIL_ALREADY_EXISTS = 2007,
  
  // 业务错误 3xxx
  FILE_TOO_LARGE = 3001,
  INVALID_FILE_FORMAT = 3002,
  IMAGE_NOT_FOUND = 3003,
  PROCESSING_FAILED = 3004,
  INSUFFICIENT_CREDITS = 3005,
  BATCH_LIMIT_EXCEEDED = 3006,
  OPERATION_NOT_ALLOWED = 3007,
  
  // 系统错误 4xxx
  INTERNAL_ERROR = 4001,
  DATABASE_ERROR = 4002,
  EXTERNAL_SERVICE_ERROR = 4003,
}

// ============ 图片处理类型 ============

export interface ImageProcessingRequest {
  image_id: number
  operation_type: 'text_removal' | 'background_replacement' | 'resize'
  parameters: Record<string, unknown>
}

export interface ImageProcessingResponse {
  success: boolean
  processing_time: number
  result?: {
    output_urls: string[]
    quality_score: number
    // 允许额外的属性，但提供类型安全的访问方式
    [key: string]: unknown
  }
  error?: string
}

export interface ResizeParams {
  width: number
  height: number
  maintain_aspect_ratio?: boolean
  resample_method?: 'lanczos' | 'bilinear' | 'bicubic' | 'nearest'
  fit_mode?: 'cover' | 'contain' | 'fill' | 'stretch'
  background_color?: string
}

export interface PlatformPreset {
  id: string
  name: string
  width: number
  height: number
  description: string
}

// ============ 文案生成类型 ============

export interface CopywritingRequest {
  image_id?: number
  product_description?: string
  platform: string
  count?: number
  keywords?: string[]
  tone?: 'professional' | 'casual' | 'persuasive' | 'friendly'
}

export interface CopywritingResponse {
  success: boolean
  copywrites: Array<{
    id: string
    content: string
    platform: string
    keywords: string[]
    character_count: number
  }>
  usage_tips?: string[]
  error?: string
}

export interface Platform {
  id: string
  name: string
  description: string
  max_length: number
  features: string[]
}

// ============ 批量处理类型 ============

export interface BatchCreateRequest {
  image_ids: number[]
  operations: string[]
  style_id?: string
  parameters?: Record<string, unknown>
}

export interface BatchTaskStatus {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  total_images: number
  processed_images: number
  failed_images: number
  estimated_time_remaining?: number
  created_at: string
  updated_at: string
}

export interface BatchResult {
  image_id: number
  original_filename: string
  results: Array<{
    operation_type: string
    output_urls: string[]
    quality_score: number
  }>
}

export interface BatchDownloadPackage {
  download_url: string
  expires_at: string
  file_size: number
  file_count: number
}

// ============ 订阅和支付类型 ============

export interface SubscriptionPlan {
  id: string
  name: string
  description: string
  price_monthly: number
  price_yearly: number
  currency: string
  features: string[]
  limits: {
    images_per_month: number
    batch_size: number
    background_removal: boolean
    text_removal: boolean
    priority_support: boolean
    api_access: boolean
  }
  popular?: boolean
}

export interface CreditPackage {
  id: string
  name: string
  credits: number
  price: number
  currency: string
  description: string
}

export interface SubscriptionStatus {
  plan_id: string | null
  plan_name: string | null
  status: 'active' | 'cancelled' | 'past_due' | 'none'
  images_used: number
  images_limit: number
  credits_remaining: number
  renewal_date: string | null
  cancel_at_period_end: boolean
}

export interface UsageStats {
  today: { used: number; limit: number }
  this_month: { used: number; limit: number }
  credits_remaining: number
}

export interface APIKey {
  id: string
  name: string
  key_prefix: string
  created_at: string
  last_used_at: string | null
  usage_count: number
  rate_limit: number
}

// ============ 用户类型 ============

export interface User {
  id: number
  email: string
  full_name: string | null
  is_verified: boolean
  created_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

// ============ 错误类型 ============

export interface APIError {
  errcode: number
  errmsg: string
  data?: unknown
}
