<template>
  <app-layout current-page-key="tool">
    <a-card :title="isEdit ? '编辑工具' : '创建工具'">
      <template #extra>
        <a-space>
          <a-button @click="goBack">
            <template #icon><RollbackOutlined /></template>
            返回
          </a-button>
          <a-button type="primary" :loading="saving" @click="handleSave">
            <template #icon><SaveOutlined /></template>
            保存
          </a-button>
          <a-button type="primary" :loading="saving" @click="handleSaveAndDeploy">
            <template #icon><CloudUploadOutlined /></template>
            {{ isEdit ? '保存并发布' : '创建并发布' }}
          </a-button>
        </a-space>
      </template>

      <a-form
        :model="formState"
        layout="vertical"
        class="form-container"
      >
        <!-- 第一行：工具名称 -->
        <a-form-item label="工具名称" required>
          <a-input v-model:value="formState.name" placeholder="请输入工具名称" />
        </a-form-item>

        <!-- 第二行：工具描述 -->
        <a-form-item label="工具描述" required>
          <a-textarea v-model:value="formState.description" placeholder="请输入工具描述" :rows="3" />
        </a-form-item>

        <!-- HTTP工具特有字段 -->
        <template v-if="formState.type === 'http'">
          <a-form-item label="请求地址" required>
            <a-input v-model:value="formState.setting.url" placeholder="请输入HTTP请求地址，支持参数变量占位符，如：http://localhost:80/user/{id}?format={format}" />
          </a-form-item>

          <a-form-item 
            label="请求Header" 
            :label-col="{ span: 24 }"
            :wrapper-col="{ span: 24 }"
            class="header-form-item"
          >
            <div class="header-row">
              <a-button type="primary" size="small" @click="addHeader">
                <template #icon><PlusOutlined /></template>
                添加请求头
              </a-button>
            </div>
            <a-table
              :columns="headerColumns"
              :data-source="formState.setting.headers"
              :pagination="false"
              size="small"
            >
              <template #bodyCell="{ column, record, index }">
                <template v-if="column.key === 'key'">
                  <a-input
                    :default-value="record.key"
                    @blur="(e) => handleHeaderChange(index, 'key', e.target.value)"
                    placeholder="请输入Header Key"
                  />
                </template>
                <template v-if="column.key === 'value'">
                  <a-input
                    :default-value="record.value"
                    @blur="(e) => handleHeaderChange(index, 'value', e.target.value)"
                    placeholder="请输入Header Value"
                  />
                </template>
                <template v-if="column.key === 'action'">
                  <a-button type="link" size="small" danger @click="removeHeader(index)">
                    <template #icon><DeleteOutlined /></template>
                    删除
                  </a-button>
                </template>
              </template>
            </a-table>
          </a-form-item>
        </template>

        <!-- 第四行：依赖函数和绑定配置 -->
        <a-row :gutter="16">
          <!-- 依赖函数 -->
          <a-col :span="12">
            <a-form-item label="依赖函数">
              <a-select
                v-model:value="formState.func_ids"
                mode="multiple"
                placeholder="请选择依赖函数"
                :loading="loadingFuncs"
                :options="funcOptions"
              />
            </a-form-item>
          </a-col>

          <!-- 绑定配置 -->
          <a-col :span="12">
            <a-form-item label="绑定配置">
              <a-select
                v-model:value="formState.config_ids"
                mode="multiple"
                placeholder="请选择绑定配置"
                :loading="loadingConfigs"
                :options="configOptions"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 第五行：参数定义和工具代码使用tab切换 -->
        <a-form-item>
          <a-tabs v-model:activeKey="activeTabKey">
            <!-- 参数定义标签页 -->
            <a-tab-pane key="parameters" tab="参数定义" force-render>
              <div class="tab-description">
                <a-alert
                  message="参数定义说明"
                  description="定义工具的输入参数。您可以使用图形化编辑器或直接编辑JSON Schema。"
                  type="info"
                  show-icon
                />
              </div>
              <div class="schema-editor-container">
                <!-- 使用JsonSchemaEditor组件 -->
                <JsonSchemaEditor 
                  v-model:value="formState.parametersStr" 
                  :is-http-tool="formState.type === 'http'"
                />
              </div>
            </a-tab-pane>

            <!-- 工具代码标签页 -->
            <a-tab-pane key="code" tab="工具代码" force-render>
              <div class="tab-description">
                <a-alert
                  message="工具代码说明"
                  description="编写工具的执行代码。系统会自动提供以下变量：parameters（传入的参数）、config（绑定的配置）、result（用于返回结果）。您可以使用依赖函数和Python标准库。"
                  type="info"
                  show-icon
                />
              </div>
              <div class="editor-container">
                <MonacoEditor
                  v-model:value="formState.code"
                  language="python"
                  :options="{
                    automaticLayout: true,
                    scrollBeyondLastLine: false
                  }"
                />
              </div>
            </a-tab-pane>
          </a-tabs>
        </a-form-item>
      </a-form>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  SaveOutlined,
  RollbackOutlined,
  CloudUploadOutlined,
  PlusOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, validateJson } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import MonacoEditor from '../../components/MonacoEditor.vue'
