<template>
  <router-view />
  <ErrorHandler />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import ErrorHandler from './components/ErrorHandler.vue'

const authStore = useAuthStore()

onMounted(() => {
  // Check if user is already logged in
  authStore.checkAuth()
})
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100vh;
}
</style>
