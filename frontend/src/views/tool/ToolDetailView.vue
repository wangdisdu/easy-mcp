<template>
  <app-layout current-page-key="tool">
    <a-card v-if="tool">
      <template #title>
        <span>工具详情 - {{ tool.name }}</span>
        <a-tag v-if="tool.current_version" color="blue" class="version-tag">v{{ tool.current_version }}</a-tag>
      </template>
      <template #extra>
        <a-space>
          <a-button @click="router.push('/tool')">
            <template #icon><RollbackOutlined /></template>
            返回
          </a-button>
          <a-button type="primary" @click="router.push(`/tool/${toolId}/edit`)">
            <template #icon><EditOutlined /></template>
            编辑
          </a-button>

          <a-button type="primary" @click="router.push(`/tool/${toolId}/debug`)">
            <template #icon><BugOutlined /></template>
            调试
          </a-button>
          <a-button
            v-if="tool.is_enabled"
            type="primary"
            danger
            @click="handleToggleState(false)"
          >
            <template #icon><PauseCircleOutlined /></template>
            禁用
          </a-button>
          <a-button
            v-else
            type="primary"
            @click="handleToggleState(true)"
          >
            <template #icon><PlayCircleOutlined /></template>
            启用
          </a-button>
        </a-space>
      </template>

      <a-tabs v-model:activeKey="activeTabKey">
        <!-- 基本信息标签页 -->
        <a-tab-pane key="basic" tab="基本信息">
          <div class="info-container">
            <div class="info-row">
              <div class="info-label">工具名称:</div>
              <div class="info-value">{{ tool.name }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">工具描述:</div>
              <div class="info-value">{{ tool.description || '无描述' }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">状态:</div>
              <div class="info-value">
                <a-tag :color="tool.is_enabled ? 'green' : 'red'">
                  {{ tool.is_enabled ? '已启用' : '已禁用' }}
                </a-tag>
              </div>
            </div>
            <div class="info-row">
              <div class="info-label">当前版本:</div>
              <div class="info-value">{{ tool.current_version || '未发布' }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">创建时间:</div>
              <div class="info-value">{{ formatTimestamp(tool.created_at) }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">更新时间:</div>
              <div class="info-value">{{ formatTimestamp(tool.updated_at) }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">创建人:</div>
              <div class="info-value">{{ tool.created_by || '-' }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">更新人:</div>
              <div class="info-value">{{ tool.updated_by || '-' }}</div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 参数定义标签页 -->
        <a-tab-pane key="parameters" tab="参数定义">
          <a-empty v-if="!parametersSchema || !parametersSchema.properties || Object.keys(parametersSchema.properties).length === 0" description="无参数定义" />
          <div v-else class="parameters-container">
            <div v-for="(param, key) in parametersSchema.properties" :key="key" class="parameter-item">
              <div class="parameter-header">
                <span class="parameter-name">{{ param.title || key }}</span>
                <a-tag class="parameter-type">{{ param.type || 'string' }}</a-tag>
                <a-tag v-if="isRequired(key)" color="red">必填</a-tag>
              </div>
              <div v-if="param.description" class="parameter-description">
                {{ param.description }}
              </div>
              <div v-if="param.enum || param.default !== undefined || param.minimum !== undefined || param.maximum !== undefined || param.format || (param.items && param.items.type)" class="parameter-details">
                <div v-if="param.enum" class="parameter-enum">
                  <span class="parameter-detail-label">可选值:</span>
                  <div class="parameter-enum-values">
                    <a-tag v-for="(value, index) in param.enum" :key="index" color="blue">{{ value }}</a-tag>
                  </div>
                </div>
                <div v-if="param.format" class="parameter-format">
                  <span class="parameter-detail-label">格式:</span>
                  <span class="parameter-detail-value">{{ param.format }}</span>
                </div>
                <div v-if="param.items && param.items.type" class="parameter-items">
                  <span class="parameter-detail-label">元素类型:</span>
                  <span class="parameter-detail-value">{{ param.items.type }}</span>
                </div>
                <div v-if="param.default !== undefined" class="parameter-default">
                  <span class="parameter-detail-label">默认值:</span>
                  <span class="parameter-detail-value">{{ JSON.stringify(param.default) }}</span>
                </div>
                <div v-if="param.minimum !== undefined" class="parameter-min">
                  <span class="parameter-detail-label">最小值:</span>
                  <span class="parameter-detail-value">{{ param.minimum }}</span>
                </div>
                <div v-if="param.maximum !== undefined" class="parameter-max">
                  <span class="parameter-detail-label">最大值:</span>
                  <span class="parameter-detail-value">{{ param.maximum }}</span>
                </div>
                <div v-if="param.minLength !== undefined" class="parameter-min-length">
                  <span class="parameter-detail-label">最小长度:</span>
                  <span class="parameter-detail-value">{{ param.minLength }}</span>
                </div>
                <div v-if="param.maxLength !== undefined" class="parameter-max-length">
                  <span class="parameter-detail-label">最大长度:</span>
                  <span class="parameter-detail-value">{{ param.maxLength }}</span>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 工具代码标签页 -->
        <a-tab-pane key="code" tab="工具代码">
          <div class="code-container">
            <pre class="code-display">{{ tool.code }}</pre>
          </div>
        </a-tab-pane>

        <!-- 发布历史标签页 -->
        <a-tab-pane key="history" tab="发布历史">
          <a-empty v-if="!deployHistory.length" description="无发布历史" />
          <div v-else class="version-list">
            <div v-for="record in deployHistory" :key="record.id" class="version-item">
              <div class="version-row">
                <div class="version-label">版本:</div>
                <a-tag
                  class="version-tag"
                  :color="tool.current_version === record.version ? 'blue' : 'default'"
                  @click="showVersionCode(record)"
                >
                  v{{ record.version }}
                </a-tag>

                <div class="version-label time-label">发布时间:</div>
                <span class="version-time">{{ formatTimestamp(record.created_at) }}</span>

                <a-button
                  type="primary"
                  size="small"
                  :disabled="tool.current_version === record.version"
                  class="rollback-button"
                  @click="showRollbackConfirm(record)"
                >
                  <template #icon><RollbackOutlined /></template>
                  回滚
                </a-button>
              </div>
              <div v-if="record.description" class="version-description">
                {{ record.description }}
              </div>
            </div>
          </div>

          <!-- 版本代码对话框 -->
          <a-modal
            v-model:open="versionCodeVisible"
            :title="`工具代码 (v${selectedVersion})`"
            width="800px"
            :footer="null"
          >
            <pre class="code-display">{{ versionCode }}</pre>
          </a-modal>

          <!-- 回滚确认对话框 -->
          <a-modal
            v-model:open="rollbackConfirmVisible"
            :title="`确认回滚到版本 v${selectedVersion}?`"
            width="800px"
            :confirm-loading="rollingBack"
            ok-text="确认回滚"
            cancel-text="取消"
            @ok="confirmRollback"
          >
            <div class="rollback-warning">
              <a-alert
                message="警告"
                description="回滚操作将使当前工具代码替换为选中版本的代码，请确认该操作。"
                type="warning"
                show-icon
                style="margin-bottom: 16px;"
              />
            </div>
            <div class="rollback-code-container">
              <div class="rollback-code-header">版本 v{{ selectedVersion }} 的代码:</div>
              <pre class="code-display">{{ versionCode }}</pre>
            </div>
          </a-modal>
        </a-tab-pane>

        <!-- 绑定配置标签页 -->
        <a-tab-pane key="configs" tab="绑定配置">
          <a-empty v-if="!relatedConfigs.length" description="无绑定配置" />
          <a-list v-else>
            <a-list-item v-for="config in relatedConfigs" :key="config.id">
              <a-list-item-meta>
                <template #avatar>
                  <SettingOutlined class="config-icon" />
                </template>
                <template #title>
                  <a
                    class="config-link"
                    @click="router.push(`/config/${config.id}`)"
                  >
                    {{ config.name }}
                  </a>
                </template>
                <template #description>
                  <div class="config-description">{{ config.description || '无描述' }}</div>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </a-list>
        </a-tab-pane>

        <!-- 依赖函数标签页 -->
        <a-tab-pane key="funcs" tab="依赖函数">
          <a-empty v-if="!relatedFuncs.length" description="无依赖函数" />
          <a-list v-else>
            <a-list-item v-for="func in relatedFuncs" :key="func.id">
              <a-list-item-meta>
                <template #avatar>
                  <FunctionOutlined class="func-icon" />
                </template>
                <template #title>
                  <a
                    class="func-link"
                    @click="router.push(`/func/${func.id}`)"
                  >
                    {{ func.name }}
                  </a>
                </template>
                <template #description>
                  <div class="func-description">{{ func.description || '无描述' }}</div>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </a-list>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 发布模态框 -->
    <a-modal
      v-model:open="deployModalVisible"
      title="发布工具"
      :confirm-loading="deploying"
      ok-text="确定"
      cancel-text="取消"
      @ok="confirmDeploy"
    >
      <a-form layout="vertical">
        <a-form-item label="发布描述">
          <a-textarea
            v-model:value="deployDescription"
            :rows="4"
            placeholder="请输入发布描述"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </app-layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  RollbackOutlined,
  EditOutlined,
  CloudUploadOutlined,
  BugOutlined,
  SettingOutlined,
  FunctionOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, formatTimestamp, validateJson } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import MonacoEditor from '../../components/MonacoEditor.vue'

const router = useRouter()
const route = useRoute()
const toolId = computed(() => route.params.id)

const loading = ref(false)
const tool = ref(null)
const deployHistory = ref([])
const loadingHistory = ref(false)
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyTotal = ref(0)
const activeTabKey = ref('basic')
const relatedConfigs = ref([])
const relatedFuncs = ref([])
const versionCodeVisible = ref(false)
const rollbackConfirmVisible = ref(false)
const selectedVersion = ref(null)
const versionCode = ref('')
const selectedRecord = ref(null)
const rollingBack = ref(false)

// Debug functionality moved to ToolDebugView.vue

// Deploy modal
const deployModalVisible = ref(false)
const deployDescription = ref('')
const deploying = ref(false)

const historyColumns = [
  {
    title: '版本',
    key: 'version',
    width: 100
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true
  },
  {
    title: '发布时间',
    key: 'created_at',
    width: 180
  },
  {
    title: '发布人',
    dataIndex: 'created_by',
    key: 'created_by',
    width: 120
  },
  {
    title: '操作',
    key: 'action',
    width: 150
  }
]

const parametersSchema = computed(() => {
  if (!tool.value || !tool.value.parameters) return null
  return tool.value.parameters
})

const isRequired = (key) => {
  if (!parametersSchema.value || !parametersSchema.value.required) return false
  return parametersSchema.value.required.includes(key)
}

onMounted(() => {
  fetchToolData()
  fetchDeployHistory()
  fetchBoundConfigs()
  fetchDependentFuncs()
})

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
  } finally {
    loading.value = false
  }
}

const fetchDeployHistory = async () => {
  loadingHistory.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${toolId.value}/deploy/history`,
      params: {
        page: historyPage.value,
        size: historyPageSize.value
      },
      onSuccess: (data, response) => {
        deployHistory.value = data
        historyTotal.value = response.total
      },
      errorMessage: '获取发布历史失败'
    })
  } finally {
    loadingHistory.value = false
  }
}

const fetchBoundConfigs = async () => {
  try {
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${toolId.value}/config`,
      onSuccess: (data) => {
        relatedConfigs.value = data || []
      },
      errorMessage: '获取绑定配置失败'
    })
  } catch (error) {
    console.error('Error fetching bound configs:', error)
  }
}

