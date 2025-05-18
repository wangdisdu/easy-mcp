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

        <!-- 第三行：依赖函数和绑定配置 -->
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

        <!-- 第四行：参数定义和工具代码使用tab切换 -->
        <a-form-item>
          <a-tabs v-model:activeKey="codeTabKey">
            <!-- 参数定义标签页 -->
            <a-tab-pane key="parameters" tab="参数定义" force-render>
              <div class="tab-description">
                <a-alert
                  message="参数定义说明"
                  description="使用JSON Schema格式定义工具的输入参数。定义每个参数的类型、描述、默认值等属性，系统将此定义作为MCP Tool input schema。"
                  type="info"
                  show-icon
                />
              </div>
              <div class="editor-container">
                <MonacoEditor
                  v-model:value="formState.parametersStr"
                  language="json"
                  :options="{
                    automaticLayout: true,
                    scrollBeyondLastLine: false
                  }"
                />
              </div>
            </a-tab-pane>

            <!-- 工具代码标签页 -->
            <a-tab-pane key="code" tab="工具代码" force-render>
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
  CloudUploadOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, validateJson } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import MonacoEditor from '../../components/MonacoEditor.vue'

const router = useRouter()
const route = useRoute()
const toolId = computed(() => route.params.id)
const isEdit = computed(() => !!toolId.value)

const saving = ref(false)
const loading = ref(false)
const loadingFuncs = ref(false)
const loadingConfigs = ref(false)
const codeTabKey = ref('parameters')

const formState = reactive({
  name: '',
  description: '',
  parametersStr: JSON.stringify({ type: 'object', properties: { name: { type: 'string', description: '名称' } }, required: ['name'] }, null, 2),
  code: '# parameters: 传入参数\n# config: 传入配置\n# result: 用于返回值\n\n# 示例代码：\nprint("执行工具...")\nresult = {"message": "Hello, World!", "parameters": parameters, "config": config}\n',
  func_ids: [],
  config_ids: []
})

const funcOptions = ref([])
const configOptions = ref([])

const formattedParameters = computed(() => {
  try {
    const parsed = JSON.parse(formState.parametersStr)
    return JSON.stringify(parsed, null, 2)
  } catch (e) {
    return '无效的 JSON'
  }
})

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
        formState.parametersStr = JSON.stringify(data.parameters, null, 2)
        formState.code = data.code

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
  return {
    name: formState.name,
    description: formState.description,
    parameters: JSON.parse(formState.parametersStr),
    code: formState.code,
    func_ids: formState.func_ids,
    config_ids: formState.config_ids
  }
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
