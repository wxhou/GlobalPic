import api from './auth'

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

export const subscriptionApi = {
  // 获取订阅套餐列表
  getPlans: (): Promise<{ data: SubscriptionPlan[] }> => {
    return api.get('/subscription/plans')
  },

  // 获取额度包列表
  getCreditPackages: (): Promise<{ data: CreditPackage[] }> => {
    return api.get('/subscription/credits')
  },

  // 创建订阅Checkout Session
  createCheckout: (planId: string, billingCycle: 'monthly' | 'yearly') => {
    return api.post('/subscription/create-checkout', { plan_id: planId, billing_cycle: billingCycle })
  },

  // 创建额度购买Checkout Session
  createCreditCheckout: (packageId: string) => {
    return api.post('/subscription/create-credit-checkout', { package_id: packageId })
  },

  // 获取订阅状态
  getStatus: (): Promise<{ data: SubscriptionStatus }> => {
    return api.get('/subscription/status')
  },

  // 取消订阅
  cancel: () => {
    return api.post('/subscription/cancel')
  },

  // 获取使用统计
  getUsageStats: (): Promise<{ data: UsageStats }> => {
    return api.get('/subscription/usage')
  },

  // ===== API Key 管理 =====

  // 创建API Key
  createAPIKey: (name: string): Promise<{ data: { key: string; api_key: APIKey } }> => {
    return api.post('/subscription/api-keys', { name })
  },

  // 获取API Key列表
  getAPIKeys: (): Promise<{ data: APIKey[] }> => {
    return api.get('/subscription/api-keys')
  },

  // 删除API Key
  deleteAPIKey: (keyId: string) => {
    return api.delete(`/subscription/api-keys/${keyId}`)
  },
}

export default subscriptionApi
