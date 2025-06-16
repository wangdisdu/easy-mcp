<template>
  <app-layout current-page-key="tool">
    <a-card :title="`调试工具: ${tool ? tool.name : '加载中...'}`">
      <template #extra>
        <a-space>
          <a-button @click="router.push(`/tool`)">
            <template #icon><RollbackOutlined /></template>
            返回
          </a-button>
        </a-space>
      </template>

      <a-spin :spinning="loading">
        <div v-if="tool" class="debug-container">
          <!-- 左侧：参数表单 -->
          <div class="debug-form">
            <h3>参数设置</h3>
            <a-form layout="vertical">
              <!-- 动态渲染表单 -->
              <template v-if="parametersSchema && parametersSchema.properties">
                <template v-for="(property, key) in parametersSchema.properties" :key="key">
                  <a-form-item
                    :label="property.title || key"
                    :required="isRequired(key)"
                    :help="property.description"
                  >
                    <!-- 字符串类型 -->
                    <template v-if="property.type === 'string'">
                      <!-- 枚举类型 -->
                      <a-select
                        v-if="property.enum"
                        v-model:value="formValues[key]"
                        :placeholder="`请选择${property.title || key}`"
                      >
                        <a-select-option
                          v-for="option in property.enum"
                          :key="option"
                          :value="option"
                        >
                          {{ option }}
                        </a-select-option>
                      </a-select>
                      <!-- 多行文本 -->
                      <a-textarea
                        v-else-if="property.format === 'textarea'"
                        v-model:value="formValues[key]"
                        :rows="4"
                        :placeholder="`请输入${property.title || key}`"
                      />
                      <!-- 普通文本 -->
                      <a-input
                        v-else
                        v-model:value="formValues[key]"
                        :placeholder="`请输入${property.title || key}`"
                      />
                    </template>

                    <!-- 数字类型 -->
                    <template v-else-if="property.type === 'number' || property.type === 'integer'">
                      <a-input-number
                        v-model:value="formValues[key]"
                        :min="property.minimum"
                        :max="property.maximum"
                        :step="property.type === 'integer' ? 1 : 0.1"
                        style="width: 100%"
                      />
                    </template>

                    <!-- 布尔类型 -->
                    <template v-else-if="property.type === 'boolean'">
                      <a-switch v-model:checked="formValues[key]" />
                    </template>

                    <!-- 数组类型 -->
                    <template v-else-if="property.type === 'array'">
                      <a-select
                        v-if="property.items && property.items.enum"
                        v-model:value="formValues[key]"
                        mode="multiple"
                        :placeholder="`请选择${property.title || key}`"
                      >
                        <a-select-option
                          v-for="option in property.items.enum"
                          :key="option"
                          :value="option"
                        >
                          {{ option }}
                        </a-select-option>
                      </a-select>
                      <a-textarea
                        v-else
                        v-model:value="arrayInputs[key]"
                        :rows="3"
                        placeholder="请输入JSON数组，例如: ['item1', 'item2']"
                        @change="handleArrayInput(key)"
                      />
                    </template>

                    <!-- 对象类型 -->
                    <template v-else-if="property.type === 'object'">
                      <a-textarea
                        v-model:value="objectInputs[key]"
                        :rows="4"
                        placeholder="请输入JSON对象，例如: {'key': 'value'}"
                        @change="handleObjectInput(key)"
                      />
                    </template>

                    <!-- 其他类型 -->
                    <template v-else>
                      <a-input
                        v-model:value="formValues[key]"
                        :placeholder="`请输入${property.title || key}`"
                      />
                    </template>
                  </a-form-item>
                </template>
              </template>

              <!-- 无参数或参数格式错误 -->
              <a-empty v-else description="无参数定义或参数格式错误" />

              <!-- 执行按钮 -->
              <a-form-item>
                <a-button
                  type="primary"
                  :loading="debugging"
                  :disabled="!tool || !parametersSchema"
                  @click="handleDebug"
                >
                  <template #icon><PlayCircleOutlined /></template>
                  执行
                </a-button>
                <a-button
                  style="margin-left: 8px;"
                  :disabled="!tool || !parametersSchema"
                  @click="resetForm"
                >
                  <template #icon><ReloadOutlined /></template>
                  重置
                </a-button>
              </a-form-item>
            </a-form>
          </div>

          <!-- 右侧：执行结果 -->
          <div class="debug-result">
            <h3>执行结果</h3>
            <a-spin :spinning="debugging">
              <div v-if="debugResult" class="result-container">
                <!-- 错误提示 -->
                <a-alert
                  v-if="!debugResult.success"
                  type="error"
                  show-icon
                  :message="'执行失败'"
                  :description="debugResult.error_message"
                  class="error-alert"
                />

                <a-tabs v-model:activeKey="resultTabKey">
                  <a-tab-pane key="result" tab="返回值">
                    <pre v-if="debugResult.success" class="result-content">{{ formatResult(debugResult.result) }}</pre>
                    <a-empty v-else description="执行失败，无返回值" />
                  </a-tab-pane>
                  <a-tab-pane key="logs" tab="日志">
                    <a-list
                      class="log-list"
                      :data-source="debugResult.logs"
                      size="small"
                      bordered
                    >
                      <template #renderItem="{ item }">
                        <a-list-item>{{ item }}</a-list-item>
                      </template>
                      <template #empty>
                        <a-empty description="无日志" />
                      </template>
                    </a-list>
                  </a-tab-pane>
                </a-tabs>
              </div>
              <a-empty v-else description="暂无执行结果" />
            </a-spin>
          </div>
        </div>
        <a-empty v-else-if="!loading" description="工具不存在或无法访问" />
      </a-spin>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  RollbackOutlined,
  PlayCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, validateJson } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

