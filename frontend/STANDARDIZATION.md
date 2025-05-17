# Vue 前端代码标准化指南

本文档定义了 Easy MCP 项目前端 Vue 代码的标准化规范，旨在确保代码的一致性、可维护性和可读性。所有贡献者应遵循这些规范，以保持代码库的质量和一致性。

## 目录

1. [项目结构](#项目结构)
2. [组件结构](#组件结构)
3. [API调用模式](#API调用模式)
4. [状态管理](#状态管理)
5. [路由管理](#路由管理)
6. [表单处理](#表单处理)
7. [UI组件规范](#UI组件规范)
8. [错误处理](#错误处理)
9. [代码格式化](#代码格式化)
10. [命名约定](#命名约定)

## 项目结构

```
frontend/
├── public/                # 静态资源
│   └── logo/              # 应用图标
├── src/                   # 源代码
│   ├── components/        # 公共组件
│   ├── router/            # 路由配置
│   ├── stores/            # Pinia 状态管理
│   ├── utils/             # 工具函数
│   ├── views/             # 页面组件
│   ├── App.vue            # 根组件
│   └── main.js            # 应用入口
├── package.json           # 项目依赖
├── vite.config.js         # Vite 配置
└── STANDARDIZATION.md     # 本文档
```

## 组件结构

### 使用 Composition API 和 `<script setup>` 语法

所有组件应使用 Composition API 和 `<script setup>` 语法：

```vue
<script setup>
// 1. Vue 核心导入
import { ref, reactive, computed, onMounted } from 'vue'
// 2. Vue Router 和 Pinia
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
// 3. UI 库组件和图标
import { message, Modal } from 'ant-design-vue'
import { SaveOutlined, DeleteOutlined } from '@ant-design/icons-vue'
// 4. Axios 和其他工具
import axios from 'axios'
import { callApi, validateForm } from '../utils/api-util'
import { formatTimestamp } from '../utils/date-format'
// 5. 本地组件
import AppLayout from '../components/AppLayout.vue'

// props 和 emits
const props = defineProps({
  // props 定义
})
const emit = defineEmits(['event1', 'event2'])

// 响应式状态
const state = reactive({})
const value = ref(null)

// 计算属性
const computedValue = computed(() => {})

// 方法
const handleEvent = () => {}

// 生命周期钩子
onMounted(() => {})
</script>
```

### 模板结构

模板应遵循一致的结构：

```vue
<template>
  <app-layout current-page-key="key">
    <a-card :title="title">
      <!-- Card extra actions -->
      <template #extra>
        <a-space>
          <a-button @click="action" size="middle">
            <template #icon><Icon /></template>
            按钮文本
          </a-button>
        </a-space>
      </template>

      <!-- Main content -->
      <a-form :model="formState" layout="vertical">
        <!-- Form items -->
      </a-form>
    </a-card>
  </app-layout>
</template>
```

## API调用模式

### 标准 API 调用模式

使用 `api-util.js` 中的 `callApi` 函数：

```javascript
const fetchData = async () => {
  try {
    await callApi({
      method: 'get',
      url: '/api/v1/endpoint',
      errorMessage: '遇到错误：获取数据失败',
      onSuccess: (data) => {
        // 处理响应
        state.value = data
      }
    })
  } catch (error) {
    // 错误已在 callApi 中处理
  }
}
```

### 创建/更新模式

```javascript
const saveData = async () => {
  try {
    saving.value = true

    await callApi({
      method: isNew.value ? 'post' : 'put',
      url: isNew.value ? '/api/v1/endpoint' : `/api/v1/endpoint/${id}`,
      data: payload,
      successMessage: isNew.value ? '创建成功' : '更新成功',
      errorMessage: isNew.value ? '遇到错误：创建失败' : '遇到错误：更新失败',
      onSuccess: () => {
        // 导航回上一页或刷新
        goBack()
      }
    })
  } catch (error) {
    // 错误已在 callApi 中处理
  } finally {
    saving.value = false
  }
}
```

### 删除模式

```javascript
const deleteItem = async (id) => {
  try {
    await callApi({
      method: 'delete',
      url: `/api/v1/endpoint/${id}`,
      successMessage: '删除成功',
      errorMessage: '遇到错误：删除失败'
    })

    // 刷新列表
    fetchData()
  } catch (error) {
    // 错误已在 callApi 中处理
  }
}
```

## 状态管理

### Pinia Store 定义

使用 `defineStore` 创建 Pinia store：

```javascript
import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    async login(account, password) {
      // 实现登录逻辑
    },

    logout() {
      // 实现登出逻辑
    }
  }
})
```

### 在组件中使用 Store

```javascript
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

// 访问状态
const userAccount = computed(() => authStore.user?.account || '未登录')

// 调用 action
const handleLogin = async () => {
  const success = await authStore.login(account.value, password.value)
}
```

## 路由管理

### 路由定义

在 `router/index.js` 中定义路由：

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// 导入视图
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'

// 定义路由
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
  }
]

// 创建路由
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

### 在组件中使用路由

```javascript
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 导航
const navigateToEdit = (id) => {
  router.push(`/item/${id}/edit`)
}

// 获取路由参数
const id = computed(() => route.params.id)
```

## 表单处理

### 表单验证

使用 `api-util.js` 中的 `validateForm` 函数：

```javascript
const validateUserForm = (form, isCreate = true) => {
  const requiredFields = ['account']
  if (isCreate) {
    requiredFields.push('password')
  }

  return validateForm(form, requiredFields)
}

const handleSave = () => {
  const validation = validateUserForm(formState, true)
  if (!validation.valid) {
    message.error(validation.message)
    return
  }

  // 继续保存
  saveData()
}
```

### JSON 验证

使用 `validateJson` 函数：

```javascript
const validation = validateJson(jsonString)
if (!validation.valid) {
  message.error(validation.message || 'JSON格式不正确')
  return
}
```

### 动态表单

对于基于 JSON Schema 的动态表单，使用 `JsonSchemaForm` 组件：

```vue
<json-schema-form
  v-if="schemaObj"
  v-model="formState.configObj"
  :schema="schemaObj"
/>
```

## UI组件规范

### 按钮标准

- 使用一致的按钮大小：`size="middle"`
- 为常见操作包含图标：
  - 保存：`<SaveOutlined />`
  - 取消/返回：`<RollbackOutlined />`
  - 创建：`<PlusOutlined />`
  - 删除：`<DeleteOutlined />`
  - 编辑：`<EditOutlined />`
  - 发布：`<CloudUploadOutlined />`
  - 复制：`<CopyOutlined />`
  - 历史：`<HistoryOutlined />`

### 表格标准

- 对长文本使用省略号和提示
- 包含带标准化选项的分页
- 使用一致的滚动设置

```javascript
const columns = [
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name',
    width: 150,
    ellipsis: true,
    tooltip: true
  }
]
```

表格分页配置：

```vue
<a-table
  :columns="columns"
  :data-source="dataSource"
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
  :scroll="{ x: 'max-content' }"
>
  <!-- 表格单元格模板 -->
</a-table>
```

### 模态框标准

- 使用 `open` 属性而非已弃用的 `visible`
- 使用一致的宽度（例如，`width="800px"` 或 `width="1000px"`）
- 使用中文文本按钮：`确定` 和 `取消`

```vue
<a-modal
  v-model:open="modalVisible"
  title="模态框标题"
  @ok="handleOk"
  :confirm-loading="confirmLoading"
  width="800px"
  ok-text="确定"
  cancel-text="取消"
>
  <!-- 模态框内容 -->
</a-modal>
```

### 标签和状态显示

使用 `a-tag` 显示状态和类型：

```vue
<a-tag v-if="record.type === 'tool'" color="blue">工具函数</a-tag>
<a-tag v-else-if="record.type === 'library'" color="green">库函数</a-tag>
```

对于状态指示器，使用图标：

```vue
<template v-if="record.enabled">
  <CheckCircleFilled style="color: #52c41a" />
  <span style="margin-left: 8px">{{ record.tool }}</span>
</template>
<template v-else>
  <StopFilled style="color: #d9d9d9" />
  <span style="margin-left: 8px; color: #d9d9d9">{{ record.tool }}</span>
</template>
```

## 错误处理

使用 `callApi` 函数进行统一的错误处理：

```javascript
try {
  // API 调用
} catch (error) {
  // 错误已在 callApi 中处理
}
```

如果需要手动处理错误，始终检查 `error.errorHandled`：

```javascript
try {
  // 其他操作
} catch (error) {
  console.error('Error description:', error)
  if (!error.errorHandled) {
    message.error('遇到错误：具体错误描述')
  }
}
```

## 代码格式化

### 导入顺序

遵循一致的导入顺序：

1. Vue 核心导入
2. Vue Router 和 Pinia
3. UI 库组件和图标
4. Axios 和其他工具
5. 本地组件

示例：

```javascript
// 1. Vue 核心导入
import { ref, reactive, computed, onMounted } from 'vue'
// 2. Vue Router 和 Pinia
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
// 3. UI 库组件和图标
import { message, Modal } from 'ant-design-vue'
import { SaveOutlined, DeleteOutlined } from '@ant-design/icons-vue'
// 4. Axios 和其他工具
import axios from 'axios'
import { callApi, validateForm, validateJson } from '../utils/api-util'
import { formatTimestamp } from '../utils/date-format'
// 5. 本地组件
import AppLayout from '../components/AppLayout.vue'
```

### 空行

- 在导入组之间使用一个空行
- 在不同功能块之间使用一个空行
- 在方法之间使用一个空行

## 命名约定

### 文件命名

- 组件文件：使用 PascalCase（例如：`AppLayout.vue`）
- 视图文件：使用 PascalCase 并以 View 结尾（例如：`LoginView.vue`）
- 工具文件：使用 kebab-case（例如：`api-util.js`）
- Store 文件：使用 camelCase（例如：`auth.js`）

### 变量命名

- 使用 camelCase 命名变量和函数（例如：`fetchData`，`handleSubmit`）
- 使用 PascalCase 命名组件（例如：`AppLayout`）
- 使用前缀 `is`、`has` 或 `should` 命名布尔值（例如：`isLoading`，`hasError`）
- 使用 `ref` 后缀命名 ref 变量（例如：`nameRef`）或直接使用描述性名称（例如：`loading`）

### 事件命名

- 使用 camelCase 命名事件处理函数，并以 `handle` 开头（例如：`handleSubmit`，`handleClick`）
- 使用 camelCase 命名自定义事件，并使用动词（例如：`click`，`change`，`update:modelValue`）

### CSS 类命名

- 使用 kebab-case 命名 CSS 类（例如：`user-avatar`，`login-form`）
- 使用 BEM 命名约定（Block-Element-Modifier）
  - 块：`block`
  - 元素：`block__element`
  - 修饰符：`block--modifier` 或 `block__element--modifier`
