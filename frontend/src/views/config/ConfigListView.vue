<template>
  <app-layout current-page-key="config">
    <a-card title="配置管理">
      <div class="action-bar">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索配置名称或描述"
          style="width: 300px"
          @search="handleSearch"
        />

        <a-button type="primary" @click="router.push('/config/create')">
          <template #icon><PlusOutlined /></template>
          创建配置
        </a-button>
      </div>

      <a-table
        :columns="columns"
        :data-source="configs"
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
      >
        <!-- 名称列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <a @click="router.push(`/config/${record.id}`)">{{ record.name }}</a>
          </template>

          <!-- 描述列 -->
          <template v-else-if="column.key === 'description'">
            <span>{{ record.description || '无描述' }}</span>
          </template>

          <!-- 创建时间列 -->
          <template v-else-if="column.key === 'created_at'">
            <span>{{ formatTimestamp(record.created_at) }}</span>
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space :size="0">
              <a-button type="link" size="small" @click="openConfigModal(record)">
                <template #icon><SettingOutlined /></template>
                配置
              </a-button>
              <a-button type="link" size="small" @click="router.push(`/config/${record.id}/edit`)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除此配置吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDelete(record.id)"
              >
                <a-button type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>

      <!-- 配置弹窗 -->
      <a-modal
        v-model:open="configModalVisible"
        :title="`配置设置: ${currentConfig?.name || ''}`"
        width="800px"
        :footer="null"
        @cancel="closeConfigModal"
      >
        <template v-if="currentConfig">
          <div v-if="!currentConfig.conf_schema || Object.keys(currentConfig.conf_schema).length === 0" class="empty-schema">
            <a-empty description="没有可用的配置模式" />
          </div>
          <div v-else>
            <JsonSchemaForm
              :schema="currentConfig.conf_schema"
              v-model:value="configFormValue"
              :loading="configFormLoading"
              @submit="saveConfigValue"
              @cancel="closeConfigModal"
            />
          </div>
        </template>
      </a-modal>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  SettingOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import JsonSchemaForm from '../../components/JsonSchemaForm.vue'

const router = useRouter()
const loading = ref(false)
const configs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchText = ref('')

// 配置弹窗相关
const configModalVisible = ref(false)
const currentConfig = ref(null)
const configFormLoading = ref(false)
const configFormValue = ref({})

const columns = [
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name',
    width: 160,
    ellipsis: true,
    tooltip: true
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    width: 200,
    ellipsis: true,
    tooltip: true
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right'
  }
]

onMounted(() => {
  fetchConfigs()
})

const fetchConfigs = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/config',
      params: {
        page: currentPage.value,
        size: pageSize.value,
        search: searchText.value || undefined
      },
      onSuccess: (data, response) => {
        configs.value = data
        total.value = response.total
      },
      errorMessage: '获取配置列表失败'
    })
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchConfigs()
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
  fetchConfigs()
}

const handlePageSizeChange = (current, size) => {
  currentPage.value = 1
  pageSize.value = size
  fetchConfigs()
}

const handleDelete = async (id) => {
  try {
    await callApi({
      method: 'delete',
      url: `/api/v1/config/${id}`,
      successMessage: '删除成功',
      errorMessage: '删除失败'
    })

    // Refresh list
    fetchConfigs()
  } catch (error) {
    console.error('Error deleting config:', error)
  }
}

// 打开配置弹窗
const openConfigModal = (config) => {
  currentConfig.value = config
  configFormValue.value = config.conf_value || {}
  configModalVisible.value = true
}

// 关闭配置弹窗
const closeConfigModal = () => {
  configModalVisible.value = false
  currentConfig.value = null
  configFormValue.value = {}
}

// 保存配置值
const saveConfigValue = async (formData) => {
  if (!currentConfig.value) return

  configFormLoading.value = true

  try {
    await callApi({
      method: 'put',
      url: `/api/v1/config/${currentConfig.value.id}/value`,
      data: {
        conf_value: formData
      },
      successMessage: '配置保存成功',
      errorMessage: '配置保存失败'
    })

    // 刷新列表
    fetchConfigs()

    // 关闭弹窗
    closeConfigModal()
  } catch (error) {
    console.error('Error saving config value:', error)
  } finally {
    configFormLoading.value = false
  }
}
</script>

<style scoped>
.action-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.empty-schema {
  padding: 40px 0;
  text-align: center;
}
</style>
