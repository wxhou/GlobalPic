import api, { extractData } from './index'
import { UnifiedResponse } from './types'

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

export interface BatchCreateResponse {
  success: boolean
  task_id: string
  status: string
  total_images: number
  estimated_time: number
}

export const batchApi = {
  // 创建批量处理任务
  create: async (data: BatchCreateRequest): Promise<BatchCreateResponse> => {
    const response = await api.post<UnifiedResponse<BatchCreateResponse>>('/batch/create', data)
    return extractData<BatchCreateResponse>(response) as BatchCreateResponse
  },

  // 获取任务状态
  getStatus: async (taskId: string): Promise<BatchTaskStatus> => {
    const response = await api.get<UnifiedResponse<BatchTaskStatus>>('/batch/status', {
      params: { task_id: taskId },
    })
    return extractData<BatchTaskStatus>(response) as BatchTaskStatus
  },

  // 获取任务结果
  getResults: async (taskId: string): Promise<BatchResult> => {
    const response = await api.get<UnifiedResponse<BatchResult>>('/batch/results', {
      params: { task_id: taskId },
    })
    return extractData<BatchResult>(response) as BatchResult
  },

  // 取消任务
  cancel: async (taskId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post<UnifiedResponse<{ success: boolean; message: string }>>(
      '/batch/cancel',
      { task_id: taskId }
    )
    return extractData(response) as { success: boolean; message: string }
  },

  // 获取批量处理器状态
  getProcessorStatus: async (): Promise<Record<string, unknown>> => {
    const response = await api.get<UnifiedResponse<Record<string, unknown>>>(
      '/batch/processor-status'
    )
    return extractData(response) as Record<string, unknown>
  },
}

export default batchApi