const router = useRouter()
const route = useRoute()
const toolId = computed(() => route.params.id)

// 状态变量
const loading = ref(false)
const tool = ref(null)
const debugging = ref(false)
const debugResult = ref(null)
const resultTabKey = ref('result')

// 表单数据
const formValues = reactive({})
const arrayInputs = reactive({})
const objectInputs = reactive({})

// 计算属性
const parametersSchema = computed(() => {
  if (!tool.value || !tool.value.parameters) return null
  return tool.value.parameters
})

// 判断参数是否必填
const isRequired = (key) => {
  if (!parametersSchema.value || !parametersSchema.value.required) return false
  return parametersSchema.value.required.includes(key)
}

// 生命周期钩子
onMounted(() => {
  fetchToolData()
})

// 监听工具数据变化，初始化表单
watch(() => tool.value, (newTool) => {
  if (newTool && newTool.parameters && newTool.parameters.properties) {
    initFormValues()
  }
}, { immediate: true })

// 初始化表单值
const initFormValues = () => {
  if (!parametersSchema.value || !parametersSchema.value.properties) return

  // 清空现有值
  Object.keys(formValues).forEach(key => delete formValues[key])
  Object.keys(arrayInputs).forEach(key => delete arrayInputs[key])
  Object.keys(objectInputs).forEach(key => delete objectInputs[key])

  // 设置默认值
  Object.entries(parametersSchema.value.properties).forEach(([key, property]) => {
    if (property.default !== undefined) {
      formValues[key] = property.default
    } else {
      // 根据类型设置默认值
      switch (property.type) {
        case 'string':
          formValues[key] = ''
          break
        case 'number':
        case 'integer':
          formValues[key] = null
          break
        case 'boolean':
          formValues[key] = false
          break
        case 'array':
          formValues[key] = []
          arrayInputs[key] = '[]'
          break
        case 'object':
          formValues[key] = {}
          objectInputs[key] = '{}'
          break
        default:
          formValues[key] = null
      }
    }
  })
}

// 重置表单
const resetForm = () => {
  initFormValues()
  message.success('表单已重置')
}

// 处理数组输入
const handleArrayInput = (key) => {
  try {
    const arrayValue = JSON.parse(arrayInputs[key])
    if (Array.isArray(arrayValue)) {
      formValues[key] = arrayValue
    } else {
      message.error('请输入有效的JSON数组')
    }
  } catch (error) {
    message.error('JSON格式错误: ' + error.message)
  }
}

// 处理对象输入
const handleObjectInput = (key) => {
  try {
    const objectValue = JSON.parse(objectInputs[key])
    if (objectValue && typeof objectValue === 'object' && !Array.isArray(objectValue)) {
      formValues[key] = objectValue
    } else {
      message.error('请输入有效的JSON对象')
    }
  } catch (error) {
    message.error('JSON格式错误: ' + error.message)
  }
}

// 获取工具数据
const fetchToolData = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${toolId.value}`,
      onSuccess: (data) => {
        tool.value = data
      },
      errorMessage: '获取工具数据失败'
    })
  } catch (error) {
    console.error('Error fetching tool data:', error)
  } finally {
    loading.value = false
  }
}

// 执行调试
const handleDebug = async () => {
  debugging.value = true
  debugResult.value = null

  try {
    await callApi({
      method: 'post',
      url: `/api/v1/tool/${toolId.value}/debug`,
      data: {
        parameters: formValues
      },
      onSuccess: (data) => {
        debugResult.value = data

        // 根据执行结果设置激活的标签页
        if (data.success) {
          resultTabKey.value = 'result'
          message.success('执行成功')
        } else {
          resultTabKey.value = 'logs'
          // 不再显示错误提示，因为错误已在UI中显示
        }
      },
      // 不显示默认错误提示，因为我们已经在UI中显示了错误
      errorMessage: null
    })
  } catch (error) {
    // 错误已由拦截器处理，这里只需要处理UI状态
    console.error('Error debugging tool:', error)
    debugResult.value = {
      success: false,
      error: error.response?.data?.message || error.message || '调试请求失败'
    }
    resultTabKey.value = 'logs'
  } finally {
    debugging.value = false
  }
}

// 格式化结果
const formatResult = (result) => {
  try {
    if (typeof result === 'object') {
      return JSON.stringify(result, null, 2)
    }
    return String(result)
  } catch (error) {
    return String(result)
  }
}
</script>

<style scoped>
.debug-container {
  display: flex;
  gap: 24px;
}

.debug-form {
  flex: 1;
  min-width: 0;
  padding-right: 12px;
  border-right: 1px solid #f0f0f0;
}

.debug-result {
  flex: 1;
  min-width: 0;
  padding-left: 12px;
}

h3 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.result-container {
  min-height: 300px;
}

.result-content {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.log-list {
  max-height: 400px;
  overflow-y: auto;
}

.error-alert {
  margin-bottom: 16px;
}
</style>
