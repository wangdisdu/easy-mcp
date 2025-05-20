<template>
  <app-layout current-page-key="log">
    <a-card title="系统日志">
      <div class="log-container">
        <!-- 左侧日志文件列表 -->
        <div class="log-files-panel">
          <div class="panel-header">
            <h3>日志文件</h3>
            <a-button type="primary" size="small" @click="refreshLogs">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </div>

          <div class="log-files-list" :class="{ 'loading': loading }">
            <a-spin v-if="loading" />
            <template v-else>
              <a-empty v-if="logFiles.length === 0" description="没有找到日志文件" />
              <div
                v-for="file in logFiles"
                :key="file.name"
                class="log-file-card"
                :class="{ 'active': selectedLog && selectedLog.name === file.name }"
                @click="selectLog(file)"
              >
                <div class="log-file-info">
                  <div class="log-file-name">
                    <FileOutlined /> {{ file.name }}
                  </div>
                  <div class="log-file-meta">
                    <div>大小: {{ file.size_human }}</div>
                    <div>修改时间: {{ file.modified_at_human }}</div>
                  </div>
                </div>
                <!-- 日志文件下载功能已移除 -->
              </div>
            </template>
          </div>
        </div>

        <!-- 右侧日志内容显示 -->
        <div class="log-content-panel">
          <div v-if="!selectedLog" class="no-log-selected">
            <a-empty description="请选择一个日志文件查看" />
          </div>

          <div v-else class="log-content-container">
            <div class="panel-header">
              <h3>{{ selectedLog.name }}</h3>
              <div class="log-controls">
                <a-space>
                  <a-input-number
                    v-model:value="maxLines"
                    :min="100"
                    :max="10000"
                    :step="100"
                    size="small"
                    addon-before="行数"
                  />
                  <a-switch
                    v-model:checked="tailMode"
                    checked-children="末尾"
                    un-checked-children="开头"
                    size="small"
                  />
                  <a-button type="primary" size="small" @click="loadLogContent">
                    <template #icon><ReloadOutlined /></template>
                    刷新
                  </a-button>
                </a-space>
              </div>
            </div>

            <div class="log-info-bar">
              <span>总行数: {{ logContent.total_lines }}</span>
              <span>显示行数: {{ logContent.displayed_lines }}</span>
            </div>

            <div class="log-content-viewer">
              <a-spin v-if="contentLoading" />
              <pre v-else>{{ logContent.content }}</pre>
            </div>
          </div>
        </div>
      </div>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import {
  FileOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

// 状态变量
const loading = ref(false)
const contentLoading = ref(false)
const logFiles = ref([])
const selectedLog = ref(null)
const logContent = ref({
  content: '',
  total_lines: 0,
  displayed_lines: 0
})
const maxLines = ref(1000)
const tailMode = ref(true)

// 获取日志文件列表
const fetchLogFiles = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/log',
      onSuccess: (data) => {
        logFiles.value = data.files
      },
      errorMessage: '获取日志文件列表失败'
    })
  } finally {
    loading.value = false
  }
}

// 刷新日志列表
const refreshLogs = () => {
  fetchLogFiles()
}

// 选择日志文件
const selectLog = (log) => {
  selectedLog.value = log
  loadLogContent()
}

// 加载日志内容
const loadLogContent = async () => {
  if (!selectedLog.value) return

  contentLoading.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/log/content/${selectedLog.value.name}`,
      params: {
        max_lines: maxLines.value,
        tail: tailMode.value
      },
      onSuccess: (data) => {
        logContent.value = data
      },
      errorMessage: '获取日志内容失败'
    })
  } catch (error) {
    console.error('Error loading log content:', error)
  } finally {
    contentLoading.value = false
  }
}

// 日志文件下载功能已移除

// 监听参数变化自动刷新内容
watch([maxLines, tailMode], () => {
  if (selectedLog.value) {
    loadLogContent()
  }
})

// 组件挂载时获取日志文件列表
onMounted(() => {
  fetchLogFiles()
})
</script>

<style scoped>
/* 主容器布局 */
.log-container {
  display: flex;
  height: calc(100vh - 180px);
  min-height: 500px;
  gap: 16px;
}

/* 左侧日志文件列表面板 */
.log-files-panel {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

/* 右侧日志内容面板 */
.log-content-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

/* 面板头部 */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background-color: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

/* 日志文件列表 */
.log-files-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.log-files-list.loading {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 日志文件卡片 */
.log-file-card {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-file-card:hover {
  background-color: #f5f5f5;
}

.log-file-card.active {
  background-color: #e6f7ff;
  border-color: #91d5ff;
}

.log-file-info {
  flex: 1;
  overflow: hidden;
}

.log-file-name {
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.log-file-meta {
  font-size: 12px;
  color: #8c8c8c;
}

/* 日志内容区域 */
.log-content-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.log-info-bar {
  padding: 8px 16px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #f0f0f0;
  font-size: 12px;
  color: #8c8c8c;
  display: flex;
  gap: 16px;
}

.log-content-viewer {
  flex: 1;
  overflow: auto;
  padding: 16px;
  background-color: #fafafa;
  font-family: monospace;
  position: relative;
}

.log-content-viewer pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 无选中日志时的提示 */
.no-log-selected {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
