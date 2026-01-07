import api from './auth'

// 图片处理相关API

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

export const imageApi = {
  // 上传图片
  upload: (formData: FormData) => {
    return api.post('/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // 获取图片列表
  list: (params?: { page?: number; per_page?: number }) => {
    return api.get('/images', { params })
  },

  // 获取单张图片
  get: (id: number) => {
    return api.get('/images/detail', { params: { image_id: id } })
  },

  // 删除图片 (使用 POST + body)
  delete: (id: number) => {
    return api.post('/images/delete', { image_id: id })
  },

  // 处理图片
  process: (data: ImageProcessingRequest) => {
    return api.post('/images/process', data)
  },

  // 获取处理状态
  getProcessingStatus: () => {
    return api.get('/images/processing/status')
  },

  // 获取支持的平台尺寸预设
  getPlatformPresets: (): Promise<{ data: PlatformPreset[] }> => {
    return api.get('/resize/presets')
  },

  // 调整图片尺寸 (使用 POST + body)
  resize: (imageId: number, params: ResizeParams) => {
    return api.post('/images/resize', { image_id: imageId, ...params })
  },

  // 获取图片历史记录
  getHistory: (params?: { page?: number; limit?: number }) => {
    return api.get('/images/history', { params })
  },
}

export default imageApi
