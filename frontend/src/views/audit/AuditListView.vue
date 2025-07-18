<template>
  <app-layout current-page-key="audit">
    <a-card title="审计日志">
      <div class="action-bar">
        <a-space>
          <a-input
            v-model:value="filters.username"
            placeholder="用户名"
            style="width: 150px"
            allow-clear
          />

          <a-select
            v-model:value="filters.action"
            placeholder="操作类型"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="create">创建</a-select-option>
            <a-select-option value="update">更新</a-select-option>
            <a-select-option value="delete">删除</a-select-option>
            <a-select-option value="deploy">发布</a-select-option>
            <a-select-option value="rollback">回滚</a-select-option>
            <a-select-option value="import">导入</a-select-option>
          </a-select>

          <a-select
            v-model:value="filters.resource_type"
            placeholder="资源类型"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="user">用户</a-select-option>
            <a-select-option value="tool">工具</a-select-option>
            <a-select-option value="func">函数</a-select-option>
            <a-select-option value="config">配置</a-select-option>
            <a-select-option value="tag">标签</a-select-option>
          </a-select>

          <a-input
            v-model:value="filters.resource_name"
            placeholder="资源名称"
            style="width: 150px"
            allow-clear
          />

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
        :data-source="audits"
        :loading="loading"
        :pagination="{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          onChange: handlePageChange,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          onShowSizeChange: handlePageSizeChange,
          showTotal: (total) => `共 ${total} 条记录`
        }"
        :row-key="(record) => record.id"
      >
        <!-- 操作类型列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-tag :color="getActionColor(record.action)">
              {{ getActionText(record.action) }}
            </a-tag>
          </template>

          <!-- 资源类型列 -->
          <template v-else-if="column.key === 'resource_type'">
            <a-tag :color="getResourceColor(record.resource_type)">
              {{ getResourceText(record.resource_type) }}
            </a-tag>
          </template>

          <!-- 资源ID列 -->
          <template v-else-if="column.key === 'resource_id'">
            <a v-if="record.resource_id" @click="navigateToResource(record)">
              {{ record.resource_id }}
            </a>
            <span v-else>-</span>
          </template>

          <!-- 资源名称列 -->
          <template v-else-if="column.key === 'resource_name'">
            <span>{{ record.resource_name || '-' }}</span>
          </template>

          <!-- 操作时间列 -->
          <template v-else-if="column.key === 'created_at'">
            <span>{{ formatTimestamp(record.created_at) }}</span>
          </template>

          <!-- 详情列 -->
          <template v-else-if="column.key === 'details'">
            <a-button
              v-if="record.details"
              type="link"
              size="small"
              @click="showDetails(record)"
            >
              <template #icon><EyeOutlined /></template>
              查看
            </a-button>
          </template>
        </template>
      </a-table>

      <!-- 详情模态框 -->
      <a-modal
        v-model:open="detailsModalVisible"
        title="操作详情"
        width="800px"
        :footer="null"
        ok-text="确定"
        cancel-text="取消"
      >
        <pre v-if="selectedAudit">{{ JSON.stringify(selectedAudit.details, null, 2) }}</pre>
      </a-modal>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  SearchOutlined,
  EyeOutlined,
  ReloadOutlined,
  ClearOutlined
} from '@ant-design/icons-vue'
import { callApi, formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

const router = useRouter()
const loading = ref(false)
const audits = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const filters = reactive({
  username: '',
  action: undefined,
  resource_type: undefined,
  resource_name: ''
})

const dateRange = ref([])

const detailsModalVisible = ref(false)
const selectedAudit = ref(null)

const columns = [
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    width: 120
  },
  {
    title: '操作类型',
    key: 'action',
    width: 100
  },
  {
    title: '资源类型',
    key: 'resource_type',
    width: 100
  },
  {
    title: '资源ID',
    key: 'resource_id',
    width: 80
  },
  {
    title: '资源名称',
    key: 'resource_name',
    width: 150,
    ellipsis: true,
    tooltip: true
  },
  {
    title: 'IP地址',
    dataIndex: 'ip_address',
    key: 'ip_address',
    width: 120
  },
  {
    title: '操作时间',
    key: 'created_at',
    width: 180
  },
  {
    title: '详情',
    key: 'details',
    width: 100
  }
]

onMounted(() => {
  fetchAudits()
})

const fetchAudits = async () => {
  loading.value = true

  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value
    }

    if (filters.username) {
      params.username = filters.username
    }

    if (filters.action) {
      params.action = filters.action
    }

    if (filters.resource_type) {
      params.resource_type = filters.resource_type
    }

    if (filters.resource_name) {
      params.resource_name = filters.resource_name
    }

    // Add date range filter
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0].valueOf()
      params.end_time = dateRange.value[1].valueOf()
    }

    await callApi({
      method: 'get',
      url: '/api/v1/audit',
      params,
      onSuccess: (data, response) => {
        audits.value = data
        total.value = response.total
      },
      errorMessage: '获取审计日志失败'
    })
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchAudits()
}

const handleReset = () => {
  filters.username = ''
  filters.action = undefined
  filters.resource_type = undefined
  filters.resource_name = ''
  dateRange.value = []
  currentPage.value = 1
  fetchAudits()
}

const handleDateRangeChange = () => {
  handleSearch()
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
  fetchAudits()
}

const handlePageSizeChange = (current, size) => {
  currentPage.value = 1
  pageSize.value = size
  fetchAudits()
}

const getActionText = (action) => {
  const actionMap = {
    'create': '创建',
    'update': '更新',
    'delete': '删除',
    'deploy': '发布',
    'rollback': '回滚',
    'import': '导入'
  }

  return actionMap[action] || action
}

const getActionColor = (action) => {
  const colorMap = {
    'create': 'green',
    'update': 'blue',
    'delete': 'red',
    'deploy': 'purple',
    'rollback': 'orange'
  }

  return colorMap[action] || 'default'
}

const getResourceText = (resourceType) => {
  const resourceMap = {
    'user': '用户',
    'tool': '工具',
    'func': '函数',
    'config': '配置',
    'tag': '标签'
  }

  return resourceMap[resourceType] || resourceType
}

const getResourceColor = (resourceType) => {
  const colorMap = {
    'user': 'cyan',
    'tool': 'blue',
    'func': 'green',
    'config': 'purple'
  }

  return colorMap[resourceType] || 'default'
}

const navigateToResource = (record) => {
  const { resource_type, resource_id } = record

  if (!resource_id) return

  switch (resource_type) {
    case 'user':
      router.push(`/user/${resource_id}/edit`)
      break
    case 'tool':
      router.push(`/tool/${resource_id}`)
      break
    case 'func':
      router.push(`/func/${resource_id}`)
      break
    case 'config':
      router.push(`/config/${resource_id}`)
      break
  }
}

const showDetails = (record) => {
  selectedAudit.value = record
  detailsModalVisible.value = true
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

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
