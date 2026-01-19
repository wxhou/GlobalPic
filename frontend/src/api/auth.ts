import api, { extractData } from './index'
import { User, AuthTokens, APIError } from './types'

interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

interface RegisterResponse {
  message: string
  email: string
}

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await api.post('/auth/login', { email, password })
    const data = extractData<LoginResponse>(response)
    if (data) {
      // 保存 token
      localStorage.setItem('access_token', data.access_token)
    }
    return data as LoginResponse
  },

  register: async (email: string, password: string, name: string): Promise<RegisterResponse> => {
    const response = await api.post('/auth/register', { email, password, name })
    return extractData<RegisterResponse>(response) as RegisterResponse
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me')
    return extractData<User>(response) as User
  },

  verifyToken: async (): Promise<{ valid: boolean; user_id: number; email: string }> => {
    const response = await api.get('/auth/verify-token')
    return extractData(response) as { valid: boolean; user_id: number; email: string }
  },

  logout: async (): Promise<void> => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    await api.post('/auth/logout')
  },
}

export default authApi
