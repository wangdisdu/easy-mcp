import { defineStore } from 'pinia'
import axios from 'axios'
import { message } from 'ant-design-vue'
import router from '../router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    checkAuth() {
      // Check if token exists and is valid
      if (this.token) {
        // Set axios default headers
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
      }
    },

    async login(username, password) {
      try {
        const response = await axios.post('/api/v1/auth/login', {
          username,
          password
        })

        // If we get here, the login was successful (errors are handled by interceptors)
        // Save token and user info
        this.token = response.data.data.token
        this.user = { username }

        // Save to localStorage
        localStorage.setItem('token', this.token)
        localStorage.setItem('user', JSON.stringify(this.user))

        // Set axios default headers
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`

        return true
      } catch (error) {
        // Error already handled by interceptor
        return false
      }
    },

    logout() {
      // Clear state
      this.token = null
      this.user = null

      // Clear localStorage
      localStorage.removeItem('token')
      localStorage.removeItem('user')

      // Clear axios default headers
      delete axios.defaults.headers.common['Authorization']

      // Redirect to login page
      router.push('/login')
    }
  }
})
