import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// 使用懒加载优化路由加载性能
// 登录页面不使用懒加载，因为它是首次访问的页面
import LoginView from '../views/LoginView.vue'

// 使用动态导入实现懒加载
// 仪表盘
const DashboardView = () => import('../views/DashboardView.vue')

// 工具相关页面
const ToolListView = () => import('../views/tool/ToolListView.vue')
const ToolEditView = () => import('../views/tool/ToolEditView.vue')
const ToolDetailView = () => import('../views/tool/ToolDetailView.vue')
const ToolDebugView = () => import('../views/tool/ToolDebugView.vue')
const OpenApiImportView = () => import('../views/tool/OpenApiImportView.vue')

// 函数相关页面
const FuncListView = () => import('../views/func/FuncListView.vue')
const FuncEditView = () => import('../views/func/FuncEditView.vue')
const FuncDetailView = () => import('../views/func/FuncDetailView.vue')

// 配置相关页面
const ConfigListView = () => import('../views/config/ConfigListView.vue')
const ConfigEditView = () => import('../views/config/ConfigEditView.vue')
const ConfigDetailView = () => import('../views/config/ConfigDetailView.vue')

// 用户相关页面
const UserListView = () => import('../views/user/UserListView.vue')
const UserEditView = () => import('../views/user/UserEditView.vue')
const UserDetailView = () => import('../views/user/UserDetailView.vue')

// 审计日志页面
const AuditListView = () => import('../views/audit/AuditListView.vue')

// 系统日志页面
const LogListView = () => import('../views/log/LogListView.vue')

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  // Tool routes
  {
    path: '/tool',
    name: 'tool-list',
    component: ToolListView,
    meta: { requiresAuth: true }
  },
  {
    path: '/tool/create',
    name: 'tool-create',
    component: ToolEditView,
    meta: { requiresAuth: true }
  },
  {
    path: '/tool/:id',
    name: 'tool-detail',
    component: ToolDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/tool/:id/edit',
    name: 'tool-edit',
    component: ToolEditView,
    meta: { requiresAuth: true }
  },
  {
    path: '/tool/:id/debug',
    name: 'tool-debug',
    component: ToolDebugView,
    meta: { requiresAuth: true }
  },
  {
    path: '/tool/import-openapi',
    name: 'tool-import-openapi',
    component: OpenApiImportView,
    meta: { requiresAuth: true }
  },
  // Function routes
  {
    path: '/func',
    name: 'func-list',
    component: FuncListView,
    meta: { requiresAuth: true }
  },
  {
    path: '/func/create',
    name: 'func-create',
    component: FuncEditView,
    meta: { requiresAuth: true }
  },
  {
    path: '/func/:id',
    name: 'func-detail',
    component: FuncDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/func/:id/edit',
    name: 'func-edit',
    component: FuncEditView,
    meta: { requiresAuth: true }
  },
  // Config routes
  {
    path: '/config',
    name: 'config-list',
    component: ConfigListView,
    meta: { requiresAuth: true }
  },
  {
    path: '/config/create',
    name: 'config-create',
    component: ConfigEditView,
    meta: { requiresAuth: true }
  },
  {
    path: '/config/:id',
    name: 'config-detail',
    component: ConfigDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/config/:id/edit',
    name: 'config-edit',
    component: ConfigEditView,
    meta: { requiresAuth: true }
  },
  // User routes
  {
    path: '/user',
    name: 'user-list',
    component: UserListView,
    meta: { requiresAuth: true }
  },
  {
    path: '/user/create',
    name: 'user-create',
    component: UserEditView,
    meta: { requiresAuth: true }
  },
  {
    path: '/user/:id',
    name: 'user-detail',
    component: UserDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/user/:id/edit',
    name: 'user-edit',
    component: UserEditView,
    meta: { requiresAuth: true }
  },
  // Audit routes
  {
    path: '/audit',
    name: 'audit-list',
    component: AuditListView,
    meta: { requiresAuth: true }
  },
  // Log routes
  {
    path: '/log',
    name: 'log-list',
    component: LogListView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)

  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
