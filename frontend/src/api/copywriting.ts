import api from './auth'

// 文案生成相关API

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

export const copywritingApi = {
  // 生成营销文案
  generate: (data: CopywritingRequest) => {
    return api.post('/copywriting/generate', data)
  },

  // 获取支持的平台列表
  getPlatforms: (): Promise<{ data: Platform[] }> => {
    return api.get('/copywriting/platforms')
  },

  // 获取服务状态
  getStatus: () => {
    return api.get('/copywriting/status')
  },
}

export default copywritingApi
