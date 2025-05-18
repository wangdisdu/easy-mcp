import axios from 'axios'
import { message } from 'ant-design-vue'
import router from '../router'

/**
 * Configure axios with interceptors for global error handling
 *
 * @returns {Object} - Configured axios instance
 */
export const configureAxios = () => {
  // Response interceptor for handling errors
  axios.interceptors.response.use(
    (response) => {
      // If the response is successful but the API returns an error code
      if (response.data && response.data.code !== 0) {
        const errorMsg = response.data.message || '未知错误'

        // Create an error object with the response for further handling
        const error = new Error(errorMsg)
        error.response = response
        error.isApiError = true // Mark as API error for handling in callApi
        throw error
      }

      return response
    },
    (error) => {
      // Skip if already handled
      if (error.errorHandled) {
        return Promise.reject(error)
      }

      // Handle HTTP errors
      if (error.response) {
        // Handle 401 Unauthorized errors - redirect to login
        if (error.response.status === 401) {
          // Clear any auth data
          localStorage.removeItem('token')
          localStorage.removeItem('user')

          // Remove auth header
          delete axios.defaults.headers.common['Authorization']

          // Show message
          message.error('登录已过期，请重新登录')

          // Redirect to login page
          router.push('/login')

          // Mark as handled
          error.errorHandled = true
        }
        // Handle 400 Bad Request errors - show detailed error message
        else if (error.response.status === 400) {
          const errorMsg = error.response.data?.message || '请求参数错误'
          message.error(errorMsg)

          // Mark as handled
          error.errorHandled = true
        }
      }

      return Promise.reject(error)
    }
  )

  return axios
}

// Export configured axios
export default configureAxios()
