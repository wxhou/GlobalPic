import api from './auth'

// 批量处理相关API

export interface BatchCreateRequest {
  images: Array<{ image: string; filename?: string }>
  operations: string[]
  style_id?: string
}

export interface BatchTaskStatus {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  total_images: number
  processed_images: number
  failed_images: number
  success_count: number
  estimated_time_remaining?: number
  created_at?: string
  completed_at?: string
}

export interface BatchResult {
  task_id: string
  status: string
  results: Array<{
    image_id: number
    original_filename: string
    operation_results: Array<{
      operation_type: string
      output_urls: string[]
      quality_score: number
    }>
  }>
  errors: Array<{
    image_id: number
    error: string
  }>
  success_count: number
  failed_count: number
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

  // 获取任务状态 (使用 query 参数)
  getStatus: (taskId: string): Promise<{ data: BatchTaskStatus }> => {
    return api.get('/batch/status', { params: { task_id: taskId } })
  },

  // 获取任务结果 (使用 query 参数)
  getResults: (taskId: string): Promise<{ data: BatchResult }> => {
    return api.get('/batch/results', { params: { task_id: taskId } })
  },

  // 下载结果ZIP包 (使用 query 参数)
  download: (taskId: string): Promise<{ data: BatchDownloadPackage }> => {
    return api.get('/batch/download', { params: { task_id: taskId } })
  },

  // 取消任务 (使用 POST + body)
  cancel: (taskId: string) => {
    return api.post('/batch/cancel', { task_id: taskId })
  },

  // 获取批量处理器状态
  getProcessorStatus: () => {
    return api.get('/batch/processor-status')
  },
}

export default batchApi
