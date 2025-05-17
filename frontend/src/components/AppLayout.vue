<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible :width="180" :collapsedWidth="64">
      <div class="logo">
        <img v-if="!collapsed" src="/logo/logo.svg" alt="Easy MCP" class="logo-large" />
        <img v-else src="/logo/logo-small.svg" alt="MCP" class="logo-small" />
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
      >
        <a-menu-item key="dashboard">
          <template #icon><DashboardOutlined /></template>
          <span>仪表盘</span>
          <router-link to="/dashboard" />
        </a-menu-item>
        <a-menu-item key="tool">
          <template #icon><ToolOutlined /></template>
          <span>工具管理</span>
          <router-link to="/tool" />
        </a-menu-item>
        <a-menu-item key="func">
          <template #icon><FunctionOutlined /></template>
          <span>函数管理</span>
          <router-link to="/func" />
        </a-menu-item>
        <a-menu-item key="config">
          <template #icon><SettingOutlined /></template>
          <span>配置管理</span>
          <router-link to="/config" />
        </a-menu-item>
        <a-menu-item key="user">
          <template #icon><UserOutlined /></template>
          <span>用户管理</span>
          <router-link to="/user" />
        </a-menu-item>
        <a-menu-item key="audit">
          <template #icon><FileSearchOutlined /></template>
          <span>审计日志</span>
          <router-link to="/audit" />
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0; display: flex; justify-content: flex-end; height: 48px; line-height: 48px;">
        <div style="margin-right: 24px;">
          <a-dropdown>
            <a class="ant-dropdown-link" @click.prevent>
              <UserOutlined /> {{ username }} <DownOutlined />
            </a>
            <template #overlay>
              <a-menu>
                <a-menu-item key="logout" @click="handleLogout">
                  <LogoutOutlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content>
        <div class="page-container" style="padding: 16px;">
          <slot></slot>
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  DashboardOutlined,
  ToolOutlined,
  FunctionOutlined,
  SettingOutlined,
  UserOutlined,
  FileSearchOutlined,
  LogoutOutlined,
  DownOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  currentPageKey: {
    type: String,
    default: 'dashboard'
  }
})

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const collapsed = ref(false)
const selectedKeys = ref([props.currentPageKey])

// Get username from auth store
const username = computed(() => {
  return authStore.user?.username || '未登录'
})

// Update selected keys when route changes
watch(
  () => route.path,
  (path) => {
    const key = path.split('/')[1] || 'dashboard'
    selectedKeys.value = [key]
  },
  { immediate: true }
)

// Logout handler
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.logo {
  height: 32px;
  margin: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
}

.logo-large {
  width: 100px;
  height: auto;
}

.logo-small {
  width: 24px;
  height: auto;
}
</style>
