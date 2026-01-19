import api, { extractData } from './index'
import { UnifiedResponse } from './types'

export interface ImageInfo {
  id: number
  original_filename: string
  filename: string
  file_size: number
  file_format: string
  storage_url: string
  created_at: string
}

export interface ImageUploadResponse {
  success: boolean
  message: string
  image: ImageInfo
}

export interface ImageListResponse {
  images: ImageInfo[]
  total: number
  page: number
  per_page: number
  has_next: boolean
  has_prev: boolean
}

export interface ProcessingJob {
  id: number
  image_id: number
  operation_type: string
  status: string
  parameters: Record<string, unknown>
  output_url: string | null
  quality_score: number | null
  created_at: string
  completed_at: string | null
}

export interface ProcessingJobCreateResponse {
  success: boolean
  message: string
  job: ProcessingJob
}

export interface DeleteImageRequest {
  image_id: number
}

export const imageApi = {
  // 上传单张图片
  uploadImage: async (file: File): Promise<ImageUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post<UnifiedResponse<ImageUploadResponse>>(
      '/images/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return extractData<ImageUploadResponse>(response) as ImageUploadResponse
  },

  // 批量上传图片
  uploadImagesBatch: async (files: File[]): Promise<{ results: ImageUploadResponse[] }> => {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })
    
    const response = await api.post<UnifiedResponse<{ results: ImageUploadResponse[] }>>(
      '/images/upload/batch',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return extractData(response) as { results: ImageUploadResponse[] }
  },

  // 获取图片列表
  getImages: async (page: number = 1, perPage: number = 20): Promise<ImageListResponse> => {
    const response = await api.get<UnifiedResponse<ImageListResponse>>('/images', {
      params: { page, per_page: perPage },
    })
    return extractData<ImageListResponse>(response) as ImageListResponse
  },

  // 获取图片详情
  getImageDetail: async (imageId: number): Promise<{ image: ImageInfo }> => {
    const response = await api.get<UnifiedResponse<{ image: ImageInfo }>>('/images/detail', {
      params: { image_id: imageId },
    })
    return extractData(response) as { image: ImageInfo }
  },

  // 删除图片
  deleteImage: async (imageId: number): Promise<{ success: boolean; message: string }> => {
    const response = await api.post<UnifiedResponse<{ success: boolean; message: string }>>(
      '/images/delete',
      { image_id: imageId }
    )
    return extractData(response) as { success: boolean; message: string }
  },

  // 创建处理任务
  createProcessingJob: async (
    imageId: number,
    operationType: string,
    parameters?: Record<string, unknown>
  ): Promise<ProcessingJobCreateResponse> => {
    const response = await api.post<UnifiedResponse<ProcessingJobCreateResponse>>(
      '/images/process',
      {
        image_id: imageId,
        operation_type: operationType,
        parameters,
      }
    )
    return extractData<ProcessingJobCreateResponse>(response) as ProcessingJobCreateResponse
  },

  // 获取处理任务状态
  getProcessingJob: async (jobId: number): Promise<{ job: ProcessingJob }> => {
    const response = await api.get<UnifiedResponse<{ job: ProcessingJob }>>(
      '/images/jobs',
      { params: { job_id: jobId } }
    )
    return extractData(response) as { job: ProcessingJob }
  },
}

export default imageApi
