<template>
  <app-layout current-page-key="tool-log">
    <a-card title="调用日志">
      <div class="action-bar">
        <a-space>
          <a-input
            v-model:value="searchForm.tool_name"
            placeholder="工具名称"
            style="width: 150px"
            allow-clear
          />

          <a-select
            v-model:value="searchForm.call_type"
            placeholder="调用类型"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="mcp">MCP调用</a-select-option>
            <a-select-option value="debug">调试调用</a-select-option>
          </a-select>

          <a-select
            v-model:value="searchForm.is_success"
            placeholder="调用状态"
            style="width: 120px"
            allow-clear
          >
            <a-select-option :value="true">成功</a-select-option>
            <a-select-option :value="false">失败</a-select-option>
          </a-select>

          <a-range-picker
            v-model:value="dateRange"
            show-time
            format="YYYY-MM-DD HH:mm:ss"
            @change="handleDateRangeChange"
            :placeholder="['开始时间', '结束时间']"
          />
        </a-space>

        <a-space>
          <a-button type="primary" @click="handleSearch">
            <template #icon><SearchOutlined /></template>
            查询
          </a-button>
          <a-button @click="handleReset">
            <template #icon><ClearOutlined /></template>
            重置
          </a-button>
        </a-space>
      </div>

      <a-table
        :columns="columns"
        :data-source="logs"
        :loading="loading"
        :pagination="{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          onChange: handleTableChange,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          onShowSizeChange: handleTableChange,
          showTotal: (total) => `共 ${total} 条记录`
        }"
        :row-key="(record) => record.id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'tool_name'">
            <a-tag color="blue">{{ record.tool_name }}</a-tag>
          </template>
          <template v-else-if="column.key === 'call_type'">
            <a-tag :color="record.call_type === 'mcp' ? 'purple' : 'orange'">
              {{ record.call_type === 'mcp' ? 'MCP' : '调试' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'is_success'">
            <a-tag :color="record.is_success ? 'green' : 'red'">
              {{ record.is_success ? '成功' : '失败' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'duration_ms'">
            <span v-if="record.duration_ms">
              {{ formatDuration(record.duration_ms) }}
            </span>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'request_time'">
            {{ formatTimestamp(record.request_time) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="showDetail(record)">
              <template #icon><EyeOutlined /></template>
              详情
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="detailVisible"
      title="调用详情"
      width="900px"
      :footer="null"
      class="detail-modal"
    >
      <div v-if="selectedLog" class="detail-content">
        <!-- 基本信息 -->
        <a-card title="基本信息" size="small" class="info-card">
          <a-row :gutter="[16, 16]">
            <a-col :span="12">
              <div class="info-item">
                <span class="info-label">工具名称:</span>
                <a-tag color="blue">{{ selectedLog.tool_name }}</a-tag>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="info-item">
                <span class="info-label">调用类型:</span>
                <a-tag :color="selectedLog.call_type === 'mcp' ? 'purple' : 'orange'">
                  {{ selectedLog.call_type === 'mcp' ? 'MCP调用' : '调试调用' }}
                </a-tag>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="info-item">
                <span class="info-label">调用状态:</span>
                <a-tag :color="selectedLog.is_success ? 'green' : 'red'">
                  {{ selectedLog.is_success ? '成功' : '失败' }}
                </a-tag>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="info-item">
                <span class="info-label">耗时:</span>
                <span>{{ selectedLog.duration_ms ? formatDuration(selectedLog.duration_ms) : '-' }}</span>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="info-item">
                <span class="info-label">请求时间:</span>
                <span>{{ formatTimestamp(selectedLog.request_time) }}</span>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="info-item">
                <span class="info-label">响应时间:</span>
                <span>{{ selectedLog.response_time ? formatTimestamp(selectedLog.response_time) : '-' }}</span>
              </div>
            </a-col>
            <a-col :span="24" v-if="selectedLog.ip_address">
              <div class="info-item">
                <span class="info-label">IP地址:</span>
                <span>{{ selectedLog.ip_address }}</span>
              </div>
            </a-col>
            <a-col :span="24" v-if="!selectedLog.is_success && selectedLog.error_message">
              <div class="info-item">
                <span class="info-label">错误信息:</span>
                <a-typography-text type="danger">
                  {{ selectedLog.error_message }}
                </a-typography-text>
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 请求参数 -->
        <a-card
          v-if="selectedLog.request_params"
          title="请求参数"
          size="small"
          class="data-card"
        >
          <template #extra>
            <a-button
              size="small"
              type="text"
              @click="copyToClipboard(formatJsonData(selectedLog.request_params))"
            >
              <template #icon><CopyOutlined /></template>
              复制
            </a-button>
          </template>
          <div class="json-content">
            <pre>{{ formatJsonData(selectedLog.request_params) }}</pre>
          </div>
        </a-card>

        <!-- 响应数据 -->
        <a-card
          v-if="selectedLog.response_data"
          title="响应数据"
          size="small"
          class="data-card"
        >
          <template #extra>
            <a-button
              size="small"
              type="text"
              @click="copyToClipboard(formatJsonData(selectedLog.response_data))"
            >
              <template #icon><CopyOutlined /></template>
              复制
            </a-button>
          </template>
          <div class="json-content">
            <pre>{{ formatJsonData(selectedLog.response_data) }}</pre>
          </div>
        </a-card>
      </div>
    </a-modal>
  </app-layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  SearchOutlined,
  ReloadOutlined,
  ClearOutlined,
  CopyOutlined,
  EyeOutlined
} from '@ant-design/icons-vue'
import { callApi } from '../../utils/api-util'
import { formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import dayjs from 'dayjs'

const router = useRouter()
const loading = ref(false)
const detailVisible = ref(false)
const selectedLog = ref(null)

const searchForm = reactive({
  tool_name: '',
  call_type: undefined,
  is_success: undefined
})

const dateRange = ref([])
const logs = ref([])

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

const columns = [
  {
    title: '工具名称',
    dataIndex: 'tool_name',
    key: 'tool_name',
    width: 150
  },
  {
    title: '调用类型',
    dataIndex: 'call_type',
    key: 'call_type',
    width: 100
  },
  {
    title: '调用状态',
    dataIndex: 'is_success',
    key: 'is_success',
    width: 100
  },
  {
    title: '耗时',
    dataIndex: 'duration_ms',
    key: 'duration_ms',
    width: 100
  },
  {
    title: '请求时间',
    dataIndex: 'request_time',
    key: 'request_time',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 100
  }
]

onMounted(() => {
  fetchLogs()
})

const fetchLogs = async () => {
  loading.value = true

  try {
    const params = {
      page: pagination.current,
      size: pagination.pageSize
    }

    if (searchForm.tool_name) {
      params.tool_name = searchForm.tool_name
    }

    if (searchForm.call_type) {
      params.call_type = searchForm.call_type
    }

    if (searchForm.is_success !== undefined) {
      params.is_success = searchForm.is_success
    }

    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0].valueOf()
      params.end_time = dateRange.value[1].valueOf()
    }

    await callApi({
      method: 'get',
      url: '/api/v1/tool-log',
      params,
      onSuccess: (data, response) => {
        logs.value = data
        pagination.total = response.total
      },
      errorMessage: '获取工具调用日志失败'
    })
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchLogs()
}

const handleSearch = () => {
  pagination.current = 1
  fetchLogs()
}

const handleDateRangeChange = () => {
  handleSearch()
}

const handleReset = () => {
  searchForm.tool_name = ''
  searchForm.call_type = undefined
  searchForm.is_success = undefined
  dateRange.value = []
  pagination.current = 1
  fetchLogs()
}

const handleRefresh = () => {
  fetchLogs()
}

const showDetail = (record) => {
  selectedLog.value = record
  detailVisible.value = true
}

const formatDuration = (ms) => {
  if (!ms) return '0ms'
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const formatJsonData = (data) => {
  if (!data) return '-'

  // 如果已经是字符串，尝试解析为JSON
  if (typeof data === 'string') {
    // 去除首尾空白字符
    const trimmed = data.trim()

    // 检查是否看起来像JSON（以{、[开头）
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        const parsed = JSON.parse(trimmed)
        return JSON.stringify(parsed, null, 2)
      } catch (e) {
        // JSON解析失败，但看起来像JSON，显示错误信息
        return `// JSON解析错误: ${e.message}\n${trimmed}`
      }
    }

    // 尝试解析其他可能的JSON值（字符串、数字、布尔值、null）
    try {
      const parsed = JSON.parse(trimmed)
      if (typeof parsed === 'object' && parsed !== null) {
        return JSON.stringify(parsed, null, 2)
      } else {
        // 简单值，直接返回格式化后的结果
        return JSON.stringify(parsed, null, 2)
      }
    } catch (e) {
      // 不是有效的JSON，返回原始字符串
      return trimmed
    }
  }

  // 如果是对象，直接格式化
  if (typeof data === 'object' && data !== null) {
    try {
      return JSON.stringify(data, null, 2)
    } catch (e) {
      return `// 对象序列化错误: ${e.message}\n${String(data)}`
    }
  }

  // 其他类型转为字符串
  return String(data)
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    console.log('复制成功')
  } catch (err) {
    // 降级方案
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      console.log('复制成功')
    } catch (e) {
      console.error('复制失败:', e)
    }
    document.body.removeChild(textArea)
  }
}
</script>

<style scoped>
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 16px;
}

/* 详情弹窗样式 */
.detail-modal :deep(.ant-modal-body) {
  padding: 16px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 信息卡片样式 */
.info-card {
  margin-bottom: 0;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
}

.info-label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
  flex-shrink: 0;
}

/* 数据卡片样式 */
.data-card {
  margin-bottom: 0;
}

.data-card :deep(.ant-card-head) {
  min-height: 40px;
  padding: 0 16px;
}

.data-card :deep(.ant-card-head-title) {
  font-size: 14px;
  font-weight: 500;
}

.data-card :deep(.ant-card-body) {
  padding: 0;
}

/* JSON内容样式 */
.json-content {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}

.json-content pre {
  margin: 0;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: transparent;
}

/* 滚动条样式 */
.json-content::-webkit-scrollbar {
  width: 6px;
}

.json-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.json-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.json-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .detail-modal :deep(.ant-modal) {
    width: 95% !important;
    margin: 10px;
  }

  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .info-label {
    min-width: auto;
  }

  .json-content {
    max-height: 200px;
  }

  .json-content pre {
    padding: 12px;
    font-size: 11px;
  }
}
</style>
