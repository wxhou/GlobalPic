import api from './auth'

// 批量处理相关API

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

export const batchApi = {
  // 创建批量处理任务
  create: (data: BatchCreateRequest) => {
    return api.post('/batch/create', data)
  },

  // 获取任务状态
  getStatus: (taskId: string): Promise<{ data: BatchTaskStatus }> => {
    return api.get(`/batch/${taskId}/status`)
  },

  // 获取任务结果
  getResults: (taskId: string): Promise<{ data: BatchResult[] }> => {
    return api.get(`/batch/${taskId}/results`)
  },

  // 下载结果ZIP包
  download: (taskId: string): Promise<{ data: BatchDownloadPackage }> => {
    return api.get(`/batch/${taskId}/download`)
  },

  // 取消任务
  cancel: (taskId: string) => {
    return api.delete(`/batch/${taskId}`)
  },

  // 列出用户的所有批量任务
  list: (params?: { page?: number; limit?: number; status?: string }) => {
    return api.get('/batch/', { params })
  },
}

export default batchApi
