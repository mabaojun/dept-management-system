import { defineStore } from 'pinia'
import { http } from '@/api/http'
import type { TokenOut, UserOut } from '@/api/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null') as UserOut | null,
  }),
  getters: {
    isManager: (s) => s.user?.role === 'admin' || s.user?.role === 'manager',
  },
  actions: {
    async login(username: string, password: string) {
      const data = await http.post<unknown, TokenOut>('/auth/login', {
        username,
        password,
      })
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
