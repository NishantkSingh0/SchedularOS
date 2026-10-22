import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: any | null
  isAuthenticated: boolean
  setTokens: (access: string, refresh: string) => void
  setUser: (user: any) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      setTokens: (access, refresh) => {
        localStorage.setItem('access_token', access)
        localStorage.setItem('refresh_token', refresh)
        set({
          accessToken: access,
          refreshToken: refresh,
          isAuthenticated: true,
        })
      },
      setUser: (user) => set({ user }),
      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        })
      },
    }),
    {
      name: 'auth-storage',
      onRehydrateStorage: () => (state) => {
        if (state?.accessToken) localStorage.setItem('access_token', state.accessToken)
        if (state?.refreshToken) localStorage.setItem('refresh_token', state.refreshToken)
      },
    }
  )
)
