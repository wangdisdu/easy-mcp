<template>
  <app-layout current-page-key="tool">
    <a-card title="导入 OpenAPI (Swagger)">
      <template #extra>
        <a-button @click="router.push('/tool')">
          <template #icon><RollbackOutlined /></template>
          返回
        </a-button>
      </template>

      <a-steps :current="currentStep" size="small" style="margin-bottom: 24px">
        <a-step title="上传 API 文件" />
        <a-step title="选择 API 接口" />
        <a-step title="生成工具" />
      </a-steps>

      <!-- 步骤 1: 上传 API 文件 -->
      <div v-if="currentStep === 0" class="step-content">
        <a-alert
          message="上传 OpenAPI (Swagger) 文件"
          description="请上传 OpenAPI (Swagger) JSON 文件，系统将自动分析文件内容并提取 API 接口信息。支持 OpenAPI v2 和 v3 格式。"
          type="info"
          show-icon
          style="margin-bottom: 24px"
        />

        <a-upload-dragger
          name="file"
          :multiple="false"
          :before-upload="beforeUpload"
          :custom-request="customUploadRequest"
          :show-upload-list="false"
          accept="application/json"
        >
          <p class="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p class="ant-upload-hint">
            仅支持 JSON 格式的 OpenAPI (Swagger) 文件
          </p>
        </a-upload-dragger>

        <div v-if="uploadError" class="error-message">
          {{ uploadError }}
        </div>
      </div>

      <!-- 步骤 2: 选择 API 接口 -->
      <div v-if="currentStep === 1" class="step-content">
        <a-alert
          message="选择要导入的 API 接口"
          description="请选择要导入的 API 接口，系统将根据选择的接口生成工具。"
          type="info"
          show-icon
          style="margin-bottom: 24px"
        />

        <a-spin :spinning="loadingApis">
          <div v-if="apiList.length === 0 && !loadingApis" class="empty-state">
            <a-empty description="没有可用的 API 接口" />
          </div>
          <a-table
            v-else
            :columns="apiColumns"
            :data-source="apiList"
            :pagination="false"
            :row-selection="{ selectedRowKeys: selectedApiKeys, onChange: onSelectApiChange, type: 'checkbox' }"
            :row-key="record => record.tool"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'method'">
                <a-tag :color="getMethodColor(record.method)">{{ record.method.toUpperCase() }}</a-tag>
              </template>
            </template>
          </a-table>
        </a-spin>

        <div class="step-actions">
          <a-button @click="currentStep = 0">上一步</a-button>
          <a-button type="primary" :disabled="selectedApiKeys.length === 0" @click="currentStep = 2">下一步</a-button>
        </div>
      </div>

      <!-- 步骤 3: 生成工具 -->
      <div v-if="currentStep === 2" class="step-content">
        <a-alert
          message="生成工具"
          description="系统将根据选择的 API 接口生成工具，请确认以下信息。"
          type="info"
          show-icon
          style="margin-bottom: 24px"
        />

        <a-form :model="toolFormState" layout="vertical">
          <a-form-item label="API 基础 URL" required>
            <a-input v-model:value="toolFormState.baseUrl" placeholder="请输入 API 基础 URL，例如: https://api.example.com" />
          </a-form-item>
        </a-form>

        <div class="selected-apis">
          <h3>已选择的 API 接口 ({{ selectedApiKeys.length }})</h3>
          <a-list size="small" bordered>
            <a-list-item v-for="apiKey in selectedApiKeys" :key="apiKey">
              {{ getApiByKey(apiKey).method.toUpperCase() }} {{ getApiByKey(apiKey).path }}
              <template #actions>
                <a-tag>{{ getApiByKey(apiKey).tool }}</a-tag>
              </template>
            </a-list-item>
          </a-list>
        </div>

        <div class="step-actions">
          <a-button @click="currentStep = 1">上一步</a-button>
          <a-button type="primary" :loading="generating" @click="generateTools">生成工具</a-button>
        </div>
      </div>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  InboxOutlined,
  RollbackOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

const router = useRouter()
const currentStep = ref(0)
const uploadError = ref('')
const loadingApis = ref(false)
const generating = ref(false)

// API 列表
const apiList = ref([])
const selectedApiKeys = ref([])

// 工具表单状态
const toolFormState = ref({
  baseUrl: ''
})

// API 表格列定义
const apiColumns = [
  {
    title: '方法',
    key: 'method',
    width: 100
  },
  {
    title: '路径',
    dataIndex: 'path',
    key: 'path'
  },
  {
    title: '工具名称',
    dataIndex: 'tool',
    key: 'tool'
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true
  }
]

// 获取方法颜色
const getMethodColor = (method) => {
  const colors = {
    get: 'blue',
    post: 'green',
    put: 'orange',
    delete: 'red',
    patch: 'purple'
  }
  return colors[method.toLowerCase()] || 'default'
}

// 根据 key 获取 API
const getApiByKey = (key) => {
  return apiList.value.find(api => api.tool === key) || {}
}

// 上传前检查
const beforeUpload = (file) => {
  const isJSON = file.type === 'application/json'
  if (!isJSON) {
    message.error('只能上传 JSON 文件!')
  }
  return isJSON || Upload.LIST_IGNORE
}

// 自定义上传请求
const customUploadRequest = async ({ file }) => {
  uploadError.value = ''
  loadingApis.value = true

  const formData = new FormData()
  formData.append('file', file)

  try {
    await callApi({
      method: 'post',
      url: '/api/v1/tool-openapi/analyze',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onSuccess: (data) => {
        apiList.value = data.apis || []

        // 自动填充 baseUrl
        if (data.server) {
          // 如果有 server 字段，直接使用
          toolFormState.value.baseUrl = data.server
        }

        currentStep.value = 1
      },
      errorMessage: '分析 OpenAPI 文件失败'
    })
  } catch (error) {
    uploadError.value = error.message || '上传文件失败'
  } finally {
    loadingApis.value = false
  }
}

// 选择 API 变更
const onSelectApiChange = (keys) => {
  selectedApiKeys.value = keys
}

// 生成工具
const generateTools = async () => {
  if (selectedApiKeys.value.length === 0) {
    message.warning('请选择要导入的 API 接口')
    return
  }

  if (!toolFormState.value.baseUrl) {
    message.warning('请输入 API 基础 URL')
    return
  }

  generating.value = true

  try {
    // 构建选中的 API 列表
    const selectedApis = selectedApiKeys.value.map(key => {
      const api = getApiByKey(key)
      return {
        path: api.path,
        method: api.method,
        tool: api.tool,
        description: api.description,
        parameters: api.parameters
      }
    })

    await callApi({
      method: 'post',
      url: '/api/v1/tool-openapi/import',
      data: {
        server: toolFormState.value.baseUrl,
        apis: selectedApis
      },
      successMessage: '工具生成成功',
      onSuccess: () => {
        router.push('/tool')
      },
      errorMessage: '生成工具失败'
    })
  } catch (error) {
    console.error('Failed to generate tools:', error)
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.step-content {
  margin-bottom: 24px;
}

.step-actions {
  margin-top: 24px;
  display: flex;
  justify-content: space-between;
}

.error-message {
  color: #ff4d4f;
  margin-top: 16px;
}

.empty-state {
  padding: 20px;
  text-align: center;
}

.selected-apis {
  margin-top: 24px;
}
</style>
