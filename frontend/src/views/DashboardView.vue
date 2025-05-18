<template>
  <app-layout current-page-key="dashboard">
    <a-card title="仪表盘">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card>
            <template #title>
              <ToolOutlined /> 工具
            </template>
            <div class="stat-card">
              <div class="stat-number">{{ stats.toolCount }}</div>
              <div class="stat-label">已注册工具</div>
            </div>
            <a-button type="link" @click="router.push('/tool')">查看全部</a-button>
          </a-card>
        </a-col>

        <a-col :span="6">
          <a-card>
            <template #title>
              <FunctionOutlined /> 函数
            </template>
            <div class="stat-card">
              <div class="stat-number">{{ stats.funcCount }}</div>
              <div class="stat-label">已注册函数</div>
            </div>
            <a-button type="link" @click="router.push('/func')">查看全部</a-button>
          </a-card>
        </a-col>

        <a-col :span="6">
          <a-card>
            <template #title>
              <SettingOutlined /> 配置
            </template>
            <div class="stat-card">
              <div class="stat-number">{{ stats.configCount }}</div>
              <div class="stat-label">已创建配置</div>
            </div>
            <a-button type="link" @click="router.push('/config')">查看全部</a-button>
          </a-card>
        </a-col>

        <a-col :span="6">
          <a-card>
            <template #title>
              <UserOutlined /> 用户
            </template>
            <div class="stat-card">
              <div class="stat-number">{{ stats.userCount }}</div>
              <div class="stat-label">系统用户</div>
            </div>
            <a-button type="link" @click="router.push('/user')">查看全部</a-button>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="12">
          <a-card title="最近活动">
            <a-list
              :data-source="recentActivities"
              :loading="loading"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #title>
                      {{ getActionText(item.action) }} {{ item.resource_type }}
                    </template>
                    <template #description>
                      {{ item.username }} - {{ formatTimestamp(item.created_at) }}
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>

        <a-col :span="12">
          <a-card title="最近工具">
            <a-list
              :data-source="recentTools"
              :loading="loading"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #title>
                      <a @click="router.push(`/tool/${item.id}`)">{{ item.name }}</a>
                    </template>
                    <template #description>
                      {{ item.description || '无描述' }}
                    </template>
                  </a-list-item-meta>
                  <template #actions>
                    <a-tag :color="item.is_enabled ? 'green' : 'red'">
                      {{ item.is_enabled ? '已启用' : '已禁用' }}
                    </a-tag>
                  </template>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>
      </a-row>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ToolOutlined,
  FunctionOutlined,
  SettingOutlined,
  UserOutlined
} from '@ant-design/icons-vue'
import { callApi } from '../utils/api-util'
import { formatTimestamp } from '../utils/api-util'
import AppLayout from '../components/AppLayout.vue'

const router = useRouter()
const loading = ref(false)

const stats = reactive({
  toolCount: 0,
  funcCount: 0,
  configCount: 0,
  userCount: 0
})

const recentActivities = ref([])
const recentTools = ref([])

onMounted(async () => {
  loading.value = true

  try {
    // Fetch stats
    await fetchStats()

    // Fetch recent activities
    await fetchRecentActivities()

    // Fetch recent tools
    await fetchRecentTools()
  } finally {
    loading.value = false
  }
})

const fetchStats = async () => {
  try {
    // Fetch tool count
    await callApi({
      method: 'get',
      url: '/api/v1/tool',
      params: { page: 1, size: 1 },
      onSuccess: (data, response) => {
        stats.toolCount = response.total || 0
      }
    })

    // Fetch function count
    await callApi({
      method: 'get',
      url: '/api/v1/func',
      params: { page: 1, size: 1 },
      onSuccess: (data, response) => {
        stats.funcCount = response.total || 0
      }
    })

    // Fetch config count
    await callApi({
      method: 'get',
      url: '/api/v1/config',
      params: { page: 1, size: 1 },
      onSuccess: (data, response) => {
        stats.configCount = response.total || 0
      }
    })

    // Fetch user count
    await callApi({
      method: 'get',
      url: '/api/v1/user',
      params: { page: 1, size: 1 },
      onSuccess: (data, response) => {
        stats.userCount = response.total || 0
      }
    })
  } catch (error) {
    console.error('Error fetching stats:', error)
  }
}

const fetchRecentActivities = async () => {
  try {
    await callApi({
      method: 'get',
      url: '/api/v1/audit',
      params: { page: 1, size: 5 },
      onSuccess: (data) => {
        recentActivities.value = data
      }
    })
  } catch (error) {
    console.error('Error fetching recent activities:', error)
  }
}

const fetchRecentTools = async () => {
  try {
    await callApi({
      method: 'get',
      url: '/api/v1/tool',
      params: { page: 1, size: 5 },
      onSuccess: (data) => {
        recentTools.value = data
      }
    })
  } catch (error) {
    console.error('Error fetching recent tools:', error)
  }
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
</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: 8px 0;
}

.stat-number {
  font-size: 20px;
  font-weight: 500;
  color: #1890ff;
}

.stat-label {
  color: rgba(0, 0, 0, 0.45);
  margin-top: 4px;
}
</style>
