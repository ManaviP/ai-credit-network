import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      hydrated: false,

      setSession: (session) => {
        const accessToken = session?.access_token || null
        const refreshToken = session?.refresh_token || null
        const user = session?.user || null

        if (accessToken) {
          localStorage.setItem('access_token', accessToken)
        } else {
          localStorage.removeItem('access_token')
        }

        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken)
        } else {
          localStorage.removeItem('refresh_token')
        }

        set({
          accessToken,
          refreshToken,
          user,
          isAuthenticated: Boolean(user),
        })
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },

      setUser: (user) => set({ user, isAuthenticated: Boolean(user) }),
      setHydrated: (hydrated) => set({ hydrated }),
    }),
    {
      name: 'auth-storage',
      onRehydrateStorage: () => (state) => {
        state?.setHydrated?.(true)
      },
    }
  )
)
