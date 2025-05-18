<template>
  <app-layout current-page-key="user">
    <a-card v-if="user" :title="`用户详情 - ${user ? user.username : ''}`">
      <template #extra>
        <a-space>
          <a-button @click="router.push('/user')">
            <template #icon><RollbackOutlined /></template>
            返回
          </a-button>
          <a-button type="primary" @click="router.push(`/user/${userId}/edit`)">
            <template #icon><EditOutlined /></template>
            编辑
          </a-button>
        </a-space>
      </template>

      <a-tabs v-model:activeKey="activeTabKey">
        <!-- 基本信息标签页 -->
        <a-tab-pane key="basic" tab="基本信息">
          <div class="info-container">
            <div class="info-row">
              <div class="info-label">用户名:</div>
              <div class="info-value">{{ user.username }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">邮箱:</div>
              <div class="info-value">{{ user.email }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">创建时间:</div>
              <div class="info-value">{{ formatTimestamp(user.created_at) }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">更新时间:</div>
              <div class="info-value">{{ formatTimestamp(user.updated_at) }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">创建者:</div>
              <div class="info-value">{{ user.created_by || '-' }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">更新者:</div>
              <div class="info-value">{{ user.updated_by || '-' }}</div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 操作历史标签页 -->
        <a-tab-pane key="history" tab="操作历史">
          <a-table
            :columns="auditColumns"
            :data-source="auditLogs"
            :loading="loadingAudit"
            :pagination="{
              current: auditPage,
              pageSize: auditPageSize,
              total: auditTotal,
              onChange: handleAuditPageChange,
              showSizeChanger: true,
              pageSizeOptions: ['10', '20', '50', '100'],
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

              <!-- 操作时间列 -->
              <template v-else-if="column.key === 'created_at'">
                <span>{{ formatTimestamp(record.created_at) }}</span>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  RollbackOutlined,
  EditOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

const router = useRouter()
const route = useRoute()
const userId = computed(() => route.params.id)

const loading = ref(false)
const user = ref(null)
const activeTabKey = ref('basic')

// 审计日志相关
const auditLogs = ref([])
const loadingAudit = ref(false)
const auditPage = ref(1)
const auditPageSize = ref(10)
const auditTotal = ref(0)

const auditColumns = [
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
  }
]

onMounted(() => {
  fetchUserData()
  fetchAuditLogs()
})

const fetchUserData = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/user/${userId.value}`,
      onSuccess: (data) => {
        user.value = data
      },
      errorMessage: '获取用户数据失败'
    })
  } finally {
    loading.value = false
  }
}

const fetchAuditLogs = async () => {
  loadingAudit.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/audit',
      params: {
        page: auditPage.value,
        size: auditPageSize.value,
        username: user.value?.username
      },
      onSuccess: (data, response) => {
        auditLogs.value = data
        auditTotal.value = response.total
      },
      errorMessage: '获取审计日志失败'
    })
  } finally {
    loadingAudit.value = false
  }
}

const handleAuditPageChange = (page, pageSize) => {
  auditPage.value = page
  auditPageSize.value = pageSize
  fetchAuditLogs()
}

const getActionText = (action) => {
  const actionMap = {
    'create': '创建',
    'update': '更新',
    'delete': '删除',
    'deploy': '发布',
    'rollback': '回滚'
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
    'config': '配置'
  }

  return resourceMap[resourceType] || resourceType
}

const getResourceColor = (resourceType) => {
  const colorMap = {
    'user': 'blue',
    'tool': 'purple',
    'func': 'green',
    'config': 'orange'
  }

  return colorMap[resourceType] || 'default'
}
</script>
