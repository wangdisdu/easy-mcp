<template>
  <app-layout current-page-key="config">
    <a-card title="配置详情" v-if="config">
      <template #extra>
        <a-space>
          <a-button @click="router.push('/config')">
            <template #icon><RollbackOutlined /></template>
            返回
          </a-button>
          <a-button type="primary" @click="router.push(`/config/${configId}/edit`)">
            <template #icon><EditOutlined /></template>
            编辑
          </a-button>
        </a-space>
      </template>

      <a-tabs v-model:activeKey="activeTabKey">
        <!-- 基本信息标签页 -->
        <a-tab-pane key="basic" tab="基本信息">
          <div class="info-container">
            <div class="info-row">
              <div class="info-label">配置名称:</div>
              <div class="info-value">{{ config.name }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">配置描述:</div>
              <div class="info-value">{{ config.description || '无描述' }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">创建时间:</div>
              <div class="info-value">{{ formatTimestamp(config.created_at) }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">更新时间:</div>
              <div class="info-value">{{ formatTimestamp(config.updated_at) }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">创建人:</div>
              <div class="info-value">{{ config.created_by || '-' }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">更新人:</div>
              <div class="info-value">{{ config.updated_by || '-' }}</div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 配置信息标签页 -->
        <a-tab-pane key="config" tab="配置信息">
          <div v-if="!config.conf_schema" class="empty-message">
            <a-empty description="无配置架构" />
          </div>
          <div v-else>
            <a-alert
              v-if="!isValidSchema"
              type="warning"
              message="配置架构不是有效的JSON Schema格式"
              banner
              style="margin-bottom: 16px;"
            />
            <div v-else-if="!hasConfigValue" class="empty-message">
              <a-empty description="无配置值" />
            </div>
            <div v-else>
              <!-- 根据schema动态渲染配置值 -->
              <div v-for="(value, key) in configValue" :key="key" class="config-item">
                <div class="config-item-row">
                  <div class="config-item-label">
                    {{ getPropertyLabel(key) }}
                    <a-tooltip placement="right" v-if="config.value && config.value.conf_schema && config.value.conf_schema.properties && config.value.conf_schema.properties[key]">
                      <template #title>
                        <div>
                          <div><strong>类型：</strong> {{ getPropertyType(key) }}</div>
                          <div v-if="getPropertyDescription(key)"><strong>描述：</strong> {{ getPropertyDescription(key) }}</div>
                          <div v-if="getPropertyRequired(key)"><strong>必填：</strong> 是</div>
                          <div v-if="getPropertyDefault(key) !== undefined"><strong>默认值：</strong> {{ JSON.stringify(getPropertyDefault(key)) }}</div>
                        </div>
                      </template>
                      <QuestionCircleOutlined class="config-item-icon" />
                    </a-tooltip>
                  </div>
                  <div class="config-item-value">
                    <pre v-if="isObjectOrArray(value)">{{ JSON.stringify(value, null, 2) }}</pre>
                    <span v-else>{{ value }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 关联工具标签页 -->
        <a-tab-pane key="tools" tab="关联工具">
          <a-empty v-if="!relatedTools.length" description="无关联工具" />
          <a-list v-else>
            <a-list-item v-for="tool in relatedTools" :key="tool.id">
              <a-list-item-meta>
                <template #avatar>
                  <ToolOutlined class="tool-icon" />
                </template>
                <template #title>
                  <a
                    @click="router.push(`/tool/${tool.id}`)"
                    class="tool-link"
                  >
                    {{ tool.name }}
                  </a>
                </template>
                <template #description>
                  <div class="tool-description">{{ tool.description || '无描述' }}</div>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </a-list>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </app-layout>
</template>

<style scoped>
.info-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px;
}

.info-row {
  display: flex;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 8px;
}

.info-label {
  width: 120px;
  font-weight: 500;
  color: #606060;
}

.info-value {
  flex: 1;
}

.config-item {
  margin-bottom: 16px;
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
}

.config-item-row {
  display: flex;
  align-items: flex-start;
}

.config-item-label {
  width: 180px;
  font-weight: 500;
  color: #606060;
  padding-top: 8px;
  padding-right: 16px;
  display: flex;
  align-items: center;
}

.config-item-icon {
  margin-left: 6px;
  color: #bfbfbf;
  font-size: 14px;
  cursor: help;
}

.config-item-value {
  flex: 1;
  background-color: #fafafa;
  padding: 8px 12px;
  border-radius: 4px;
  overflow-x: auto;
  min-height: 36px;
  display: flex;
  align-items: center;
}

.config-item-value pre {
  margin: 0;
  width: 100%;
}

.empty-message {
  padding: 24px 0;
}

.tool-icon {
  color: #1890ff;
  font-size: 20px;
}

.tool-link {
  color: #1890ff;
  font-weight: 500;
}

.tool-link:hover {
  color: #40a9ff;
  text-decoration: underline;
}

.tool-description {
  color: #606060;
  font-size: 13px;
}

</style>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  RollbackOutlined,
  EditOutlined,
  QuestionCircleOutlined,
  ToolOutlined
} from '@ant-design/icons-vue'
import { callApi, formatTimestamp, validateJson } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

const router = useRouter()
const route = useRoute()
const configId = computed(() => route.params.id)

const loading = ref(false)
const config = ref(null)
const relatedTools = ref([])
const activeTabKey = ref('basic')

// 计算属性：配置架构是否有效
const isValidSchema = computed(() => {
  if (!config.value || !config.value.conf_schema) return false
  try {
    const schema = config.value.conf_schema
    return schema && schema.type === 'object' && schema.properties
  } catch (e) {
    console.error('Error validating schema:', e)
    return false
  }
})

// 计算属性：配置值
const configValue = computed(() => {
  if (!config.value || !config.value.conf_value) return {}
  try {
    // If conf_value is a string, try to parse it as JSON
    if (typeof config.value.conf_value === 'string') {
      return JSON.parse(config.value.conf_value)
    }
    // If it's already an object, return it directly
    return config.value.conf_value
  } catch (e) {
    console.error('Error parsing configuration value:', e)
    return {}
  }
})

// 计算属性：是否有配置值
const hasConfigValue = computed(() => {
  return configValue.value && Object.keys(configValue.value).length > 0
})

// 获取属性标签
const getPropertyLabel = (key) => {
  if (!isValidSchema.value || !config.value || !config.value.conf_schema || !config.value.conf_schema.properties) return key

  const schema = config.value.conf_schema
  const property = schema.properties[key]

  // Handle case when property is undefined (might be a nested property)
  if (!property) {
    // For nested properties, just return the key as is
    return key
  }

  return property.title || key
}

// 获取属性类型
const getPropertyType = (key) => {
  if (!isValidSchema.value || !config.value || !config.value.conf_schema || !config.value.conf_schema.properties) return 'unknown'

  const schema = config.value.conf_schema
  const property = schema.properties[key]

  // Handle case when property is undefined (might be a nested property)
  if (!property) {
    return 'object'
  }

  return property.type || 'unknown'
}

// 获取属性描述
const getPropertyDescription = (key) => {
  if (!isValidSchema.value || !config.value || !config.value.conf_schema || !config.value.conf_schema.properties) return ''

  const schema = config.value.conf_schema
  const property = schema.properties[key]

  // Handle case when property is undefined (might be a nested property)
  if (!property) {
    return ''
  }

  return property.description || ''
}

// 获取属性是否必填
const getPropertyRequired = (key) => {
  if (!isValidSchema.value || !config.value || !config.value.conf_schema || !config.value.conf_schema.properties) return false

  const schema = config.value.conf_schema

  // For nested properties, we can't easily determine if they're required
  if (!schema.properties[key]) {
    return false
  }

  return schema.required && schema.required.includes(key)
}

// 获取属性默认值
const getPropertyDefault = (key) => {
  if (!isValidSchema.value || !config.value || !config.value.conf_schema || !config.value.conf_schema.properties) return undefined

  const schema = config.value.conf_schema
  const property = schema.properties[key]

  // Handle case when property is undefined (might be a nested property)
  if (!property) {
    return undefined
  }

  return property.default
}

// 判断值是否为对象或数组
const isObjectOrArray = (value) => {
  return typeof value === 'object' && value !== null
}

onMounted(() => {
  fetchConfigData()
  fetchRelatedTools()
})

const fetchConfigData = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/config/${configId.value}`,
      onSuccess: (data) => {
        // Ensure conf_schema is parsed as an object
        if (data && data.conf_schema && typeof data.conf_schema === 'string') {
          try {
            data.conf_schema = JSON.parse(data.conf_schema)
          } catch (e) {
            console.error('Error parsing conf_schema:', e)
            data.conf_schema = {}
          }
        }

        // Store the config data
        config.value = data
      },
      errorMessage: '获取配置数据失败'
    })
  } catch (error) {
    console.error('Error fetching config data:', error)
  } finally {
    loading.value = false
  }
}

const fetchRelatedTools = async () => {
  try {
    await callApi({
      method: 'get',
      url: `/api/v1/config/${configId.value}/usage`,
      onSuccess: (data) => {
        relatedTools.value = data.tools || []
      },
      errorMessage: '获取关联工具失败'
    })
  } catch (error) {
    console.error('Error fetching related tools:', error)
  }
}
</script>
