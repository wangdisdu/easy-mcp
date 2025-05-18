<template>
  <!-- This is an invisible component that handles global errors -->
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import router from '../router'

// Global error handler for uncaught exceptions
const handleGlobalError = (event) => {
  const error = event.error || event.reason

  // Skip if already handled or if it's not an error object
  if (!error || error.errorHandled) {
    return
  }

  console.error('Uncaught error:', error)
  error.errorHandled = true // Mark as handled to prevent duplicate handling

  // If the error has a response property, it's likely an API error
  if (error.response) {
    const status = error.response.status
    const errorMsg = error.response.data?.message || '未知错误'

    // Handle 400 Bad Request
    if (status === 400) {
      message.error(`请求错误: ${errorMsg}`)
    }
    // Handle 401 Unauthorized
    else if (status === 401) {
      message.error('登录已过期，请重新登录')
      router.push('/login')
    }
    // Handle other HTTP errors
    else if (status >= 400) {
      message.error(`服务器错误 (${status}): ${errorMsg}`)
    }
  } else {
    // For non-HTTP errors, show a generic message
    message.error('应用程序错误: ' + (error.message || '未知错误'))
  }
}

// Set up event listeners
onMounted(() => {
  window.addEventListener('error', handleGlobalError)
  window.addEventListener('unhandledrejection', handleGlobalError)
})

// Clean up event listeners
onUnmounted(() => {
  window.removeEventListener('error', handleGlobalError)
  window.removeEventListener('unhandledrejection', handleGlobalError)
})
</script>
