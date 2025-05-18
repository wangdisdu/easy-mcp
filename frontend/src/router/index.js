import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// Views
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import ToolListView from '../views/tool/ToolListView.vue'
import ToolEditView from '../views/tool/ToolEditView.vue'
import ToolDetailView from '../views/tool/ToolDetailView.vue'
import ToolDebugView from '../views/tool/ToolDebugView.vue'
import FuncListView from '../views/func/FuncListView.vue'
import FuncEditView from '../views/func/FuncEditView.vue'
import FuncDetailView from '../views/func/FuncDetailView.vue'
import ConfigListView from '../views/config/ConfigListView.vue'
import ConfigEditView from '../views/config/ConfigEditView.vue'
import ConfigDetailView from '../views/config/ConfigDetailView.vue'
import UserListView from '../views/user/UserListView.vue'
import UserEditView from '../views/user/UserEditView.vue'
import UserDetailView from '../views/user/UserDetailView.vue'
import AuditListView from '../views/audit/AuditListView.vue'

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
