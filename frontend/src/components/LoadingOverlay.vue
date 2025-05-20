<template>
  <div v-if="loading" class="loading-overlay" :class="{ 'full-page': fullPage }">
    <a-spin :tip="tip">
      <template #indicator v-if="customIcon">
        <component :is="customIcon" spin />
      </template>
    </a-spin>
  </div>
</template>

<script setup>
import { LoadingOutlined } from '@ant-design/icons-vue'

defineProps({
  loading: {
    type: Boolean,
    default: true
  },
  tip: {
    type: String,
    default: '加载中...'
  },
  fullPage: {
    type: Boolean,
    default: false
  },
  customIcon: {
    type: Object,
    default: () => LoadingOutlined
  }
})
</script>

<style>
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.8);
  z-index: 1000;
}

.loading-overlay.full-page {
  position: fixed;
  z-index: 2000;
}
</style>