import JsonSchemaEditor from '../../components/JsonSchemaEditor.vue'

const router = useRouter()
const route = useRoute()
const toolId = computed(() => route.params.id)
const isEdit = computed(() => !!toolId.value)
const toolType = computed(() => route.query.type || 'basic')

const saving = ref(false)
const loading = ref(false)
const loadingFuncs = ref(false)
const loadingConfigs = ref(false)
const activeTabKey = ref('parameters')

const formState = reactive({
  name: '',
  description: '',
  type: toolType.value,
  setting: toolType.value === 'http' ? {
    url: '',
    headers: [{key: "Content-Type", value: "application/json"}]
  } : {},
  parametersStr: toolType.value === 'http' ?
    JSON.stringify({ type: 'object', properties: { name: { type: 'string', description: '名称', location: 'body' } }, required: ['name'] })
    : JSON.stringify({ type: 'object', properties: { name: { type: 'string', description: '名称' } }, required: ['name'] }),

  code: toolType.value === 'http' ? 
    `# url: 请求地址
# headers: 请求Header
# parameters: 传入工具参数
# config: 传入绑定配置
# result: 用于返回值

# 示例代码：
print("执行工具...")
result = easy_http_call(url, headers, parameters, config)` :
    `# parameters: 传入工具参数
# config: 传入绑定配置
# result: 用于返回值

# 示例代码：
print("执行工具...")
result = {"message": "Hello, World!", "parameters": parameters, "config": config}`,
  func_ids: [],
  config_ids: []
})

const funcOptions = ref([])
const configOptions = ref([])

const headerColumns = [
  {
    title: 'Key',
    dataIndex: 'key',
    key: 'key',
    width: '40%'
  },
  {
    title: 'Value',
    dataIndex: 'value',
    key: 'value',
    width: '40%'
  },
  {
    title: '操作',
    key: 'action',
    width: '20%'
  }
]

const addHeader = () => {
  formState.setting.headers.push({ key: '', value: '' })
}

const removeHeader = (index) => {
  formState.setting.headers.splice(index, 1)
}

const handleHeaderChange = (index, field, value) => {
  if (formState.setting.headers[index]) {
    formState.setting.headers[index][field] = value
  }
}

onMounted(async () => {
  // Load functions and configs
  await Promise.all([
    fetchFunctions(),
    fetchConfigs()
  ])

  // If editing, load tool data
  if (isEdit.value) {
    await fetchToolData()
  }
})

const fetchFunctions = async () => {
  loadingFuncs.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/func',
      params: { page: 1, size: 100 },
      onSuccess: (data) => {
        funcOptions.value = data.map(func => ({
          value: func.id,
          label: func.name
        }))
      },
      errorMessage: '获取函数列表失败'
    })
  } finally {
    loadingFuncs.value = false
  }
}

const fetchConfigs = async () => {
  loadingConfigs.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/config',
      params: { page: 1, size: 100 },
      onSuccess: (data) => {
        configOptions.value = data.map(config => ({
          value: config.id,
          label: config.name
        }))
      },
      errorMessage: '获取配置列表失败'
    })
  } finally {
    loadingConfigs.value = false
  }
}

