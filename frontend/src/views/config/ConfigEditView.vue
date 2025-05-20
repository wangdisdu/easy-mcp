<template>
  <app-layout current-page-key="config">
    <a-card :title="isEdit ? '编辑配置' : '创建配置'">
      <template #extra>
        <a-space>
          <a-button size="middle" @click="goBack">
            <template #icon><RollbackOutlined /></template>
            返回
          </a-button>
          <a-button
            type="primary"
            :loading="saving"
            size="middle"
            @click="handleSave"
          >
            <template #icon><SaveOutlined /></template>
            保存
          </a-button>
        </a-space>
      </template>

      <a-form
        :model="formState"
        layout="vertical"
        class="form-container"
      >
        <a-form-item label="配置名称" required>
          <a-input v-model:value="formState.name" placeholder="请输入配置名称" />
        </a-form-item>

        <a-form-item label="配置描述">
          <a-textarea v-model:value="formState.description" placeholder="请输入配置描述" :rows="3" />
        </a-form-item>

        <div>
          <a-tabs v-model:activeKey="configTabKey">
            <a-tab-pane key="schema" tab="配置定义" force-render>
              <div class="tab-description">
                <a-alert
                  message="配置定义说明"
                  description="使用JSON Schema格式定义配置项的结构。定义每个配置项的类型和描述，系统将根据此定义生成配置表单。"
                  type="info"
                  show-icon
                />
              </div>
              <div class="editor-container">
                <MonacoEditor
                  v-model:value="formState.schemaStr"
                  language="json"
                  :options="{
                    automaticLayout: true,
                    scrollBeyondLastLine: false
                  }"
                />
              </div>
            </a-tab-pane>
            <a-tab-pane key="values" tab="配置设置" force-render>
              <div class="tab-description">
                <div class="generate-button-container">
                  <a-button
                    type="primary"
                    :disabled="!isValidSchema"
                    @click="generateConfigValues"
                  >
                    <template #icon><ThunderboltOutlined /></template>
                    生成配置信息
                  </a-button>
                  <a-tooltip v-if="!isValidSchema" title="配置定义不是有效的JSON Schema">
                    <QuestionCircleOutlined class="tooltip-icon" />
                  </a-tooltip>
                </div>
              </div>
              <div class="editor-container">
                <MonacoEditor
                  v-model:value="formState.valuesStr"
                  language="json"
                  :options="{
                    automaticLayout: true,
                    scrollBeyondLastLine: false
                  }"
                />
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>
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
  ThunderboltOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, validateJson } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import MonacoEditor from '../../components/MonacoEditor.vue'

const router = useRouter()
const route = useRoute()
const configId = computed(() => route.params.id)
const isEdit = computed(() => !!configId.value)

const saving = ref(false)
const loading = ref(false)
const configTabKey = ref('schema')

const formState = reactive({
  name: '',
  description: '',
  schemaStr: JSON.stringify({
    type: 'object',
    properties: {
      apiKey: {
        type: 'string',
        description: 'API密钥'
      },
      timeout: {
        type: 'integer',
        description: '超时时间（秒）',
        default: 30
      }
    },
    required: ['apiKey']
  }, null, 2),
  valuesStr: JSON.stringify({
    apiKey: '',
    timeout: 30
  }, null, 2)
})

const formattedSchema = computed(() => {
  try {
    const parsed = JSON.parse(formState.schemaStr)
    return JSON.stringify(parsed, null, 2)
  } catch (e) {
    return '无效的 JSON'
  }
})

const formattedValues = computed(() => {
  try {
    const parsed = JSON.parse(formState.valuesStr)
    return JSON.stringify(parsed, null, 2)
  } catch (e) {
    return '无效的 JSON'
  }
})

// 检查schema是否有效
const isValidSchema = computed(() => {
  try {
    const schema = JSON.parse(formState.schemaStr)
    return schema && schema.type === 'object' && schema.properties && Object.keys(schema.properties).length > 0
  } catch (e) {
    return false
  }
})

// 根据schema生成默认配置值
const generateConfigValues = () => {
  try {
    const schema = JSON.parse(formState.schemaStr)
    if (!schema || schema.type !== 'object' || !schema.properties) {
      message.error('配置定义不是有效的JSON Schema')
      return
    }

    // 生成配置值
    const generatedValues = {}

    // 遍历schema中的所有属性
    Object.entries(schema.properties).forEach(([key, prop]) => {
      // 如果定义了默认值，使用默认值
      if (prop.default !== undefined) {
        generatedValues[key] = prop.default
      } else {
        // 根据类型生成默认值
        switch (prop.type) {
          case 'string':
            generatedValues[key] = ''
            break
          case 'number':
          case 'integer':
            generatedValues[key] = 0
            break
          case 'boolean':
            generatedValues[key] = false
            break
          case 'array':
            generatedValues[key] = []
            break
          case 'object':
            generatedValues[key] = {}
            break
          default:
            generatedValues[key] = null
        }
      }
    })

    // 更新表单中的配置值
    formState.valuesStr = JSON.stringify(generatedValues, null, 2)
    message.success('配置信息生成成功')
  } catch (e) {
    message.error(`生成配置信息失败: ${e.message}`)
  }
}

onMounted(() => {
  // If editing, load config data
  if (isEdit.value) {
    fetchConfigData()
  }
})

const fetchConfigData = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/config/${configId.value}`,
      onSuccess: (data) => {
        formState.name = data.name
        formState.description = data.description || ''
        formState.schemaStr = JSON.stringify(data.conf_schema, null, 2)
        formState.valuesStr = data.conf_value ? JSON.stringify(data.conf_value, null, 2) : '{}'
      },
      errorMessage: '获取配置数据失败'
    })
  } finally {
    loading.value = false
  }
}

const validateForm = () => {
  if (!formState.name) {
    message.error('请输入配置名称')
    return false
  }

  const schemaValidation = validateJson(formState.schemaStr)
  if (!schemaValidation.valid) {
    message.error('配置架构 JSON 格式不正确: ' + schemaValidation.message)
    return false
  }

  if (formState.valuesStr) {
    const valuesValidation = validateJson(formState.valuesStr)
    if (!valuesValidation.valid) {
      message.error('配置值 JSON 格式不正确: ' + valuesValidation.message)
      return false
    }
  }

  return true
}

const prepareData = () => {
  return {
    name: formState.name,
    description: formState.description,
    conf_schema: JSON.parse(formState.schemaStr),
    conf_value: formState.valuesStr ? JSON.parse(formState.valuesStr) : null
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
        url: `/api/v1/config/${configId.value}`,
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
        url: '/api/v1/config',
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

const goBack = () => {
  router.back()
}
</script>
