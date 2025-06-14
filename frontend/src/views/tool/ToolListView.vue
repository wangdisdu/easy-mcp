<template>
  <app-layout current-page-key="tool">
    <a-card title="工具管理">
      <div class="action-bar">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索工具名称或描述"
          style="width: 300px"
          @search="handleSearch"
        />

        <div>
          <a-dropdown>
            <a-button type="primary" style="margin-right: 8px">
              <template #icon><PlusOutlined /></template>
              创建工具
              <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="basic" @click="router.push('/tool/create?type=basic')">
                  <ToolOutlined />
                  基础工具
                </a-menu-item>
                <a-menu-item key="http" @click="router.push('/tool/create?type=http')">
                  <GlobalOutlined />
                  HTTP工具
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
          <a-dropdown>
            <a-button>
              <template #icon><ImportOutlined /></template>
              导入工具
              <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="1" @click="showImportDialog = true">
                  <ApiOutlined />
                  导入内置工具
                </a-menu-item>
                <a-menu-item key="2" @click="router.push('/tool/import-openapi')">
                  <CloudOutlined />
                  导入OpenAPI
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="tools"
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
            <a @click="router.push(`/tool/${record.id}`)">{{ record.name }}</a>
          </template>

          <!-- 描述列 -->
          <template v-else-if="column.key === 'description'">
            <span>{{ record.description || '无描述' }}</span>
          </template>

          <!-- 类型列 -->
          <template v-else-if="column.key === 'type'">
            <a-tag :color="record.type === 'http' ? 'blue' : 'green'">
              {{ record.type === 'http' ? 'HTTP工具' : '基础工具' }}
            </a-tag>
          </template>

          <!-- 状态列 -->
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.is_enabled ? 'green' : 'red'">
              {{ record.is_enabled ? '已启用' : '已禁用' }}
            </a-tag>
          </template>

          <!-- 版本列 -->
          <template v-else-if="column.key === 'version'">
            <a-tag v-if="record.current_version" color="blue">v{{ record.current_version }}</a-tag>
            <span v-else>未发布</span>
          </template>

          <!-- 创建时间列 -->
          <template v-else-if="column.key === 'created_at'">
            <span>{{ formatTimestamp(record.created_at) }}</span>
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="router.push(`/tool/${record.id}`)">
                <template #icon><EyeOutlined /></template>
                查看
              </a-button>
              <a-button type="link" size="small" @click="router.push(`/tool/${record.id}/edit`)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-button
                v-if="record.is_enabled"
                type="link"
                size="small"
                @click="handleToggleState(record.id, false)"
              >
                <template #icon><PauseCircleOutlined /></template>
                禁用
              </a-button>
              <a-button
                v-else
                type="link"
                size="small"
                @click="handleToggleState(record.id, true)"
              >
                <template #icon><PlayCircleOutlined /></template>
                启用
              </a-button>
              <a-popconfirm
                title="确定要删除此工具吗？"
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
    </a-card>

    <!-- 导入工具对话框 -->
    <import-tool-dialog
      :visible="showImportDialog"
      @update:visible="showImportDialog = $event"
      @imported="fetchTools"
    />
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
  PlayCircleOutlined,
  PauseCircleOutlined,
  ImportOutlined,
  ApiOutlined,
  DownOutlined,
  ToolOutlined,
  CloudOutlined,
  GlobalOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import ImportToolDialog from './ImportToolDialog.vue'

const router = useRouter()
const loading = ref(false)
const tools = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchText = ref('')
const showImportDialog = ref(false)

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
    title: '类型',
    dataIndex: 'type',
    key: 'type',
    width: 100
  },
  {
    title: '状态',
    key: 'status',
    width: 100
  },
  {
    title: '版本',
    key: 'version',
    width: 100,
    ellipsis: true,
    tooltip: true
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160,
    ellipsis: true,
    tooltip: true
  },
  {
    title: '操作',
    key: 'action',
    width: 280,
    fixed: 'right'
  }
]

onMounted(() => {
  fetchTools()
})

const fetchTools = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/tool',
      params: {
        page: currentPage.value,
        size: pageSize.value,
        search: searchText.value || undefined
      },
      onSuccess: (data, response) => {
        tools.value = data
        total.value = response.total
      },
      errorMessage: '获取工具列表失败'
    })
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTools()
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
  fetchTools()
}

const handlePageSizeChange = (current, size) => {
  currentPage.value = 1
  pageSize.value = size
  fetchTools()
}

const handleDelete = async (id) => {
  try {
    await callApi({
      method: 'delete',
      url: `/api/v1/tool/${id}`,
      successMessage: '删除成功',
      errorMessage: '删除失败'
    })

    // Refresh list
    fetchTools()
  } catch (error) {
    console.error('Error deleting tool:', error)
  }
}

const handleToggleState = async (id, enable) => {
  try {
    const action = enable ? 'enable' : 'disable'
    await callApi({
      method: 'patch',
      url: `/api/v1/tool/${id}/${action}`,
      successMessage: `${enable ? '启用' : '禁用'}成功`,
      errorMessage: `${enable ? '启用' : '禁用'}失败`
    })

    // Refresh list
    fetchTools()
  } catch (error) {
    console.error(`Error ${enable ? 'enabling' : 'disabling'} tool:`, error)
  }
}
</script>