const fetchToolData = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${toolId.value}`,
      onSuccess: (data) => {
        formState.name = data.name
        formState.description = data.description || ''
        formState.type = data.type || 'basic'
        formState.parametersStr = JSON.stringify(data.parameters, null, 2)
        formState.code = data.code
        formState.setting = data.setting || { url: '', headers: [] }

        // 确保 headers 是数组格式
        if (formState.setting.headers && !Array.isArray(formState.setting.headers)) {
          formState.setting.headers = []
        }

        // Load relationships
        fetchToolFunctions()
        fetchToolConfigs()
      },
      errorMessage: '获取工具数据失败'
    })
  } finally {
    loading.value = false
  }
}

const fetchToolFunctions = async () => {
  try {
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${toolId.value}/func`,
      onSuccess: (data) => {
        if (data && Array.isArray(data)) {
          formState.func_ids = data.map(func => func.id)
        } else {
          formState.func_ids = []
        }
      },
      errorMessage: '获取工具依赖函数失败'
    })
  } catch (error) {
    console.error('Error fetching tool dependent functions:', error)
  }
}

const fetchToolConfigs = async () => {
  try {
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${toolId.value}/config`,
      onSuccess: (data) => {
        if (data && Array.isArray(data)) {
          formState.config_ids = data.map(config => config.id)
        } else {
          formState.config_ids = []
        }
      },
      errorMessage: '获取工具绑定配置失败'
    })
  } catch (error) {
    console.error('Error fetching tool bound configs:', error)
  }
}

const validateForm = () => {
  if (!formState.name) {
    message.error('请输入工具名称')
    return false
  }

  if (!formState.description) {
    message.error('请输入工具描述')
    return false
  }

  if (formState.type === 'http') {
    if (!formState.setting.url) {
      message.error('请输入HTTP请求地址')
      return false
    }
  }

  const parametersValidation = validateJson(formState.parametersStr)
  if (!parametersValidation.valid) {
    message.error('参数定义 JSON 格式不正确: ' + parametersValidation.message)
    return false
  }

  if (!formState.code) {
    message.error('请输入工具代码')
    return false
  }

  return true
}

const prepareData = () => {
  const data = {
    name: formState.name,
    description: formState.description,
    type: formState.type,
    setting: formState.type === 'http' ? {
      url: formState.setting.url,
      headers: formState.setting.headers.map(header => ({
        key: header.key,
        value: header.value
      }))
    } : {},
    parameters: JSON.parse(formState.parametersStr),
    code: formState.code,
    func_ids: formState.func_ids,
    config_ids: formState.config_ids
  }

  return data
}

const handleSave = async () => {
  if (!validateForm()) return

  saving.value = true

  try {
    const data = prepareData()

    if (isEdit.value) {
      await callApi({
        method: 'put',
        url: `/api/v1/tool/${toolId.value}`,
        data,
        successMessage: '保存成功',
        errorMessage: '保存失败',
        onSuccess: () => {
          goBack()
        }
      })
    } else {
      await callApi({
        method: 'post',
        url: '/api/v1/tool',
        data,
        successMessage: '创建成功',
        errorMessage: '创建失败',
        onSuccess: () => {
          goBack()
        }
      })
    }
  } finally {
    saving.value = false
  }
}

const handleSaveAndDeploy = async () => {
  if (!validateForm()) return

  saving.value = true

  try {
    const data = prepareData()

    if (isEdit.value) {
      // 编辑模式：保存并发布
      await callApi({
        method: 'put',
        url: `/api/v1/tool/${toolId.value}/deploy`,
        data,
        successMessage: '保存并发布成功',
        errorMessage: '保存并发布失败',
        onSuccess: () => {
          goBack()
        }
      })
    } else {
      // 创建模式：创建并发布
      await callApi({
        method: 'post',
        url: '/api/v1/tool/deploy',
        data,
        successMessage: '创建并发布成功',
        errorMessage: '创建并发布失败',
        onSuccess: () => {
          goBack()
        }
      })
    }
  } finally {
    saving.value = false
  }
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.form-container {
  max-width: 1200px;
  margin: 0 auto;
}

.tab-description {
  margin-bottom: 16px;
}

.schema-editor-container {
  border-radius: 2px;
}

.editor-container {
  border-radius: 2px;
}

.header-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

:deep(.header-form-item .ant-form-item-label) {
  padding-bottom: 0;
}

:deep(.header-form-item .ant-form-item-label > label) {
  height: 32px;
  line-height: 32px;
}
</style>
