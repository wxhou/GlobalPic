// API类型定义

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
  detail: string
  code?: string
}
