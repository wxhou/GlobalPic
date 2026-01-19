import api, { extractData } from './index'
import { UnifiedResponse } from './types'

// 订阅和支付相关API

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
  user_id: number
  plan: string
  status: 'active' | 'cancelled' | 'past_due' | 'none'
  images_used: number
  images_limit: string
  credits_remaining: number
  subscription_end?: string
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

export interface APIKeyResponse {
  api_key: string
  key_id: string
  name: string
  rate_limit: number
  ip_whitelist: string[]
}

export interface PaymentStatus {
  payment_service: {
    stripe_configured: boolean
    test_mode: boolean
    public_key?: string
  }
  api_key_service: {
    enabled: boolean
    total_keys: number
  }
}

// Stripe Checkout Session 响应
export interface CheckoutSessionResponse {
  session_id: string
  url: string
  expires_at: string
}

// 取消订阅响应
export interface CancelSubscriptionResponse {
  cancelled: boolean
  effective_date: string
  message: string

export const subscriptionApi = {
  // 获取订阅套餐列表
  getPlans: async (): Promise<{ plans: SubscriptionPlan[] }> => {
    const response = await api.get<UnifiedResponse<{ plans: SubscriptionPlan[] }>>(
      '/subscription/plans'
    )
    return extractData(response) as { plans: SubscriptionPlan[] }
  },

  // 获取额度包列表
  getCreditPackages: async (): Promise<{ packages: CreditPackage[] }> => {
    const response = await api.get<UnifiedResponse<{ packages: CreditPackage[] }>>(
      '/subscription/credits'
    )
    return extractData(response) as { packages: CreditPackage[] }
  },

  // 创建订阅Checkout Session
  createCheckout: async (
    planId: string,
    billingCycle: 'subscription'
  ): Promise<CheckoutSessionResponse> => {
    const response = await api.post<UnifiedResponse<CheckoutSessionResponse>>(
      '/subscription/create-checkout',
      { plan_id: planId, mode: billingCycle }
    )
    return extractData(response) as CheckoutSessionResponse
  },

  // 创建额度购买Checkout Session
  createCreditCheckout: async (packageIndex: number): Promise<CheckoutSessionResponse> => {
    const response = await api.post<UnifiedResponse<CheckoutSessionResponse>>(
      '/subscription/create-credit-checkout',
      { package_index: packageIndex }
    )
    return extractData(response) as CheckoutSessionResponse
  },

  // 获取订阅状态
  getStatus: async (): Promise<SubscriptionStatus> => {
    const response = await api.get<UnifiedResponse<SubscriptionStatus>>('/subscription/status')
    return extractData<SubscriptionStatus>(response) as SubscriptionStatus
  },

  // 取消订阅
  cancel: async (): Promise<CancelSubscriptionResponse> => {
    const response = await api.post<UnifiedResponse<CancelSubscriptionResponse>>(
      '/subscription/cancel'
    )
    return extractData(response) as CancelSubscriptionResponse
  },

  // ===== API Key 管理 =====

  // 创建API Key
  createAPIKey: async (name: string): Promise<APIKeyResponse> => {
    const response = await api.post<UnifiedResponse<APIKeyResponse>>(
      '/subscription/api-keys',
      { name }
    )
    return extractData<APIKeyResponse>(response) as APIKeyResponse
  },

  // 获取API Key列表
  getAPIKeys: async (): Promise<{ keys: APIKey[] }> => {
    const response = await api.get<UnifiedResponse<{ keys: APIKey[] }>>(
      '/subscription/api-keys'
    )
    return extractData(response) as { keys: APIKey[] }
  },

  // 撤销API Key
  revokeAPIKey: async (keyId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post<UnifiedResponse<{ success: boolean; message: string }>>(
      '/subscription/api-keys/revoke',
      { key_id: keyId }
    )
    return extractData(response) as { success: boolean; message: string }
  },

  // 获取支付服务状态
  getPaymentStatus: async (): Promise<PaymentStatus> => {
    const response = await api.get<UnifiedResponse<PaymentStatus>>(
      '/subscription/payment/status'
    )
    return extractData<PaymentStatus>(response) as PaymentStatus
  },
}

export default subscriptionApi