const fetchDependentFuncs = async () => {
  try {
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${toolId.value}/func`,
      onSuccess: (data) => {
        relatedFuncs.value = data || []
      },
      errorMessage: '获取依赖函数失败'
    })
  } catch (error) {
    console.error('Error fetching dependent functions:', error)
  }
}

const handleHistoryPageChange = (page, pageSize) => {
  historyPage.value = page
  historyPageSize.value = pageSize
  fetchDeployHistory()
}

const showVersionCode = async (record) => {
  try {
    selectedVersion.value = record.version

    // If we already have the code in the record, use it
    if (record.code) {
      versionCode.value = record.code
      versionCodeVisible.value = true
      return
    }

    // Otherwise fetch the code for this version
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${toolId.value}/version/${record.version}`,
      onSuccess: (data) => {
        versionCode.value = data.code || '// No code available for this version'
        versionCodeVisible.value = true
      },
      errorMessage: '获取工具代码失败'
    })
  } catch (error) {
    console.error('Error fetching version code:', error)
    message.error('获取工具代码失败')
  }
}

const showRollbackConfirm = async (record) => {
  try {
    selectedVersion.value = record.version
    selectedRecord.value = record

    // If we already have the code in the record, use it
    if (record.code) {
      versionCode.value = record.code
      rollbackConfirmVisible.value = true
      return
    }

    // Otherwise fetch the code for this version
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${toolId.value}/version/${record.version}`,
      onSuccess: (data) => {
        versionCode.value = data.code || '// No code available for this version'
        rollbackConfirmVisible.value = true
      },
      errorMessage: '获取工具代码失败'
    })
  } catch (error) {
    console.error('Error fetching version code:', error)
    message.error('获取工具代码失败')
  }
}

const confirmRollback = async () => {
  if (!selectedVersion.value) return

  rollingBack.value = true

  try {
    await callApi({
      method: 'post',
      url: `/api/v1/tool/${toolId.value}/deploy/rollback/${selectedVersion.value}`,
      successMessage: '回滚成功',
      errorMessage: '回滚失败',
      onSuccess: () => {
        // Refresh data
        fetchToolData()
        rollbackConfirmVisible.value = false
      }
    })
  } catch (error) {
    console.error('Error rolling back tool:', error)
  } finally {
    rollingBack.value = false
  }
}

// Debug functions moved to ToolDebugView.vue

const showDeployModal = () => {
  deployModalVisible.value = true
  deployDescription.value = ''
}

const handleDeploy = () => {
  showDeployModal()
}

const confirmDeploy = async () => {
  deploying.value = true

  try {
    await callApi({
      method: 'post',
      url: `/api/v1/tool/${toolId.value}/deploy`,
      data: {
        description: deployDescription.value
      },
      successMessage: '发布成功',
      errorMessage: '发布失败',
      onSuccess: () => {
        deployModalVisible.value = false
        // Refresh data
        fetchToolData()
        fetchDeployHistory()
      }
    })
  } finally {
    deploying.value = false
  }
}

const handleToggleState = async (enable) => {
  try {
    const action = enable ? 'enable' : 'disable'
    await callApi({
      method: 'patch',
      url: `/api/v1/tool/${toolId.value}/${action}`,
      successMessage: `${enable ? '启用' : '禁用'}成功`,
      errorMessage: `${enable ? '启用' : '禁用'}失败`,
      onSuccess: () => {
        // Refresh tool data
        fetchToolData()
      }
    })
  } catch (error) {
    console.error(`Error ${enable ? 'enabling' : 'disabling'} tool:`, error)
  }
}
</script>

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

.code-container {
  margin: 8px 0;
}

.code-display {
  background-color: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 16px;
  font-family: 'Courier New', Courier, monospace;
  white-space: pre-wrap;
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.version-item {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 12px 16px;
  background-color: #fafafa;
  transition: background-color 0.3s;
}

.version-item:hover {
  background-color: #f0f8ff;
}

.version-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.version-label {
  font-weight: 500;
  color: #606060;
}

.time-label {
  margin-left: 16px;
}

.version-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.version-tag:hover {
  opacity: 0.8;
  transform: scale(1.05);
}

.version-time {
  color: #595959;
}

.rollback-button {
  margin-left: auto;
}

.version-description {
  margin-top: 8px;
  color: #8c8c8c;
  font-size: 13px;
  white-space: pre-line;
  border-top: 1px dashed #f0f0f0;
  padding-top: 8px;
}

.rollback-code-header {
  font-weight: 500;
  margin-bottom: 8px;
  color: #262626;
}

.config-icon,
.func-icon {
  color: #1890ff;
  font-size: 20px;
}

.config-link,
.func-link {
  color: #1890ff;
  font-weight: 500;
}

.config-link:hover,
.func-link:hover {
  color: #40a9ff;
  text-decoration: underline;
}

.config-description,
.func-description {
  color: #606060;
  font-size: 13px;
}

.version-tag {
  margin-left: 8px;
}

/* Parameters styles */
.parameters-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px;
}

.parameter-item {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 16px;
  background-color: #fafafa;
}

.parameter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.parameter-name {
  font-weight: 500;
  font-size: 16px;
  color: #262626;
}

.parameter-type {
  font-size: 12px;
  background-color: #e6f7ff;
  color: #1890ff;
}

.parameter-description {
  color: #595959;
  margin-bottom: 12px;
  font-size: 14px;
}

.parameter-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-top: 1px dashed #f0f0f0;
  padding-top: 12px;
}

.parameter-enum,
.parameter-default,
.parameter-min,
.parameter-max,
.parameter-format,
.parameter-items,
.parameter-min-length,
.parameter-max-length {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.parameter-detail-label {
  font-weight: 500;
  color: #8c8c8c;
  width: 60px;
}

.parameter-detail-value {
  color: #262626;
}

.parameter-enum-values {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
