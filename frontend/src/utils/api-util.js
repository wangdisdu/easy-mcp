import axios from 'axios'
import { message } from 'ant-design-vue'

/**
 * Call API with standard error handling
 *
 * @param {Object} options - API call options
 * @param {string} options.method - HTTP method
 * @param {string} options.url - API URL
 * @param {Object} [options.data] - Request data
 * @param {Object} [options.params] - Request parameters
 * @param {string} [options.successMessage] - Success message
 * @param {string} [options.errorMessage] - Error message
 * @param {Function} [options.onSuccess] - Success callback
 * @returns {Promise} - API response
 */
export const callApi = async (options) => {
  const {
    method,
    url,
    data,
    params,
    successMessage,
    errorMessage,
    onSuccess
  } = options

  try {
    const response = await axios({
      method,
      url,
      data,
      params
    })

    // Success handling
    if (successMessage) {
      message.success(successMessage)
    }

    if (onSuccess) {
      onSuccess(response.data.data, response.data)
    }

    return response.data
  } catch (error) {
    // If the error wasn't already handled by interceptors
    if (!error.errorHandled && !error.isApiError) {
      // Only show generic error message if not already handled
      message.error(errorMessage || '遇到错误：' + (error.message || '未知错误'))
      error.errorHandled = true
    }

    throw error
  }
}

/**
 * Validate form data
 *
 * @param {Object} form - Form data
 * @param {Array} requiredFields - Required fields
 * @returns {Object} - Validation result
 */
export const validateForm = (form, requiredFields) => {
  for (const field of requiredFields) {
    if (!form[field]) {
      return {
        valid: false,
        message: `请填写${field}字段`
      }
    }
  }

  return { valid: true }
}

/**
 * Validate JSON string
 *
 * @param {string} jsonString - JSON string
 * @returns {Object} - Validation result
 */
export const validateJson = (jsonString) => {
  try {
    JSON.parse(jsonString)
    return { valid: true }
  } catch (error) {
    return {
      valid: false,
      message: `JSON格式不正确: ${error.message}`
    }
  }
}

/**
 * Format timestamp to date string
 *
 * @param {number} timestamp - Unix timestamp in milliseconds
 * @returns {string} - Formatted date string
 */
export const formatTimestamp = (timestamp) => {
  if (!timestamp) return ''

  const date = new Date(timestamp)
  return date.toLocaleString()
}
