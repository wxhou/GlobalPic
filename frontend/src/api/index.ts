import axios, { AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ErrCode, UnifiedResponse, APIError } from './types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理统一响应格式
api.interceptors.response.use(
  (response: AxiosResponse<UnifiedResponse>) => {
    const { errcode, errmsg, data } = response.data
    
    // 如果 errcode 为 0，表示成功
    if (errcode === ErrCode.SUCCESS) {
      return response
    }
    
    // 处理错误响应
    const error: APIError = {
      errcode,
      errmsg,
      data
    }
    
    // 根据错误码进行特殊处理
    if (errcode === ErrCode.UNAUTHORIZED || errcode === ErrCode.TOKEN_INVALID || errcode === ErrCode.TOKEN_EXPIRED) {
      // Token 无效或过期，清除本地存储并跳转到登录页
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      
      // 如果不是在登录页，则跳转
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  },
  async (error) => {
    // 处理 HTTP 错误状态码
    if (error.response) {
      const { status, data } = error.response
      
      // 将 HTTP 错误转换为统一错误格式
      let errcode = ErrCode.INTERNAL_ERROR
      let errmsg = '请求失败'
      
      switch (status) {
        case 400:
          errcode = ErrCode.INVALID_REQUEST
          errmsg = data?.errmsg || '请求参数错误'
          break
        case 401:
          errcode = ErrCode.UNAUTHORIZED
          errmsg = data?.errmsg || '未登录或登录已过期'
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login'
          }
          break
        case 403:
          errcode = ErrCode.PERMISSION_DENIED
          errmsg = data?.errmsg || '没有权限'
          break
        case 404:
          errcode = ErrCode.NOT_FOUND
          errmsg = data?.errmsg || '资源不存在'
          break
        case 422:
          errcode = ErrCode.VALIDATION_ERROR
          errmsg = data?.errmsg || '数据验证失败'
          break
        case 429:
          errcode = ErrCode.RATE_LIMITED
          errmsg = data?.errmsg || '请求过于频繁'
          break
        case 500:
          errcode = ErrCode.INTERNAL_ERROR
          errmsg = data?.errmsg || '服务器内部错误'
          break
        case 502:
        case 503:
          errcode = ErrCode.EXTERNAL_SERVICE_ERROR
          errmsg = data?.errmsg || '服务暂时不可用'
          break
      }
      
      const apiError: APIError = {
        errcode,
        errmsg,
        data: data?.data
      }
      
      return Promise.reject(apiError)
    }
    
    // 处理网络错误
    if (error.request) {
      const networkError: APIError = {
        errcode: ErrCode.INTERNAL_ERROR,
        errmsg: '网络连接失败，请检查网络设置'
      }
      return Promise.reject(networkError)
    }
    
    return Promise.reject(error)
  }
)

// 工具函数：从响应中提取数据
export function extractData<T>(response: AxiosResponse<UnifiedResponse<T>>): T | null {
  if (response.data.errcode === ErrCode.SUCCESS) {
    return response.data.data || null
  }
  return null
}

// 工具函数：检查响应是否成功
export function isSuccess(response: AxiosResponse<UnifiedResponse>): boolean {
  return response.data.errcode === ErrCode.SUCCESS
}

// 工具函数：获取错误消息
export function getErrorMessage(error: APIError): string {
  return error.errmsg || '操作失败'
}

export default api
