<template>
  <app-layout current-page-key="func">
    <a-card v-if="func">
      <template #title>
        <span>函数详情 - {{ func.name }}</span>
        <a-tag v-if="func.current_version" color="blue" class="version-tag">v{{ func.current_version }}</a-tag>
      </template>
      <template #extra>
        <a-space>
          <a-button @click="router.push('/func')">
            <template #icon><RollbackOutlined /></template>
            返回
          </a-button>
          <a-button type="primary" @click="router.push(`/func/${funcId}/edit`)">
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
              <div class="info-label">函数名称:</div>
              <div class="info-value">{{ func.name }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">函数描述:</div>
              <div class="info-value">{{ func.description || '无描述' }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">当前版本:</div>
              <div class="info-value">{{ func.current_version || '未发布' }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">创建时间:</div>
              <div class="info-value">{{ formatTimestamp(func.created_at) }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">更新时间:</div>
              <div class="info-value">{{ formatTimestamp(func.updated_at) }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">创建人:</div>
              <div class="info-value">{{ func.created_by || '-' }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">更新人:</div>
              <div class="info-value">{{ func.updated_by || '-' }}</div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 函数代码标签页 -->
        <a-tab-pane key="code" tab="函数代码">
          <div class="code-container">
            <pre class="code-display">{{ func.code }}</pre>
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
                  :color="func.current_version === record.version ? 'blue' : 'default'"
                  @click="showVersionCode(record)"
                >
                  v{{ record.version }}
                </a-tag>

                <div class="version-label time-label">发布时间:</div>
                <span class="version-time">{{ formatTimestamp(record.created_at) }}</span>

                <a-button
                  type="primary"
                  size="small"
                  :disabled="func.current_version === record.version"
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
            :title="`函数代码 (v${selectedVersion})`"
            width="800px"
            footer="{null}"
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
                description="回滚操作将使当前函数代码替换为选中版本的代码，请确认该操作。"
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

        <!-- 依赖函数标签页 -->
        <a-tab-pane key="dependencies" tab="依赖函数">
          <a-empty v-if="!dependencies.length" description="无依赖函数" />
          <a-list v-else>
            <a-list-item v-for="dep in dependencies" :key="dep.id">
              <a-list-item-meta>
                <template #avatar>
                  <FunctionOutlined class="func-icon" />
                </template>
                <template #title>
                  <a
                    class="func-link"
                    @click="router.push(`/func/${dep.id}`)"
                  >
                    {{ dep.name }}
                  </a>
                </template>
                <template #description>
                  {{ dep.description || '无描述' }}
                </template>
              </a-list-item-meta>
            </a-list-item>
          </a-list>
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
                    class="tool-link"
                    @click="router.push(`/tool/${tool.id}`)"
                  >
                    {{ tool.name }}
                  </a>
                </template>
                <template #description>
                  {{ tool.description || '无描述' }}
                </template>
              </a-list-item-meta>
            </a-list-item>
          </a-list>
        </a-tab-pane>

        <!-- 关联函数标签页 -->
        <a-tab-pane key="dependent-funcs" tab="关联函数">
          <a-empty v-if="!dependentFuncs.length" description="无关联函数" />
          <a-list v-else>
            <a-list-item v-for="depFunc in dependentFuncs" :key="depFunc.id">
              <a-list-item-meta>
                <template #avatar>
                  <FunctionOutlined class="func-icon" />
                </template>
                <template #title>
                  <a
                    class="func-link"
                    @click="router.push(`/func/${depFunc.id}`)"
                  >
                    {{ depFunc.name }}
                  </a>
                </template>
                <template #description>
                  {{ depFunc.description || '无描述' }}
                </template>
              </a-list-item-meta>
            </a-list-item>
          </a-list>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- Deploy modal removed -->
  </app-layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  RollbackOutlined,
  EditOutlined,
  InfoCircleOutlined,
  ToolOutlined,
  FunctionOutlined,
  HistoryOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import MonacoEditor from '../../components/MonacoEditor.vue'

const router = useRouter()
const route = useRoute()
const funcId = computed(() => route.params.id)

const loading = ref(false)
const func = ref(null)
const dependencies = ref([])
const dependentFuncs = ref([])
const relatedTools = ref([])
const deployHistory = ref([])
const loadingHistory = ref(false)
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyTotal = ref(0)
const activeTabKey = ref('basic')
const versionCodeVisible = ref(false)
const rollbackConfirmVisible = ref(false)
const selectedVersion = ref(null)
const versionCode = ref('')
const selectedRecord = ref(null)
const rollingBack = ref(false)

// No deploy functionality

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

onMounted(() => {
  fetchFuncData()
  fetchUsageInfo()
  fetchDependencies()
  fetchDeployHistory()
})

const fetchFuncData = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/func/${funcId.value}`,
      onSuccess: (data) => {
        func.value = data
      },
      errorMessage: '获取函数数据失败'
    })
  } finally {
    loading.value = false
  }
}

const fetchUsageInfo = async () => {
  try {
    await callApi({
      method: 'get',
      url: `/api/v1/func/${funcId.value}/usage`,
      onSuccess: (data) => {
        if (data) {
          relatedTools.value = data.tools || []
          dependentFuncs.value = data.funcs || []
        }
      },
      errorMessage: '获取使用信息失败'
    })
  } catch (error) {
    console.error('Error fetching usage info:', error)
  }
}

const fetchDependencies = async () => {
  try {
    await callApi({
      method: 'get',
      url: `/api/v1/func/${funcId.value}/depend`,
      onSuccess: (data) => {
        dependencies.value = data || []
      },
      errorMessage: '获取依赖函数失败'
    })
  } catch (error) {
    console.error('Error fetching dependencies:', error)
  }
}

const fetchDeployHistory = async () => {
  loadingHistory.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/func/${funcId.value}/deploy/history`,
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

const handleHistoryPageChange = (page, pageSize) => {
  historyPage.value = page
  historyPageSize.value = pageSize
  fetchDeployHistory()
}

// Deploy functionality removed

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
      url: `/api/v1/func/${funcId.value}/version/${record.version}`,
      onSuccess: (data) => {
        versionCode.value = data.code || '// No code available for this version'
        rollbackConfirmVisible.value = true
      },
      errorMessage: '获取函数代码失败'
    })
  } catch (error) {
    console.error('Error fetching version code:', error)
    message.error('获取函数代码失败')
  }
}

const confirmRollback = async () => {
  if (!selectedVersion.value) return

  rollingBack.value = true

  try {
    await callApi({
      method: 'post',
      url: `/api/v1/func/${funcId.value}/deploy/rollback/${selectedVersion.value}`,
      successMessage: '回滚成功',
      errorMessage: '回滚失败',
      onSuccess: () => {
        // Refresh data
        fetchFuncData()
        rollbackConfirmVisible.value = false
      }
    })
  } catch (error) {
    console.error('Error rolling back function:', error)
  } finally {
    rollingBack.value = false
  }
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
      url: `/api/v1/func/${funcId.value}/version/${record.version}`,
      onSuccess: (data) => {
        versionCode.value = data.code || '// No code available for this version'
        versionCodeVisible.value = true
      },
      errorMessage: '获取函数代码失败'
    })
  } catch (error) {
    console.error('Error fetching version code:', error)
    message.error('获取函数代码失败')
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

.version-tag {
  margin-left: 8px;
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

.tool-icon,
.func-icon {
  color: #1890ff;
  font-size: 20px;
}

.tool-link,
.func-link {
  color: #1890ff;
  font-weight: 500;
}

.tool-link:hover,
.func-link:hover {
  color: #40a9ff;
  text-decoration: underline;
}

.tool-description,
.func-description {
  color: #606060;
  font-size: 13px;
}
</style>
