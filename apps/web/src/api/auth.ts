import apiClient from './client'

export interface LoginResponse {
  access: string
  refresh: string
}

export interface RegisterResponse {
  message: string
  user_id: string
  org_id: string
}

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post<LoginResponse>('/auth/token/', {
      username,
      password,
    })
    return response.data
  },

  register: async (data: {
    username: string
    password: string
    email: string
    org_name: string
  }) => {
    const response = await apiClient.post<RegisterResponse>('/auth/register/', data)
    return response.data
  },

  me: async () => {
    const response = await apiClient.get('/auth/me/')
    return response.data
  },
}
